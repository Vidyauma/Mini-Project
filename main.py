import streamlit as st
import requests
import json
import google.generativeai as genai
import random
import speech_recognition as sr
import pyttsx3
import pandas as pd
import numpy as np
from textblob import TextBlob
import streamlit as st
from streamlit_ace import st_ace
import requests
import json
import google.generativeai as genai
import matplotlib.pyplot as plt


import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase app if not already initialized
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize only once
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()





LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
# 🔹 Configure Gemini API
GENAI_API_KEY = "AIzaSyA1_G2JAeNJpaUp_DrHUuUaDCeJvNOHixA"  # Replace with your actual API key
genai.configure(api_key=GENAI_API_KEY)

# 🔹 Firebase Authentication API Keys
FIREBASE_API_KEY = "AIzaSyACv2f5iO06ptYa0tw2SJi6eOaGK_ogPGY"  # Replace with your actual Firebase API key
FIREBASE_SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
FIREBASE_SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
FIREBASE_DATABASE_URL = "https://interviewprepbot-default-rtdb.firebaseio.com/"
import firebase_admin
from firebase_admin import db

def store_data_in_firebase(user_id, category, data):
    """
    Stores user performance data in Firebase under the given category (aptitude, coding, hr).
    
    :param user_id: Unique user ID
    :param category: Section of interview process (aptitude, coding, hr)
    :param data: Dictionary containing user responses/scores
    """
    try:
        ref = db.reference(f"users/{user_id}/{category}")  # Reference user data path
        ref.set(data)  # Store/overwrite data
        print(f"✅ Successfully stored {category} data for {user_id}.")
    except Exception as e:
        print(f"❌ Error storing data: {e}")

def get_user_data_from_firebase(user_id, data_type):
    try:
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            return user_data.get(data_type, None)  # Fetch specific data type
        else:
            return None
    except Exception as e:
        print(f"❌ Error fetching {data_type} data: {e}")
        return None
# 📌 Function: User Signup
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

# 📌 Function: User Signup
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
                st.success("✅ Registration successful! You can now log in.")
                st.session_state["stage"] = "login"
                st.rerun()
            else:
                st.error("⚠️ Registration failed. Email may already be in use.")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

    if st.button("Already have an account? Login here"):
        st.session_state["stage"] = "login"
        st.rerun()

# 📌 Function: User Login
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
                st.success("✅ Login successful! Proceeding to chatbot...")
                st.session_state["stage"] = "chatbot"
                st.rerun()
            else:
                st.error("⚠️ Invalid credentials. Try again.")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

    if st.button("New User? Sign Up Here"):
        st.session_state["stage"] = "signup"
        st.rerun()

# 📌 Function: Chatbot Page (Job Role & Difficulty Selection)
def chatbot_page():
    st.title("🤖 AI Chatbot - Interview Prep")
    job_role = st.selectbox("👨‍💻 Select Your Job Role", ["Software Engineer", "Data Scientist", "Product Manager"])
    difficulty = st.selectbox("🎯 Select Difficulty Level", ["Easy", "Medium", "Hard"])

    if st.button("Start Aptitude Round"):
        # Store user choices in session state
        st.session_state["job_role"] = job_role
        st.session_state["difficulty"] = difficulty

        # Get the user ID from session state (you should already have this set after login/signup)
        user_id = st.session_state.get("user")

        if user_id:
            # Prepare the data to be stored in Firebase
            user_data = {
                "job_role": job_role,
                "difficulty": difficulty,
            }

            try:
                # Send the data to Firebase Realtime Database
                response = requests.patch(
                    f"{FIREBASE_DATABASE_URL}{user_id}.json",
                    json=user_data
                )

                if response.status_code == 200:
                    st.success("✅ Data saved successfully!")
                else:
                    st.error(f"⚠️ Failed to save data: {response.status_code}")

            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")

        # Move to the next stage (Aptitude Round)
        st.session_state["stage"] = "aptitude"
        st.rerun()
# 📌 Function: Generate Aptitude Questions using Google Gemini API




def fetch_aptitude_questions(difficulty):
    """
    Generates random aptitude questions based on difficulty (Easy, Medium, Hard).
    """
    prompt = f"""
    Generate 5 unique aptitude questions in JSON format based on difficulty: {difficulty}.
    Ensure variety in topics such as math, logic, reasoning, and general knowledge.
    Format strictly as:
    {{
        "questions": [
            {{
                "question": "What is 2+2?",
                "options": ["2", "3", "4", "5"],
                "correct_answer": "4"
            }},
            {{
                "question": "What is the capital of France?",
                "options": ["Berlin", "Paris", "Madrid", "Rome"],
                "correct_answer": "Paris"
            }}
        ]
    }}
    """
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    # Ensure proper JSON formatting
    response_text = response.text.strip().replace("```json", "").replace("```", "").strip()

    try:
        questions_data = json.loads(response_text)
        random.shuffle(questions_data["questions"])  # Shuffle for randomness
        return questions_data.get("questions", [])
    except json.JSONDecodeError as e:
        print(f"❌ Failed to fetch questions: {e}")
        return []

