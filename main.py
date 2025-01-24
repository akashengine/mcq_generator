import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_KEY = st.secrets["DIFY_API_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

def start_workflow(subject, count, complexity, keywords, question_type):
   url = "https://testing.drishtigpt.com/v1/workflows/run"
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
       response = requests.post(url, headers=headers, json=payload)
       response.raise_for_status()
       return response.json()
   except Exception as e:
       st.error(f"API Error: {e}")
       return None

def process_questions(result_text):
   questions = []
   current_q = []
   
   for line in result_text.split("\n"):
       if line.startswith("Question:"):
           if current_q:
               questions.append(current_q)
           current_q = [line.split("Question:")[1].strip()]
       elif line.strip().startswith("(") and len(line.strip()) > 2:
           current_q.append(line.strip())
       elif line.startswith("Correct Answer:"):
           current_q.append(line.split("Correct Answer:")[1].strip())
       elif line.startswith("Explanation:"):
           current_q.append(line.split("Explanation:")[1].strip())
           
   if current_q:
       questions.append(current_q)
       
   return questions

# Authentication
if "authenticated" not in st.session_state:
   st.session_state.authenticated = False
if "results" not in st.session_state:
   st.session_state.results = []

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
               formatted_questions = []
               
               for q in questions:
                   if len(q) >= 6:  # Question + 4 options + correct + explanation
                       formatted_questions.append({
                           "Question": q[0],
                           "Options": "\n".join(q[1:5]),
                           "Correct Answer": q[5],
                           "Explanation": q[6] if len(q) > 6 else ""
                       })
               
               st.session_state.results.insert(0, {
                   "timestamp": datetime.now(),
                   "questions": formatted_questions
               })
               
               st.success("Questions generated successfully!")
               
               with st.expander("View Generated Questions", expanded=True):
                   for q in formatted_questions:
                       st.markdown(f"**Question:** {q['Question']}")
                       st.markdown(f"**Options:**\n{q['Options']}")
                       st.markdown(f"**Correct Answer:** {q['Correct Answer']}")
                       st.markdown(f"**Explanation:** {q['Explanation']}")
                       st.divider()

# Show previous results
if st.session_state.results:
   st.header("Previously Generated Questions")
   for result in st.session_state.results[1:]:  # Skip the most recent one
       with st.expander(f"Generated at {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
           for q in result["questions"]:
               st.markdown(f"**Question:** {q['Question']}")
               st.markdown(f"**Options:**\n{q['Options']}")
               st.markdown(f"**Correct Answer:** {q['Correct Answer']}")
               st.markdown(f"**Explanation:** {q['Explanation']}")
               st.divider()
