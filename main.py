import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Environment setup
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
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def get_workflow_status(workflow_id):
    try:
        response = requests.get(
            f"{BASE_URL}/workflows/run/{workflow_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        return response.json()
    except Exception as e:
        st.error(f"Status Check Error: {e}")
        return None

# Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.tasks = []

if not st.session_state.authenticated:
    with st.form("login"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted and password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif submitted:
            st.error("Invalid password")
    st.stop()

# Main app
st.title("Question Generator")
tab1, tab2 = st.tabs(["Generate Questions", "View Tasks"])

with tab1:
    subject = st.selectbox("Subject", ["Economics", "Geography", "History", "Miscellaneous- Factual, Static GK", "Polity"])
    count = st.number_input("Number of Questions", 1, 15, 10)
    complexity = st.selectbox("Complexity", ["Easy", "Medium", "Hard"])
    keywords = st.text_area("Keywords", "BB-Economics_part1 Keywords")
    question_type = st.selectbox("Question Type", ["Simple Statement MCQ", "Fill-in-the-Blanks MCQ", "Match-the-Column", "Multi-Statement Validation"])

    if st.button("Generate Questions"):
        with st.spinner("Starting generation..."):
            response = start_workflow(subject, count, complexity, keywords, question_type)
            if response and "workflow_run_id" in response:
                new_task = {
                    "timestamp": datetime.now(),
                    "subject": subject,
                    "workflow_id": response["workflow_run_id"],
                    "status": "Processing"
                }
                st.session_state.tasks.append(new_task)
                st.success(f"Task started! Check View Tasks tab for status.")
                st.rerun()

with tab2:
    if not st.session_state.tasks:
        st.info("No tasks generated yet")
    else:
        for idx, task in enumerate(st.session_state.tasks):
            with st.expander(f"{task['subject']} - {task['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                st.write(f"Status: {task['status']}")
                if task['status'] == 'Processing':
                    if st.button(f"Check Status", key=f"check_{idx}"):
                        result = get_workflow_status(task['workflow_id'])
                        if result and result.get('status') == 'succeeded':
                            outputs = result.get('outputs', {})
                            if outputs:
                                questions = []
                                for q in outputs['result'].split("\n\n"):
                                    if "Correct Answer" in q:
                                        parts = q.split("\n")
                                        questions.append({
                                            "Question": parts[0].split(":")[1].strip(),
                                            "Options": [p.split(" ")[1].strip() for p in parts[1:5]],
                                            "Correct": parts[5].split(":")[1].strip(),
                                            "Explanation": parts[6].split(":")[1].strip()
                                        })
                                df = pd.DataFrame(questions)
                                st.dataframe(df)
                                st.session_state.tasks[idx]['status'] = 'Completed'
                                st.session_state.tasks[idx]['output'] = df
                                st.rerun()
