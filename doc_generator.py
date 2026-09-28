import os
import json
from pptx import Presentation
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_pitch_content(idea):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing")
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert startup founder. Take this hackathon project idea and expand it into a 5-slide pitch deck.
    
    Idea Data:
    {json.dumps(idea, indent=2)}
    
    Output a JSON array of up to 5 slide objects. Each object must have a 'title' and 'content' (bullet points as a single string separated by newlines).
    Example:
    [
      {{"title": "The Problem", "content": "- Point 1\\n- Point 2"}}
    ]
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)

def create_pptx(idea, output_filename="pitch_deck.pptx"):
    print("Generating pitch content with LLM...")
    try:
        slides_data = generate_pitch_content(idea)
    except Exception as e:
        print(f"Failed to generate pitch content: {e}")
        slides_data = [{"title": "Error", "content": f"Could not generate slides: {str(e)}"}]
    
    print("Building PPTX file...")
    prs = Presentation()
    
    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    
    title.text = idea.get("title", "Project Title")
    subtitle.text = idea.get("theme", "Hackathon Project")
    
    # Content slides
    bullet_slide_layout = prs.slide_layouts[1]
    
    for slide_data in slides_data:
        slide = prs.slides.add_slide(bullet_slide_layout)
        shapes = slide.shapes
        title_shape = shapes.title
        body_shape = shapes.placeholders[1]
        
        title_shape.text = slide_data.get("title", "Slide")
        tf = body_shape.text_frame
        tf.text = slide_data.get("content", "")
        
    prs.save(output_filename)
    print(f"Saved pitch deck to {output_filename}")
    return output_filename

if __name__ == "__main__":
    with open("data/ideas.json") as f:
        ideas = json.load(f)
    create_pptx(ideas[0], "test_deck.pptx")
