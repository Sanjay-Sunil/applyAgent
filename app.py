import streamlit as st
import json
import os

st.set_page_config(page_title="Hackathon LAM", page_icon="🚀", layout="wide")

st.title("🚀 Hackathon LAM Command Center")

# Load data
def load_data():
    base_dir = os.path.dirname(__file__)
    try:
        with open(os.path.join(base_dir, "data", "profiles.json"), "r") as f:
            profiles = json.load(f)
        with open(os.path.join(base_dir, "data", "ideas.json"), "r") as f:
            ideas = json.load(f)
        return profiles, ideas
    except FileNotFoundError:
        st.error("Data files not found. Please ensure profiles.json and ideas.json exist in the data folder.")
        return [], []

profiles, ideas = load_data()

st.sidebar.header("Configuration")
hackathon_url = st.sidebar.text_input("Hackathon URL", placeholder="https://devpost.com/...")

# Select profiles
profile_options = {p['name']: p for p in profiles}
selected_profile_names = st.sidebar.multiselect(
    "Select Applicants",
    options=list(profile_options.keys()),
    default=[list(profile_options.keys())[0]] if profile_options else None
)

# Select idea
idea_options = {f"{i['title']} ({i['theme']})": i for i in ideas}
selected_idea_name = st.sidebar.selectbox(
    "Select Project Idea",
    options=list(idea_options.keys())
)

import subprocess
import time

def get_state():
    try:
        with open("state.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"status": "idle"}

def set_state(data):
    with open("state.json", "w") as f:
        json.dump(data, f, indent=2)

st.sidebar.markdown("---")
start_button = st.sidebar.button("▶️ Start Application Agent", type="primary")

if start_button:
    if not hackathon_url:
        st.warning("Please enter a hackathon URL.")
    elif not selected_profile_names:
        st.warning("Please select at least one applicant.")
    else:
        st.info("Starting Playwright Agent in the background...")
        # Reset state
        set_state({"status": "starting"})
        # Launch background process
        subprocess.Popen(["python3", "browser_agent.py", hackathon_url])
        time.sleep(2)
        st.rerun()
        
st.markdown("### Dashboard")

state = get_state()
status = state.get("status", "idle")

if status == "idle":
    st.markdown("Welcome to the LAM Command Center. Configure the agent on the sidebar and click **Start**.")
elif status in ["starting", "generating_docs", "running"]:
    if status == "generating_docs":
        st.info("Agent is writing your Pitch Deck presentation...")
    else:
        st.info("Agent is actively scraping the form and writing answers...")
    st.spinner("Please wait...")
    time.sleep(2)
    st.rerun()
elif status == "waiting_for_approval":
    st.success("Form filled! Awaiting your approval.")
    
    st.subheader("Human Verification (Review Stage)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Generated Document (PDF/PPT)**")
        st.success("Pitch deck generated successfully! (Check folder for .pptx file)")

    with col2:
        st.markdown("**Form Fields Filled (by Gemini)**")
        answers = state.get("proposed_answers", {})
        if "error" in answers:
            st.error(f"LLM Error: {answers['error']}")
        else:
            for field in state.get("extracted_fields", []):
                fid = field["id"]
                st.text_input(field["label"], value=answers.get(fid, ""), key=fid)

    colA, colB = st.columns([1, 4])
    with colA:
        if st.button("✅ Approve & Submit", type="primary"):
            state["status"] = "approved"
            set_state(state)
            st.rerun()
    with colB:
        if st.button("❌ Abort"):
            state["status"] = "aborted"
            set_state(state)
            st.rerun()
elif status == "approved":
    st.success("Application successfully submitted! (Simulated)")
    if st.button("Reset"):
        set_state({"status": "idle"})
        st.rerun()
elif status == "aborted":
    st.error("Agent aborted.")
    if st.button("Reset"):
        set_state({"status": "idle"})
        st.rerun()
