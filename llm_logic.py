import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_form_answers(form_fields, profile, idea):
    """
    Uses Gemini to generate answers for scraped hackathon form fields.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not set in environment (or .env file)."}
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an AI assistant helping a user apply to a hackathon.
    
    Here is the applicant's profile:
    {json.dumps(profile, indent=2)}
    
    Here is their project idea:
    {json.dumps(idea, indent=2)}
    
    Here are the fields required in the application form:
    {json.dumps(form_fields, indent=2)}
    
    Return a JSON object mapping each field 'id' to the appropriate answer.
    If the field asks for dietary restrictions, use the profile.
    If the field asks for a project description, use the idea.
    If a field asks a custom essay question (like 'Why this hackathon?'), generate a concise, enthusiastic answer.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}
