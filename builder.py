import json
from google.genai import types
from config import client_gemini
from database import save_agent_blueprint

def create_agent_blueprint(user_prompt, file_path=None):
    """
    Translates user request into a strict 'Logic Blueprint'.
    """
    system_instruction = """
    You are an AI Architect. Create a JSON Agent Blueprint.
    The 'instructions' field must be a set of MANDATORY RULES the agent will follow.
    
    Output JSON:
    {
        "agent_name": "Name",
        "description": "Short summary",
        "tools": ["pdf_tool", "email_tool"],
        "instructions": "Master instructions for the agent (e.g. 'Always extract X', 'Never say Y')"
    }
    """

    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_instruction}\nUser Request: {user_prompt}",
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        blueprint = json.loads(response.text)
        if save_agent_blueprint(blueprint):
            return blueprint
        return None

    except Exception as e:
        print(f"Builder Error: {e}")
        return None