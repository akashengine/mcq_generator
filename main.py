import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_KEY = st.secrets["DIFY_API_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]
BASE_URL = "http://testing.drishtigpt.com/v1"

def start_workflow(subject, count, complexity, keywords, question_type):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {
            "subject": subject,
            "count": str(count),
            "complexity": complexity,
            "keywords": keywords,
            "question_type": question_type
        },
        "response_mode": "blocking",
        "user": "abc-123"
    }
    
    try:
        st.write("Sending request with payload:", payload)
        response = requests.post(f"{BASE_URL}/workflows/run", headers=headers, json=payload)
        st.write("Response:", response.text)  # Debug response
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def get_workflow_status(workflow_id):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(f"{BASE_URL}/workflows/run/{workflow_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Status Check Error: {e}")
        return None

# Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if not st.session_state.authenticated:
    password = st.text_input("Password", type="password")
    if st.button("Login") and password == APP_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# Main app
st.title("Question Generator")
tab1, tab2 = st.tabs(["Generate Questions", "View Tasks"])

with tab1:
    with st.form("generate_form"):
        subject = st.selectbox("Subject", ["Economics", "Geography", "History", "Miscellaneous- Factual, Static GK", "Polity"])
        count = st.number_input("Number of Questions", 1, 15, 10)
        complexity = st.selectbox("Complexity", ["Easy", "Medium", "Hard"])
        keywords = st.text_area("Keywords", "BB-Economics_part1 Keywords")
        question_type = st.selectbox("Question Type", ["Simple Statement MCQ", "Fill-in-the-Blanks MCQ", "Match-the-Column", "Multi-Statement Validation"])
        submitted = st.form_submit_button("Generate Questions")

        if submitted:
            with st.spinner("Starting generation..."):
                response = start_workflow(subject, count, complexity, keywords, question_type)
                if response and "workflow_run_id" in response:
                    task = {
                        "timestamp": datetime.now(),
                        "subject": subject,
                        "workflow_id": response["workflow_run_id"],
                        "status": "Processing"
                    }
                    st.session_state.tasks.append(task)
                    st.success("Task started! Check View Tasks tab.")

with tab2:
    if len(st.session_state.tasks) == 0:
        st.info("No tasks generated yet")
    else:
        for idx, task in enumerate(reversed(st.session_state.tasks)):
            with st.expander(f"{task['subject']} - {task['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                st.write(f"Status: {task['status']}")
                if task['status'] == 'Processing':
                    if st.button(f"Check Status", key=f"check_{idx}"):
                        result = get_workflow_status(task['workflow_id'])
                        if result and result.get('status') == 'succeeded':
                            st.json(result)  # Debug output
                            if 'outputs' in result and 'result' in result['outputs']:
                                st.success("Questions generated successfully!")
                                st.text(result['outputs']['result'])
                                task['status'] = 'Completed'
