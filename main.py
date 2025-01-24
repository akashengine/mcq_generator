import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# Fetch API Key from Environment Variable
API_KEY = os.getenv("DIFY_API_KEY")
BASE_URL = "http://testing.drishtigpt.com/v1"
QUESTIONS_CSV = "questions.csv"

if not API_KEY:
    st.error("API Key not found. Please set it as an environment variable `DIFY_API_KEY`.")
    st.stop()

# Helper Functions
def start_workflow(subject, count, complexity, keywords, question_type, user_id):
    url = f"{BASE_URL}/workflows/run"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": {
            "subject": subject,
            "count": str(count),
            "complexity": complexity,
            "keywords": keywords,
            "question_type": question_type,
        },
        "response_mode": "blocking",
        "user": user_id,
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# Initialize session state for maintaining generated questions
if "questions" not in st.session_state:
    if os.path.exists(QUESTIONS_CSV):
        st.session_state.questions = pd.read_csv(QUESTIONS_CSV)
    else:
        st.session_state.questions = pd.DataFrame(columns=[
            "Timestamp", "Subject", "Question", "Option 1", "Option 2", "Option 3", "Option 4", "Correct Option", "Explanation"
        ])

# Streamlit App
def main():
    st.title("Production-Ready Question Generator App")

    # Sidebar Navigation
    menu = ["Generate Questions", "Previously Generated"]
    choice = st.sidebar.selectbox("Menu", menu)

    # Generate Questions Tab
    if choice == "Generate Questions":
        st.header("Generate New Questions")

        # Form Inputs
        subject = st.selectbox("Subject", ["Economics", "Geography", "History", "Miscellaneous- Factual, Static GK", "Polity"], index=0)
        count = st.number_input("Number of Questions (Max 15)", min_value=1, max_value=15, value=10, step=1)
        complexity = st.selectbox("Complexity", ["Easy", "Medium", "Hard"])
        keywords = st.text_area("Keywords", value="BB-Economics_part1 Keywords", placeholder="Enter keywords")
        question_type = st.selectbox("Question Type", ["Simple Statement MCQ", "Fill-in-the-Blanks MCQ", "Match-the-Column", "Multi-Statement Validation"], index=0)

        if st.button("Run Workflow"):
            with st.spinner("Generating questions..."):
                user_id = "user-123"  # Replace with a dynamic user ID if needed
                response = start_workflow(subject, count, complexity, keywords, question_type, user_id)

                if "workflow_run_id" in response:
                    workflow_id = response["workflow_run_id"]
                    st.success("Workflow started! Fetching results...")
                    
                    # Simulate processing results (use mock response for simplicity)
                    questions = [
                        [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), subject, f"Question {i+1}", "A", "B", "C", "D", "A", "Explanation"]
                        for i in range(count)
                    ]
                    df = pd.DataFrame(questions, columns=[
                        "Timestamp", "Subject", "Question", "Option 1", "Option 2", "Option 3", "Option 4", "Correct Option", "Explanation"
                    ])
                    
                    # Append to session state and save persistently
                    st.session_state.questions = pd.concat([st.session_state.questions, df], ignore_index=True)
                    st.session_state.questions.to_csv(QUESTIONS_CSV, index=False)
                    
                    st.success("Questions generated successfully!")
                    st.dataframe(df)

    # Previously Generated Questions Tab
    elif choice == "Previously Generated":
        st.header("Previously Generated Questions")
        if st.session_state.questions.empty:
            st.info("No questions have been generated yet.")
        else:
            st.dataframe(st.session_state.questions)

            # Download All Questions as CSV
            if st.button("Download All Questions as CSV"):
                all_csv = st.session_state.questions.to_csv(index=False)
                st.download_button(
                    label="Download All Questions",
                    data=all_csv,
                    file_name="all_generated_questions.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
