import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Config
API_KEY = st.secrets["DIFY_API_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"] 

def start_workflow(subject, count, complexity, keywords, question_type):
   url = "https://testing.drishtigpt.com/v1/workflows/run"
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
   headers = {
       "Authorization": f"Bearer {API_KEY}",
       "Content-Type": "application/json"
   }
   
   response = requests.post(url, headers=headers, json=payload)
   return response.json()

def process_questions(result_text):
   questions = []
   for q in result_text.split("\n\n"):
       if "Correct Answer" in q:
           parts = q.split("\n")
           question = parts[0].split(":")[1].strip()
           options = [p.strip() for p in parts[1:5]]
           correct = parts[5].split(":")[1].strip()
           explanation = parts[6].split(":")[1].strip()
           questions.append([question, *options, correct, explanation])
   return questions

# Auth check
if "authenticated" not in st.session_state:
   st.session_state.authenticated = False

if not st.session_state.authenticated:
   password = st.text_input("Password", type="password")
   if st.button("Login"):
       if password == APP_PASSWORD:
           st.session_state.authenticated = True
           st.rerun()
       else:
           st.error("Invalid password")
   st.stop()

# Main app
st.title("Question Generator")

with st.form("generate_form"):
   subject = st.selectbox("Subject", ["Economics", "Geography", "History", "Miscellaneous- Factual, Static GK", "Polity"])
   count = st.number_input("Number of Questions", 1, 15, 10)
   complexity = st.selectbox("Complexity", ["Easy", "Medium", "Hard"])
   keywords = st.text_area("Keywords", "BB-Economics_part1 Keywords")
   question_type = st.selectbox("Question Type", ["Simple Statement MCQ", "Fill-in-the-Blanks MCQ", "Match-the-Column", "Multi-Statement Validation"])
   submitted = st.form_submit_button("Generate Questions")

if submitted:
   with st.spinner("Generating questions..."):
       response = start_workflow(subject, count, complexity, keywords, question_type)
       if response and "data" in response:
           result = response["data"]
           if result["status"] == "succeeded":
               questions = process_questions(result["outputs"]["result"])
               df = pd.DataFrame(questions, columns=["Question", "Options", "Option 1", "Option 2", "Option 3", "Correct Answer", "Explanation"])
               st.success("Questions generated successfully!")
               st.dataframe(df)
