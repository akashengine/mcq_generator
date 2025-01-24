import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# Environment variables
API_KEY = os.getenv("DIFY_API_KEY")
APP_PASSWORD = os.getenv("APP_PASSWORD")
BASE_URL = "http://testing.drishtigpt.com/v1"

# Validate credentials
if not API_KEY or not APP_PASSWORD:
    st.error("Missing environment variables. Set DIFY_API_KEY and APP_PASSWORD.")
    st.stop()

# Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter Password", type="password")
    if st.button("Login") and password == APP_PASSWORD:
        st.session_state.authenticated = True
        st.success("Logged in successfully!")
    st.stop()

# Helper function for API calls
def start_workflow(subject, count, complexity, keywords, question_type):
    try:
        response = requests.post(
            f"{BASE_URL}/workflows/run",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
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
        )
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def process_questions(result_text):
    questions = []
    for q in result_text.split("\n\n"):
        if "Correct Answer" in q:
            parts = q.split("\n")
            question = parts[0].split(":")[1].strip()
            options = [p.split(" ")[1].strip() for p in parts[1:5]]
            correct = parts[5].split(":")[1].strip()
            explanation = parts[6].split(":")[1].strip()
            questions.append([question, *options, correct, explanation])
    return questions

# Initialize session state
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Main app
st.title("Question Generator")

tab1, tab2 = st.tabs(["Generate Questions", "View Tasks"])

with tab1:
    subject = st.selectbox("Subject", 
        ["Economics", "Geography", "History", "Miscellaneous- Factual, Static GK", "Polity"])
    count = st.number_input("Number of Questions", min_value=1, max_value=15, value=10)
    complexity = st.selectbox("Complexity", ["Easy", "Medium", "Hard"])
    keywords = st.text_area("Keywords", "BB-Economics_part1 Keywords")
    question_type = st.selectbox("Question Type", 
        ["Simple Statement MCQ", "Fill-in-the-Blanks MCQ", "Match-the-Column", "Multi-Statement Validation"])

    if st.button("Generate Questions"):
        with st.spinner("Generating questions..."):
            response = start_workflow(subject, count, complexity, keywords, question_type)
            if response and 'data' in response:
                result = response['data']
                if result['status'] == 'succeeded':
                    questions = process_questions(result['outputs']['result'])
                    df = pd.DataFrame(questions, columns=[
                        "Question", "Option 1", "Option 2", "Option 3", 
                        "Option 4", "Correct Option", "Explanation"
                    ])
                    st.session_state.tasks.append({
                        'timestamp': datetime.now(),
                        'subject': subject,
                        'workflow_id': result['id'],
                        'questions': df
                    })
                    st.success("Questions generated successfully!")
                    st.dataframe(df)
                else:
                    st.error(f"Generation failed: {result.get('error', 'Unknown error')}")

with tab2:
    if not st.session_state.tasks:
        st.info("No tasks generated yet")
    else:
        for task in st.session_state.tasks:
            with st.expander(f"{task['subject']} - {task['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                st.dataframe(task['questions'])
