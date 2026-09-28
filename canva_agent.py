import os
import json
import time
from playwright.sync_api import sync_playwright

def generate_canva_deck(idea_file):
    with open(idea_file) as f:
        ideas = json.load(f)
    
    # Grab the first idea for testing
    idea = ideas[0]
    
    # Formatting the prompt for the @Canva extension
    prompt = f"""@Canva Please generate a startup presentation for my hackathon project.
    
Title: {idea['title']}
Theme: {idea['theme']}
Problem: {idea['problem']}
Solution: {idea['solution']}
"""
    
    with sync_playwright() as p:
        # We reuse the same persistent profile so you stay logged in
        os.makedirs("./playwright_profile", exist_ok=True)
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./playwright_profile",
            headless=False # Must be visible!
        )
        page = browser.new_page()
        print("Opening Gemini Web UI...")
        page.goto("https://gemini.google.com/app")
        
        print("Please log in to your Google Account in the browser window if prompted.")
        print("Waiting for the Gemini chat box to become available...")
        
        try:
            # Gemini's chat input is a custom 'rich-textarea' element
            page.wait_for_selector("rich-textarea", timeout=60000)
            print("Chat box found! Injecting prompt...")
            
            # Click the chat box to focus it
            page.locator("rich-textarea").first.click()
            page.wait_for_timeout(1000)
            
            # Type the prompt out like a human (needed for custom rich text editors)
            page.keyboard.type(prompt, delay=10)
            page.wait_for_timeout(1000)
            
            # Hit Enter to send
            page.keyboard.press("Enter")
            
            print("Prompt submitted! Canva is generating your deck.")
            print("The browser will remain open for 5 minutes so you can click the Canva link and download the PPTX.")
            
            # Keep the browser alive so you can see and download the Canva output
            page.wait_for_timeout(300000) 
            
        except Exception as e:
            print("Timed out waiting for the chat box. You might need to finish logging in.")
            print(f"Error details: {e}")
            
        browser.close()

if __name__ == "__main__":
    generate_canva_deck("data/ideas.json")
