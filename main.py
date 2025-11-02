import json
import random
import streamlit as st
import requests
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from textblob import TextBlob
from streamlit_ace import st_ace
import firebase_admin
from firebase_admin import credentials, firestore, db

# Initialize Firebase if not already done
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://interviewprepbot-default-rtdb.firebaseio.com/"
    })
firestore_db = firestore.client()
# 🔹 Gemini API Key (move to Streamlit secrets or .env in production)
GENAI_API_KEY = "YOUR_GENAI_API_KEY"
genai.configure(api_key=GENAI_API_KEY)

# 🔹 Firebase Authentication
FIREBASE_API_KEY = "YOUR_FIREBASE_API_KEY"
FIREBASE_SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
FIREBASE_SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
FIREBASE_DATABASE_URL = "https://interviewprepbot-default-rtdb.firebaseio.com/"

# ------------------------ Firebase Utility Functions ------------------------
def store_data_in_firebase(user_id, category, data):
    try:
        ref = db.reference(f"users/{user_id}/{category}")
        ref.set(data)
        print(f"✅ Successfully stored {category} data for {user_id}.")
    except Exception as e:
        print(f"❌ Error storing data: {e}")

def get_user_data_from_firebase(user_id, data_type):
    try:
        user_ref = firestore_db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if user_doc.exists:
            return user_doc.to_dict().get(data_type, None)
        return None
    except Exception as e:
        print(f"❌ Error fetching {data_type} data: {e}")
        return None

def store_user_data(user_id, email):
    try:
        data = {user_id: {"email": email}}
        response = requests.patch(FIREBASE_DATABASE_URL, json=data)
        if response.status_code == 200:
            st.success("✅ User data stored successfully!")
        else:
            st.error("⚠️ Failed to store user data.")
    except Exception as e:
        st.error(f"⚠️ Error storing user data: {str(e)}")

# ------------------------ Auth: Signup ------------------------
def signup():
    st.title("📝 Sign Up")
    email = st.text_input("📧 Email")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Register"):
        try:
            payload = {"email": email, "password": password, "returnSecureToken": True}
            response = requests.post(FIREBASE_SIGNUP_URL, json=payload)

            if response.status_code == 200:
                user_data = response.json()
                store_user_data(user_data["localId"], email)
                st.success("✅ Registration successful!")
                st.session_state["stage"] = "login"
                st.rerun()
            else:
                st.error("⚠️ Registration failed. Email may already be in use.")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

    if st.button("Already have an account? Login here"):
        st.session_state["stage"] = "login"
        st.rerun()

# ------------------------ Auth: Login ------------------------
def login():
    st.title("🔐 Login Page")
    email = st.text_input("📧 Email")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Login"):
        try:
            payload = {"email": email, "password": password, "returnSecureToken": True}
            response = requests.post(FIREBASE_SIGNIN_URL, json=payload)

            if response.status_code == 200:
                user_data = response.json()
                st.session_state["user"] = user_data["localId"]
                st.success("✅ Login successful!")
                st.session_state["stage"] = "chatbot"
                st.rerun()
            else:
                st.error("⚠️ Invalid credentials.")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

    if st.button("New User? Sign Up Here"):
        st.session_state["stage"] = "signup"
        st.rerun()

# ------------------------ Chatbot Page ------------------------
def chatbot_page():
    st.title("🤖 AI Chatbot - Interview Prep")
    job_role = st.selectbox("👨‍💻 Select Your Job Role", ["Software Engineer", "Data Scientist", "Product Manager"])
    difficulty = st.selectbox("🎯 Select Difficulty Level", ["Easy", "Medium", "Hard"])

    if st.button("Start Aptitude Round"):
        st.session_state["job_role"] = job_role
        st.session_state["difficulty"] = difficulty
        user_id = st.session_state.get("user")

        if user_id:
            user_data = {"job_role": job_role, "difficulty": difficulty}
            try:
                response = requests.patch(f"{FIREBASE_DATABASE_URL}{user_id}.json", json=user_data)
                if response.status_code == 200:
                    st.success("✅ Data saved successfully!")
                else:
                    st.error(f"⚠️ Failed to save data: {response.status_code}")
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")

        st.session_state["stage"] = "aptitude"
        st.rerun()

# ------------------------ Gemini API: Aptitude Questions ------------------------
def fetch_aptitude_questions(difficulty):
    prompt = f"""
    Generate 5 unique aptitude questions in JSON format based on difficulty: {difficulty}.
    Ensure variety in topics such as math, logic, reasoning, and general knowledge.
    Format:
    {{
        "questions": [
            {{
                "question": "Sample question?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A"
            }},
            ...
        ]
    }}
    """
# ------------------------ Aptitude Round Page ------------------------
def aptitude_round_page():
    st.title("📝 Aptitude Round")

    if "difficulty" not in st.session_state:
        st.error("⚠️ Please go back and select a difficulty level.")
        return

    difficulty = st.session_state["difficulty"]

    if "aptitude_questions" not in st.session_state:
        st.session_state["aptitude_questions"] = fetch_aptitude_questions(difficulty)
        st.session_state["current_question"] = 0
        st.session_state["score"] = 0

    questions = st.session_state["aptitude_questions"]
    current = st.session_state["current_question"]

    if current < len(questions):
        q = questions[current]
        st.write(f"**Q{current + 1}: {q['question']}**")
        user_answer = st.radio("Choose an option:", q["options"], key=f"q{current}")

        if st.button("Submit Answer"):
            if user_answer == q["correct_answer"]:
                st.session_state["score"] += 1
            st.session_state["current_question"] += 1
            st.rerun()
    else:
        st.success(f"✅ Completed! Score: {st.session_state['score']}/{len(questions)}")
        user_id = st.session_state.get("user")
        if user_id:
            store_data_in_firebase(user_id, "aptitude", {
                "score": st.session_state["score"],
                "total_questions": len(questions)
            })
        if st.button("➡️ Proceed to Coding Round"):
            st.session_state["stage"] = "coding"
            st.rerun()

