from googleapiclient.discovery import build
import re
import io
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import os
import re
import smtplib
import pypdf
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.genai import types
from config import client_gemini
from database import get_agent_by_name, log_agent_activity, register_file_processed
from knowledge import extract_text_from_file
import uuid

from google.oauth2.service_account import Credentials

# One master list of permissions for your single JSON file
MASTER_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive'
]

# Load the single file once, but give it all the permissions
import json
import os

# Write the credentials file at runtime if it doesn't exist
if not os.path.exists('credentials.json'):
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        with open('credentials.json', 'w') as f:
            f.write(creds_json)
            
creds = Credentials.from_service_account_file('credentials.json', scopes=MASTER_SCOPES)

# ==========================================
# EMAIL CONFIGURATION (SMTP)
# ==========================================
# Keep the server variables, but remove the hardcoded user credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_direct_email(sender_email, sender_password, to_email, subject, body):
    """Sends an automated email dynamically using the user's credentials."""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

def push_to_google_doc(doc_link, text_content):
    """Appends generated text into a live Google Doc."""
    try:
        # Extract the Document ID from the URL using Regex
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', doc_link)
        if not match:
            return False, "Invalid Google Docs URL format."
        doc_id = match.group(1)

        # Authenticate using the same credentials.json file
        scopes = ['https://www.googleapis.com/auth/documents']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
        service = build('docs', 'v1', credentials=creds)

        # Build the insertion request
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': text_content + "\n\n"
                }
            }
        ]
        
        # Execute the update
        service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def push_to_google_slide(slide_link, text_content):
    """Creates a new slide and injects generated text into a live Google Presentation."""
    try:
        # --- THE FIX: Intercept lists and convert them to a single string ---
        if isinstance(text_content, list):
            text_content = "\n".join(f"• {item}" for item in text_content)
        elif not isinstance(text_content, str):
            text_content = str(text_content)

        # Extract the Presentation ID from the URL
        import re
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', slide_link)
        if not match:
            return False, "Invalid Google Slides URL format."
        presentation_id = match.group(1)

        # Authenticate using your master credentials.json file
        scopes = ['https://www.googleapis.com/auth/presentations']
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
        service = build('slides', 'v1', credentials=creds)

        # Generate unique IDs for the new slide and its text box
        slide_id = str(uuid.uuid4())
        textbox_id = str(uuid.uuid4())

        # Build the exact sequence of actions for the API
        requests = [
            {
                # Action 1: Create a new slide with a standard layout
                'createSlide': {
                    'objectId': slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY'
                    },
                    'placeholderIdMappings': [
                        {
                            'layoutPlaceholder': {'type': 'BODY'},
                            'objectId': textbox_id
                        }
                    ]
                }
            },
            {
                # Action 2: Insert the AI's bullet points into that new body text box
                'insertText': {
                    'objectId': textbox_id,
                    'text': text_content
                }
            }
        ]
        
        # Execute the update
        service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': requests}).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)
        
def push_to_google_sheet(sheet_link, csv_text):
    """Authenticates via Service Account and pushes raw CSV text to a Google Sheet."""
    try:
        # 1. Authenticate using the JSON key
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
        client = gspread.authorize(creds)
        
        # 2. Open the specific spreadsheet by its URL
        sheet = client.open_by_url(sheet_link).sheet1
        
        # 3. Clean and parse the CSV text using pandas
        # We strip any weird spacing and read it as a virtual file
        df = pd.read_csv(io.StringIO(csv_text.strip()))
        df = df.fillna("") # Replace empty cells so JSON doesn't break
        
        # 4. Convert headers and rows into a list of lists format required by gspread
        data_to_push = [df.columns.values.tolist()] + df.values.tolist()
        
        # 5. Push to the sheet! (Clear old data first to avoid overlapping)
        sheet.clear()
        sheet.update(range_name='A1', values=data_to_push)
        
        return True, "Success"
    except Exception as e:
        return False, str(e)

def extract_text_from_pdf(file_path):
    """Safely pulls text from PDF and scrubs hidden characters for JSON safety."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    # Scrub non-printable/control characters (keeps newlines and tabs)
                    content = "".join(char for char in content if ord(char) >= 32 or char in "\n\t")
                    text += content + "\n"
        
        # Final Regex Scrub: Remove non-ASCII/control characters that break JSON
        return re.sub(r'[^\x00-\x7F]+', ' ', text)
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def send_direct_email(sender_email, sender_password, to_email, subject, body):
    """Sends an automated email dynamically using the user's credentials."""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

