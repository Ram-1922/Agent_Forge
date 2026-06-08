import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from config import users_col, client_gemini # Using Gemini to draft the mail!

load_dotenv()

def generate_ai_email_body(candidate_name, reason, sender_name):
    """
    Uses Gemini to draft a professional, personalized recruitment email.
    """
    prompt = f"""
    Write a short, professional, and warm interview invitation email.
    Recipient: {candidate_name}
    Reason for selection: {reason}
    Sender Name: {sender_name}
    
    The tone should be 'SaaS Professional'. Mention the specific reason they were selected 
    to make it feel personal. Keep it under 100 words.
    """
    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except:
        # Fallback if Gemini API fails
        return f"Hi {candidate_name}, we were impressed by your background in {reason}. Let's chat!"

def send_interview_invite(to_email, candidate_name, reason, current_username=None):
    """
    Fetches recruiter info from DB, generates AI content, and sends via SMTP.
    """
    # 1. Fetch User Data for Personalization
    recruiter_email = os.getenv("EMAIL_USER") # Default fallback
    display_name = current_username or "The Hiring Team"

    if current_username:
        user_data = users_col.find_one({"username": current_username})
        if user_data:
            recruiter_email = user_data.get("email", recruiter_email)

    # 2. Generate the Body using Gemini
    ai_drafted_body = generate_ai_email_body(candidate_name, reason, display_name)

    # 3. SMTP Setup
    sender_email = os.getenv("EMAIL_USER")
    sender_pass = os.getenv("EMAIL_PASS")

    msg = EmailMessage()
    msg.set_content(ai_drafted_body)
    msg['Subject'] = f"Exciting Opportunity: Next Steps for {candidate_name}"
    msg['From'] = f"{display_name} <{sender_email}>"
    msg['To'] = to_email
    msg['Reply-To'] = recruiter_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_pass)
            smtp.send_message(msg)
        return f"AI-Personalized mail sent to {candidate_name} ({to_email})."
    except Exception as e:
        return f"Mail Error: {str(e)}"