import pandas as pd
import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="AI Answer Assessment System", layout="wide")

# Persistent storage for session setup and student results
if "results" not in st.session_state:
    st.session_state.results = []
if "question_img" not in st.session_state:
    st.session_state.question_img = None
if "scheme_img" not in st.session_state:
    st.session_state.scheme_img = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.title("📝 AI Answer Assessment System")

# Select Role to split Teacher setup and Student view
role = st.radio("Select Portal:", ["Student Portal", "Teacher Control Panel"], horizontal=True)

st.markdown("---")

# ==================== TEACHER CONTROL PANEL ====================
if role == "Teacher Control Panel":
    st.header("⚙️ Teacher Setup & Live Dashboard")
    
    passcode = st.text_input("Enter Teacher Passcode", type="password")
    
    # Passcode set to '1234' by default
    if passcode == "1234":
        st.success("Authenticated")
        
        st.session_state.api_key = st.text_input(
            "Gemini API Key", 
            value=st.session_state.api_key, 
            type="password"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1. Upload Question Image")
            q_file = st.file_uploader("Question Image", type=["jpg", "jpeg", "png"], key="q_file")
            if q_file:
                st.session_state.question_img = Image.open(q_file)
                st.image(st.session_state.question_img, caption="Question Ready", width=250)

        with col2:
            st.subheader("2. Upload Marking Scheme Image")
            s_file = st.file_uploader("Marking Scheme Image", type=["jpg", "jpeg", "png"], key="s_file")
            if s_file:
                st.session_state.scheme_img = Image.open(s_file)
                st.image(st.session_state.scheme_img, caption="Marking Scheme Ready", width=250)

        st.markdown("---")
        st.header("📊 Class Results Grid")
        
        if st.session_state.results:
            df = pd.DataFrame(st.session_state.results)
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results as Excel (CSV)",
                data=csv,
                file_name="student_grades.csv",
                mime="text/csv",
            )
            
            if st.button("Clear Results for Next Question"):
                st.session_state.results = []
                st.experimental_rerun()
        else:
            st.info("Waiting for student submissions...")

    elif passcode != "":
        st.error("Incorrect passcode.")

# ==================== STUDENT PORTAL ====================
else:
    st.header("📤 Student Answer Submission")
    
    # Check if Teacher has completed setup
    if not st.session_state.api_key or not st.session_state.question_img or not st.session_state.scheme_img:
        st.warning("The question is not active yet. Please wait for your teacher to set up the question.")
    else:
        student_name = st.text_input("Enter Your Full Name")
        ans_file = st.file_uploader("Upload Picture of Your Handwritten Answer", type=["jpg", "jpeg", "png"])
        
        submit_button = st.button("Submit Answer")

        if submit_button:
            if not student_name:
                st.error("Please enter your name before submitting.")
            elif not ans_file:
                st.error("Please select a picture of your answer to upload.")
            else:
                try:
                    with st.spinner("Submitting and grading answer... Please wait."):
                        client = genai.Client(api_key=st.session_state.api_key)
                        
                        student_ans_img = Image.open(ans_file)

                        prompt = """
                        You are an accurate exam evaluator. You are provided with 3 images in this order:
                        1. Image 1: Question
                        2. Image 2: Official Marking Scheme
                        3. Image 3: Student's Handwritten Answer

                        Compare Image 3 against Image 1 and Image 2.
                        Return your evaluation in two distinct sections:
                        Score: [Numeric mark or fraction]
                        Missing Ideas/Keywords: [Concise 1-2 sentence description of missing or incorrect points]
                        """

                        # Evaluate images via Gemini API
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[
                                st.session_state.question_img, 
                                st.session_state.scheme_img, 
                                student_ans_img, 
                                prompt
                            ]
                        )

                        # Output parsing into columns
                        full_text = response.text
                        score = "Evaluated"
                        missing_ideas = full_text

                        if "Score:" in full_text and "Missing Ideas/Keywords:" in full_text:
                            parts = full_text.split("Missing Ideas/Keywords:")
                            score = parts[0].replace("Score:", "").strip()
                            missing_ideas = parts[1].strip()

                        # Append student response to grid
                        st.session_state.results.append({
                            "Student Name": student_name,
                            "Score": score,
                            "Missing Ideas / Keywords": missing_ideas
                        })
                        
                        st.success(f"Successfully submitted! Your answer has been evaluated, {student_name}.")

                except Exception as e:
                    st.error(f"Submission error: {str(e)}")
