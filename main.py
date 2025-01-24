import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# Fetch API Key and Password from Environment Variables
API_KEY = os.getenv("DIFY_API_KEY")
APP_PASSWORD = os.getenv("APP_PASSWORD")
BASE_URL = "http://testing.drishtigpt.com/v1"

if not API_KEY:
    st.error("API Key not found. Please set it as an environment variable `DIFY_API_KEY`.")
    st.stop()

if not APP_PASSWORD:
    st.error("App password not found. Please set it as an environment variable `APP_PASSWORD`.")
    st.stop()

# Authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    password = st.text_input("Enter Password", type="password")
    login_clicked = st.button("Login")

    if login_clicked:
        if password == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid password.")
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

def get_workflow_output(workflow_id):
    url = f"{BASE_URL}/workflows/run/{workflow_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    return response.json()

# Initialize session state for workflow tasks
if "tasks" not in st.session_state:
    st.session_state.tasks = pd.DataFrame(columns=["Timestamp", "Subject", "Workflow ID", "Status", "Output"])

# Streamlit App
def main():
    st.title("Production-Ready Question Generator App")

    # Sidebar Navigation
    menu = ["Generate Questions", "Task Status"]
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
            with st.spinner("Starting workflow..."):
                user_id = "user-123"  # Replace with dynamic user ID if needed
                response = start_workflow(subject, count, complexity, keywords, question_type, user_id)

                if "workflow_run_id" in response:
                    workflow_id = response["workflow_run_id"]
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Add task to session state
                    new_task = pd.DataFrame({
                        "Timestamp": [timestamp],
                        "Subject": [subject],
                        "Workflow ID": [workflow_id],
                        "Status": ["Processing"],
                        "Output": [None]
                    })
                    st.session_state.tasks = pd.concat([st.session_state.tasks, new_task], ignore_index=True)

                    st.success("Workflow started successfully! Check task status in the Task Status tab.")
                else:
                    st.error("Failed to start workflow. Check inputs or API key.")

    # Task Status Tab
    elif choice == "Task Status":
        st.header("Task Status")

        if st.session_state.tasks.empty:
            st.info("No tasks have been started yet.")
        else:
            for index, row in st.session_state.tasks.iterrows():
                st.write(f"**Task ID:** {row['Workflow ID']}")
                st.write(f"**Subject:** {row['Subject']}")
                st.write(f"**Status:** {row['Status']}")

                if row["Status"] == "Processing":
                    if st.button(f"Check Status for {row['Workflow ID']}"):
                        result = get_workflow_output(row["Workflow ID"])

                        if result.get("status") == "succeeded":
                            outputs = result.get("outputs", {})
                            if outputs:
                                question_data = eval(outputs.get("result", "[]"))

                                # Process results into a readable format
                                questions = []
                                for q in question_data.split("\n\n"):
                                    if "Correct Answer" in q:
                                        parts = q.split("\n")
                                        question = parts[0].split(":")[1].strip()
                                        options = [p.split(" ")[1].strip() for p in parts[1:5]]
                                        correct = parts[5].split(":")[1].strip()
                                        explanation = parts[6].split(":")[1].strip()
                                        questions.append([question, *options, correct, explanation])

                                # Show results in a table
                                df = pd.DataFrame(questions, columns=["Question", "Option 1", "Option 2", "Option 3", "Option 4", "Correct Option", "Explanation"])
                                st.write("Generated Questions:")
                                st.dataframe(df)

                                # Update task status
                                st.session_state.tasks.at[index, "Status"] = "Completed"
                                st.session_state.tasks.at[index, "Output"] = df

                        else:
                            st.error(f"Workflow still processing or failed. Status: {result.get('status')}")

if __name__ == "__main__":
    main()
