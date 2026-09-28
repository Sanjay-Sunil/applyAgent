import sys
import json
import time
import os
from playwright.sync_api import sync_playwright
from llm_logic import generate_form_answers
from doc_generator import create_pptx

def run_agent(url, selected_profile, selected_idea, state_file):
    print(f"Starting agent for {url}...")
    
    # Generate the pitch deck immediately
    update_state(state_file, {"status": "generating_docs"})
    deck_path = f"{selected_idea['id']}_pitch.pptx"
    create_pptx(selected_idea, deck_path)
    
    # Update state to running
    update_state(state_file, {"status": "running"})
        
    with sync_playwright() as p:
        # Use persistent context to bypass constant logins
        os.makedirs("./playwright_profile", exist_ok=True)
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./playwright_profile",
            headless=False # Set to false so we can see it during testing!
        )
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        # STEP 1: Look for "Apply" or "Register" buttons
        print("Looking for registration buttons...")
        try:
            apply_buttons = page.locator("button:has-text('Apply'), button:has-text('Register'), a:has-text('Apply'), a:has-text('Register'), button:has-text('Participate')")
            if apply_buttons.count() > 0:
                print(f"Found {apply_buttons.count()} potential apply buttons. Clicking the first one...")
                apply_buttons.first.click(timeout=5000)
                page.wait_for_timeout(3000) # Wait for modal to open or page to load
        except Exception as e:
            print("No apply button needed or click failed:", e)
            
        # STEP 2: Scrape fields
        fields_data = []
        inputs = page.locator("input:not([type='hidden']), textarea, select")
        count = inputs.count()
        file_input_id = None
        
        for i in range(count):
            loc = inputs.nth(i)
            tag = loc.evaluate("el => el.tagName").lower()
            name = loc.get_attribute("name") or loc.get_attribute("id") or f"field_{i}"
            input_type = loc.get_attribute("type")
            
            # Simple heuristic for labels
            label = loc.evaluate("(el) => { let l = document.querySelector(`label[for='${el.id}']`); return l ? l.innerText : ''; }")
            if not label:
                label = loc.get_attribute("placeholder") or name
                
            if input_type == "file":
                file_input_id = name
                print(f"Detected file upload field: {name}")
                continue # We handle file uploads separately
                
            fields_data.append({"id": name, "label": label, "type": tag})
            
        print("Fields extracted:", fields_data)
        
        # Get answers from Gemini
        answers = generate_form_answers(fields_data, selected_profile, selected_idea)
        
        # Inject answers into the page
        if "error" not in answers:
            for field in fields_data:
                fid = field["id"]
                if fid in answers:
                    val = str(answers[fid])
                    try:
                        # Find element safely and fill it
                        loc = page.locator(f"//input[@id='{fid}' or @name='{fid}'] | //textarea[@id='{fid}' or @name='{fid}']").first
                        if loc.is_visible():
                            loc.fill(val)
                    except Exception as e:
                        print(f"Failed to fill {fid}: {e}")
                        
            # Upload the pitch deck if a file field was found
            if file_input_id and os.path.exists(deck_path):
                print(f"Uploading {deck_path} to {file_input_id}...")
                try:
                    loc = page.locator(f"input[type='file'][id='{file_input_id}'], input[type='file'][name='{file_input_id}']").first
                    loc.set_input_files(deck_path)
                except Exception as e:
                    print(f"Failed to upload file: {e}")
        
        # Notify Streamlit we are paused and ready for review
        update_state(state_file, {
            "status": "waiting_for_approval",
            "extracted_fields": fields_data,
            "proposed_answers": answers
        })
            
        print("Waiting for human approval...")
        # Wait for approval signal from Streamlit
        while True:
            time.sleep(2)
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                if state.get("status") == "approved":
                    print("Approved! Clicking submit...")
                    # TODO: In real usage, click the actual submit button here
                    update_state(state_file, {"status": "completed"})
                    break
                elif state.get("status") == "aborted":
                    print("Aborted.")
                    break
            except Exception:
                pass
                
        browser.close()

def update_state(state_file, data):
    with open(state_file, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python browser_agent.py <url>")
        sys.exit(1)
        
    # Test data
    with open("data/profiles.json") as f:
        profiles = json.load(f)
    with open("data/ideas.json") as f:
        ideas = json.load(f)
        
    run_agent(sys.argv[1], profiles[0], ideas[0], "state.json")