def run_agent(agent_name, file_paths, auto_approve, current_username, user_instructions, sender_email=None, sender_password=None, sheet_link=None, doc_link=None, slide_link=None):
    """The Autonomous Agent Execution Loop."""
    execution_logs = []
    
    def web_log(msg):
        print(msg)
        execution_logs.append(msg)

    web_log(f"🤖 Agent '{agent_name}' initialized for {current_username}...")

    # 1. Fetch Agent Rules from Database
    agent_data = get_agent_by_name(agent_name)
    if not agent_data:
        error_msg = f"❌ ERROR: Agent '{agent_name}' not found."
        web_log(error_msg)
        return {"status": "error", "message": error_msg, "logs": execution_logs}

    # 2. Extract Knowledge from Uploaded File (Universal)
    web_log("📖 Reading document content...")
    document_text = extract_text_from_file(file_paths[0]) if file_paths else "No file uploaded."
    
    if file_paths:
        register_file_processed(agent_name, file_paths[0])

    # 3. Gemini Analysis Prompt
    web_log("🧠 Performing targeted AI analysis...")
    master_rules = agent_data.get('instructions', "Analyze the resume.")
    
    # ... (Keep everything above this exactly the same) ...

    # 3. Gemini Analysis Prompt (UPDATED FOR MULTIPLE TASKS)
    # 3. Gemini Analysis Prompt (UPDATED FOR DYNAMIC MULTI-TOOL BUCKETS)
    web_log("🧠 Performing targeted AI analysis...")
    
    prompt = f"""
    YOU ARE: {agent_name}
    MASTER RULES: {master_rules}
    USER TASK: {user_instructions}
    
    DATA (FILE CONTENT):
    {document_text[:15000]}

    MISSION:
    1. Execute the USER TASK strictly following your MASTER RULES.
    2. Sort your output into the specific tools provided below. If a tool is not needed, leave its field blank.
    
    OUTPUT FORMAT (STRICT JSON ONLY):
    {{
        "analysis_report": "A short summary of what you did to display on the frontend dashboard.",
        "csv_data": "Product,Qty,Price\\nItem1,1,10.00\\nItem2,2,20.00 (OUTPUT STRICT RAW CSV DATA ONLY. NO markdown, NO quotes, NO conversational text.)",
        "doc_data": "The formal paragraphs or text intended for the Google Document.",
        "slide_data": "The bullet points intended for the presentation.",
        "email_tasks": [
            {{
                "candidate_name": "Target Name (or blank)",
                "found_email": "extracted_email@example.com",
                "automated_draft": "Subject: ...\\n\\nDear [Name], ..."
            }}
        ]
    }}
    """

    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )

        result_json = json.loads(response.text)
        web_log("✅ AI Analysis complete.")
        
        # Extract the separate buckets of data
        analysis_report = result_json.get('analysis_report', 'No report generated.')
        csv_data = result_json.get('csv_data', '')
        doc_data = result_json.get('doc_data', '')
        slide_data = result_json.get('slide_data', '')
        email_tasks = result_json.get('email_tasks', [])
        
        # ADD THESE TWO LINES BACK IN:
        display_email = email_tasks[0].get('found_email', '') if email_tasks else ''
        display_draft = email_tasks[0].get('automated_draft', '') if email_tasks else ''

        # ==========================================
        # 4. DIRECT SMTP EMAIL EXECUTION (BULK LOOP)
        # ==========================================
        equipped_tools = str(agent_data.get('tools', [])).lower()

        # ==========================================
        # TOOL 1: EMAIL EXECUTION
        # ==========================================
        if 'email' in equipped_tools or 'mail' in equipped_tools:
            if email_tasks and auto_approve:
                web_log(f"📨 Email Tool Authorized. Processing {len(email_tasks)} emails...")
                
                for task in email_tasks:
                    target_email = task.get('found_email')
                    draft_body = task.get('automated_draft')
                    
                    if not target_email or target_email == "extracted_email@example.com":
                        continue
                    
                    # (Your existing SMTP send logic goes here)
                    success = send_direct_email(sender_email, sender_password, target_email, "Update", draft_body)
                    if success:
                        web_log(f"✅ Mail Sent Successfully to {target_email}!")
                    else:
                        web_log(f"❌ SMTP failed for {target_email}. Did you provide the App Password?")
            elif email_tasks:
                web_log("🛡️ Emails drafted but NOT sent (Auto-Approve OFF).")
        else:
            web_log("🚫 Email Tool not equipped. Bypassing SMTP execution.")

        # ==========================================
        # TOOL 2: SPREADSHEET EXECUTION
        # ==========================================
        # ================== TOOL: SPREADSHEET ==================
        # ================== TOOL: SPREADSHEET ==================
        if 'spreadsheet' in equipped_tools or 'csv' in equipped_tools or 'sheet' in equipped_tools:
            if sheet_link and csv_data:
                web_log(f"📊 Spreadsheet Tool Triggered. Targeting: {sheet_link}")
                success, err = push_to_google_sheet(sheet_link, csv_data) # Changed to csv_data
                if success:
                    web_log("✅ SUCCESS: Data appended to Google Sheet.")
                else:
                    web_log(f"❌ Google Sheets API Error: {err}")
            else:
                web_log("⚠️ Sheet tool equipped, but no link provided or no CSV data generated.")
                
        # ================== TOOL: GOOGLE DOCS ==================
        if 'doc' in equipped_tools or 'writer' in equipped_tools:
            if doc_link and doc_data:
                web_log(f"📝 Google Docs Tool Triggered. Targeting: {doc_link}")
                success, err = push_to_google_doc(doc_link, doc_data) # Changed to doc_data
                if success:
                    web_log("✅ SUCCESS: Document updated remotely.")
                else:
                    web_log(f"❌ Google Docs API Error: {err}")
            else:
                web_log("⚠️ Docs tool equipped, but no link provided or no text generated.")

        # ================== TOOL: GOOGLE SLIDES ==================
        if 'slide' in equipped_tools or 'presentation' in equipped_tools:
            if slide_link and slide_data:
                web_log(f"🖥️ Google Slides Tool Triggered. Targeting: {slide_link}")
                success, err = push_to_google_slide(slide_link, slide_data)
                if success:
                    web_log("✅ SUCCESS: New slide created and text injected remotely.")
                else:
                    web_log(f"❌ Google Slides API Error: {err}")
            else:
                web_log("⚠️ Slides tool equipped, but no link provided or no text generated.")

        # Return payload to frontend
        return {
            "status": "success",
            "agent_name": agent_name,
            "response": analysis_report,
            "extracted_email": display_email,
            "draft_body": display_draft,
            "logs": execution_logs
        }

    except Exception as e:
        web_log(f"❌ Execution Error: {str(e)}")
        return {"status": "error", "message": str(e), "logs": execution_logs}