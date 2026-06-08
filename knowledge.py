import os
import re
import json
import pandas as pd
from pypdf import PdfReader
from docx import Document

def apply_privacy_controls(text):
    """
    🛡️ PRIVACY GUARDRAIL: Automatically redacts sensitive information 
    before the text is ever sent to the LLM. 
    """
    original_len = len(text)
    
    # Redact standard Phone Numbers
    phone_pattern = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    text = phone_pattern.sub("[REDACTED PHONE NUMBER]", text)
    
    # Redact Social Security Numbers (US format as an example)
    ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    text = ssn_pattern.sub("[REDACTED SSN]", text)

    # We specifically DO NOT redact emails here because the 'Email Tool' needs them.
    
    if len(text) != original_len:
        print("   🔒 Privacy Control Triggered: Sensitive data redacted from file.")
        
    return text

def extract_text_from_file(file_path):
    """
    The Universal File Parser.
    Extracts raw text from almost any business document format.
    """
    ext = os.path.splitext(file_path)[-1].lower()
    text = ""

    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        
        elif ext == '.docx':
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            
        elif ext in ['.csv', '.xlsx', '.xls']:
            # Note: Requires 'openpyxl' installed for Excel files
            if ext == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            text = df.to_string()
            
        elif ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                text = json.dumps(data, indent=2)
                
        elif ext in ['.txt', '.md', '.log']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
        else:
            print(f"⚠️ Warning: Unsupported file type '{ext}'. Attempting raw text extraction.")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                
        # Run the text through our security layer
        clean_text = apply_privacy_controls(text.strip())
        return clean_text

    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return ""

def prepare_context(file_paths):
    """
    Combines multiple files into one structured context string 
    for the Agent's reasoning engine.
    """
    if not file_paths:
        return "No external documents provided."

    combined_knowledge = ""
    for path in file_paths:
        if not os.path.exists(path):
            print(f"❌ Error: File not found -> {path}")
            continue
            
        print(f"   📄 Parsing: {os.path.basename(path)}...")
        content = extract_text_from_file(path)
        
        if content:
            combined_knowledge += f"\n--- START OF DOCUMENT: {os.path.basename(path)} ---\n"
            combined_knowledge += f"{content}\n"
            combined_knowledge += f"--- END OF DOCUMENT ---\n"
        else:
            print(f"   ⚠️ Warning: No readable text found in {os.path.basename(path)}")
            
    return combined_knowledge