# ------------------------ Coding Round Page ------------------------
def coding_round_page():
    st.title("💻 Coding Round")
    user_id = st.session_state.get("user")
    if not user_id:
        st.error("⚠️ Please log in first.")
        return

    language = st.selectbox("Choose Language", ["Python", "C++", "Java"])

    if "coding_question" not in st.session_state:
        st.session_state["coding_question"] = generate_unique_coding_question()

    question = st.session_state["coding_question"]
    st.write(f"### Question: {question}")

    code = st_ace(language=language.lower(), theme="monokai", key="editor")

    if st.button("🧪 Submit Code"):
        result = evaluate_code_with_gemini(question, code, language)
        st.session_state["coding_result"] = result
        st.session_state["submitted_code"] = code
        st.session_state["code_submitted"] = True
        st.rerun()

    if st.session_state.get("code_submitted"):
        result = st.session_state["coding_result"]
        st.subheader("✅ Evaluation Result")
        st.write("**Correct:**", result.get("is_correct"))
        if not result.get("is_correct"):
            st.write("**Explanation:**", result.get("explanation"))
            st.code(result.get("correct_code"), language=language.lower())

        store_data_in_firebase(user_id, "coding", {
            "question": question,
            "user_code": code,
            "evaluation": result
        })

        if st.button("➡️ Proceed to HR Round"):
            st.session_state["stage"] = "hr_round"
            st.rerun()

# ------------------------ HR Interview Page ------------------------
def hr_interview_page():
    st.title("🎤 HR Interview Round")
    user_id = st.session_state.get("user")
    if not user_id:
        st.error("⚠️ Please login first.")
        return

    if "resume_data" not in st.session_state:
        uploaded = st.file_uploader("📂 Upload Resume", type=["pdf", "txt"])
        if uploaded:
            st.session_state["resume_data"] = extract_resume_text(uploaded)
            st.success("✅ Resume uploaded!")

    if "resume_data" in st.session_state:
        if "hr_questions" not in st.session_state:
            st.session_state["hr_questions"] = generate_hr_questions(st.session_state["resume_data"])
            st.session_state["current_hr_question"] = 0

        questions = st.session_state["hr_questions"]
        current = st.session_state["current_hr_question"]

        if current < len(questions):
            q = questions[current]
            speak(q)
            st.write(f"**Bot:** {q}")

            if st.button("🎙️ Answer with Voice"):
                response = recognize_speech()
                if response:
                    st.write(f"**You:** {response}")
                    store_data_in_firebase(user_id, f"hr/question_{current + 1}", response)
                    st.session_state["current_hr_question"] += 1
                    st.rerun()
        else:
            st.success("🎉 HR Round Completed!")
            if st.button("➡️ Proceed to Performance Analysis"):
                st.session_state["stage"] = "performance_analysis"
                st.rerun()

# ------------------------ Performance Analysis ------------------------
def analyze_performance():
    st.title("📊 Performance Analysis")
    user_id = st.session_state.get("user")
    if not user_id:
        st.error("⚠️ Please login first.")
        return

    aptitude = st.session_state.get("score", 0)
    coding = 1  # Example
    hr = True

    store_data_in_firebase(user_id, "performance_analysis", {
        "aptitude_score": aptitude,
        "coding_score": coding,
        "hr_completed": hr
    })

    plot_performance(aptitude, coding, hr)
    feedback = generate_ai_feedback(aptitude, coding, hr)
    st.subheader("🧠 AI Feedback")
    st.markdown(feedback)

# ------------------------ Plot & Feedback ------------------------
def plot_performance(aptitude, coding, hr):
    labels = ['Aptitude', 'Coding', 'HR']
    values = [aptitude, coding, int(hr)]
    fig, ax = plt.subplots()
    ax.bar(labels, values, color=['blue', 'green', 'orange'])
    st.pyplot(fig)

def generate_ai_feedback(aptitude, coding, hr):
    prompt = f"""
    Give feedback:
    - Aptitude: {aptitude}/5
    - Coding: {coding}/3
    - HR: {'Yes' if hr else 'No'}
    Respond with improvement tips in bullet points.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model.generate_content(prompt).text

# ------------------------ Main ------------------------
def main():
    if "stage" not in st.session_state:
        st.session_state["stage"] = "login"

    if st.session_state["stage"] == "login":
        login()
    elif st.session_state["stage"] == "signup":
        signup()
    elif st.session_state["stage"] == "chatbot":
        chatbot_page()
    elif st.session_state["stage"] == "aptitude":
        aptitude_round_page()
    elif st.session_state["stage"] == "coding":
        coding_round_page()
    elif st.session_state["stage"] == "hr_round":
        hr_interview_page()
    elif st.session_state["stage"] == "performance_analysis":
        analyze_performance()

if __name__ == "__main__":
    main()