# 📌 Function: Store Aptitude Data in Firebase
def store_aptitude_data_in_firebase(user_id, questions, score):
    """
    Store generated aptitude questions and user's score in Firebase.
    """
    try:
        data = {
            "questions": questions,
            "score": score  # Ensure score is stored
        }

        response = requests.patch(
            f"{FIREBASE_DATABASE_URL}users/{user_id}/aptitude.json",
            json=data
        )

        if response.status_code == 200:
            st.success("✅ Aptitude round data saved successfully.")
        else:
            st.error(f"⚠️ Failed to save aptitude data: {response.status_code} - {response.text}")

    except Exception as e:
        st.error(f"⚠️ Error saving aptitude data: {str(e)}")

# 📌 Function: Aptitude Round
import streamlit as st

def aptitude_round_page():
    """
    Aptitude round where dynamically generated questions are displayed.
    """
    st.title("📝 Aptitude Round")

    # Check if difficulty level is set
    if "difficulty" not in st.session_state:
        st.error("⚠️ Difficulty level not set. Please go back and select it.")
        return
    
    difficulty = st.session_state["difficulty"]
    st.write(f"**Selected Difficulty Level:** {difficulty.capitalize()}")

    # Fetch new questions if not already stored in session
    if "aptitude_questions" not in st.session_state:
        st.session_state["aptitude_questions"] = fetch_aptitude_questions(difficulty)
        st.session_state["current_question"] = 0
        st.session_state["score"] = 0

    questions = st.session_state["aptitude_questions"]

    if not questions:
        st.error("⚠️ No questions generated. Please try again.")
        return

    current_question = st.session_state["current_question"]

    if current_question < len(questions):
        q = questions[current_question]
        st.write(f"**Q{current_question+1}: {q['question']}**")
        user_answer = st.radio("Choose an option:", q["options"], key=f"q{current_question}")

        if st.button("Submit Answer"):
            if user_answer == q["correct_answer"]:
                st.session_state["score"] += 1
            st.session_state["current_question"] += 1
            st.rerun()

    else:
        st.success(f"✅ Test Completed! Your Score: {st.session_state['score']}/{len(questions)}")
        
        # ✅ Save the results in Firebase
        user_id = st.session_state.get("user")
        if user_id:
            store_aptitude_data_in_firebase(user_id, "aptitude", {
                "score": st.session_state["score"],
                "total_questions": len(questions)
            })

        # Navigate to the Coding Round
        if st.button("➡️ Proceed to Coding Round"):
            st.session_state["stage"] = "coding"
            st.rerun()

# 📌 Function: Generate External Coding Challenge Link
def store_coding_data(user_id, completed_problems):
    try:
        # Initialize Firestore (assuming already initialized)
        doc_ref = db.collection('coding_progress').document(user_id)
        
        # Save the data under the user ID
        doc_ref.set({"completed_problems": completed_problems})
        
        print("✅ Coding data stored successfully for user:", user_id)
    except Exception as e:
        print(f"❌ Error storing coding data: {e}")


# ✅ Get Coding Challenge Links
def get_coding_challenge_link(job_role, difficulty):
    base_urls = {
        "LeetCode": "https://leetcode.com/problemset/all/?difficulty=",
        "CodeChef": "https://www.codechef.com/problems/school",
        "GeeksforGeeks": "https://practice.geeksforgeeks.org/explore/?page=1",
        "AtCoder": "https://atcoder.jp/"
    }

    difficulty_map = {
        "Easy": "EASY",
        "Medium": "MEDIUM",
        "Hard": "HARD"
    }

    difficulty_param = difficulty_map.get(difficulty, "EASY")
    links = {
        "LeetCode": base_urls["LeetCode"] + difficulty_param,
        "CodeChef": base_urls["CodeChef"],
        "GeeksforGeeks": base_urls["GeeksforGeeks"]
    }
    return links

def coding_round_page():
    st.title("💻 Coding Round")
    user_id = st.session_state.get("user")
    if not user_id:
        st.error("Please login first.")
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
        result = st.session_state.get("coding_result")
        code = st.session_state.get("submitted_code")

        st.subheader("✅ Evaluation Result")
        st.write("**Correct:**", result.get("is_correct"))
        if not result.get("is_correct"):
            st.write("**Explanation:**", result.get("explanation"))
            st.code(result.get("correct_code"), language=language.lower())

        # Store result
        store_coding_result(user_id, question, code, result)
        st.success("Result saved!")

        if st.button("➡️ Proceed to HR Round"):
            st.session_state["stage"] = "hr_round"
            st.rerun()

def generate_unique_coding_question():
    prompt = """
    Generate 1 unique coding interview question in plain text. Make sure it's clear and concise.
    Example topics: strings, arrays, sorting, recursion, graphs, dynamic programming.
    Output only the question text.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

def evaluate_code_with_gemini(question, user_code, language):
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = f'''
    Evaluate the following coding question:
    Language: {language}
    Question: {question}
    Code:
    {user_code}

    Respond in JSON format:
    {{
        "is_correct": true/false,
        "explanation": "...",
        "correct_code": "..."
    }}
    '''
    response = model.generate_content(prompt)
    response_text = response.text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        st.error("⚠️ Gemini returned invalid JSON. Showing raw output.")
        st.code(response_text)
        return {
            "is_correct": False,
            "explanation": "Could not parse Gemini response.",
            "correct_code": "N/A"
        }

def store_coding_result(user_id, question, user_code, result_data):
    data = {
        "question": question,
        "user_code": user_code,
        "evaluation": result_data
    }
    url = f"{FIREBASE_DATABASE_URL}users/{user_id}/coding.json"
    requests.patch(url, json=data)

def store_hr_response(user_id, question, response_text):
    data = {
        question: response_text
    }
    url = f"{FIREBASE_DATABASE_URL}users/{user_id}/hr.json"
    requests.patch(url, json=data)


import speech_recognition as sr
import streamlit as st
import pyttsx3
import time

import streamlit as st
import speech_recognition as sr
import pyttsx3
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.generativeai import GenerativeModel

# Firebase Initialization


def hr_interview_page():
    st.title("🎤 HR Interview Round")
    st.write("The chatbot will ask HR-related questions based on your resume. Respond using voice!")

    user_id = st.session_state.get("user")
    if not user_id:
        st.error("⚠️ User not logged in. Please login first.")
        return

    if "resume_data" not in st.session_state:
        uploaded_file = st.file_uploader("📂 Upload Your Resume (PDF/Text)", type=["pdf", "txt"])
        if uploaded_file is not None:
            st.session_state["resume_data"] = extract_resume_text(uploaded_file)
            st.success("✅ Resume uploaded successfully!")

    if "resume_data" in st.session_state:
        if "hr_questions" not in st.session_state:
            st.session_state["hr_questions"] = generate_hr_questions(st.session_state["resume_data"])
            st.session_state["current_hr_question"] = 0

        questions = st.session_state["hr_questions"]
        responses = st.session_state.get("hr_responses", {})

        if st.session_state["current_hr_question"] < len(questions):
            question = questions[st.session_state["current_hr_question"]]
            speak(question)
            st.write(f"**Bot:** {question}")

            if st.button("🎙️ Answer with Voice"):
                user_response = recognize_speech()
                if user_response:
                    st.write(f"**You:** {user_response}")
                    responses[question] = user_response  # Store in session state
                    store_hr_response(user_id, question, user_response)  # Store in Firebase
                    st.session_state["current_hr_question"] += 1
                    st.rerun()
        else:
            st.success("🎉 HR Interview Completed! Proceeding to Performance Analysis.")
            if st.button("➡️ Proceed to Performance Analysis"):
                st.session_state["stage"] = "performance_analysis"
                st.rerun()

# 🔹 Firebase Storage Function
def store_hr_response_in_firebase(user_id, question, response):
    try:
        user_ref = db.collection("users").document(user_id).collection("hr_responses").document()
        user_ref.set({"question": question, "response": response})
        print("✅ HR response stored successfully!")
    except Exception as e:
        print(f"❌ Error storing HR response: {e}")
# 🔹 Resume Processing & Question Generation
def extract_resume_text(uploaded_file):
    return "Sample extracted resume text based on uploaded file."

def generate_hr_questions(resume_text):
    prompt = f"""
    Generate 5 HR interview questions based on this resume data:
    {resume_text}
    Provide questions only in JSON format as:
    {{"questions": ["Question 1", "Question 2", "Question 3"]}}
    """
    model = GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    response_text = response.text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(response_text).get("questions", [])
    except:
        return ["Tell me about yourself.", "Why do you want this job?", "What are your strengths and weaknesses?"]

# 🔹 Voice Processing
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎙️ Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Could not understand your response."
        except sr.RequestError:
            return "Speech recognition service is unavailable."

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def store_performance_data(user_id, data):
    """
    Store performance analysis data in Firebase.
    """
    try:
        response = requests.patch(
            f"{FIREBASE_DATABASE_URL}{user_id}/performance_analysis.json",
            json=data
        )
        if response.status_code == 200:
            st.success("✅ Performance analysis saved successfully.")
        else:
            st.error(f"⚠️ Failed to save data to Firebase: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error saving performance data: {str(e)}")



def store_performance_data(user_id, aptitude, coding, hr):
    data = {
        "aptitude_score": aptitude,
        "coding_score": coding,
        "hr_completed": hr
    }
    url = f"{FIREBASE_DATABASE_URL}users/{user_id}/performance_analysis.json"
    requests.patch(url, json=data)

def analyze_performance():
    st.title("📊 Performance Analysis")
    user_id = st.session_state.get("user")
    if not user_id:
        st.error("Please login first.")
        return

    # Mock data or fetch from DB
    aptitude_score = 3
    coding_score = 1
    hr_done = True

    # Store to Firebase via REST
    store_performance_data(user_id, aptitude_score, coding_score, hr_done)

    plot_performance(aptitude_score, coding_score, hr_done)
    feedback = generate_ai_feedback(aptitude_score, coding_score, hr_done)

    st.subheader("🧠 AI Feedback")
    st.markdown(feedback)

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

    
# 📌 Function: Main Navigation
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


# Run the App
if __name__ == "__main__":
    main()

