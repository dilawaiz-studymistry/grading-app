import pandas as pd
import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="AI Answer Assessment System", layout="wide")

# ==================== SHARED GLOBAL MEMORY ====================
@st.cache_resource
def get_global_store():
    return {
        "api_key": "",
        "question_img": None,
        "scheme_img": None,
        "results": []
    }

global_store = get_global_store()

st.title("📝 AI Answer Assessment System")

# Navigation
role = st.radio("Select Portal:", ["Student Portal", "Teacher Control Panel"], horizontal=True)

st.markdown("---")

# ==================== TEACHER CONTROL PANEL ====================
if role == "Teacher Control Panel":
    st.header("⚙️ Teacher Setup & Live Dashboard")
    
    passcode = st.text_input("Enter Teacher Passcode", type="password")
    
    if passcode == "1234":
        st.success("Authenticated")
        
        # Save API key to global store
        api_input = st.text_input("Gemini API Key", value=global_store["api_key"], type="password")
        if api_input:
            global_store["api_key"] = api_input.strip()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1. Upload Question Image")
            q_file = st.file_uploader("Question Image", type=["jpg", "jpeg", "png"], key="q_file")
            if q_file:
                global_store["question_img"] = Image.open(q_file)
                st.image(global_store["question_img"], caption="Question Active Globally", width=250)

        with col2:
            st.subheader("2. Upload Marking Scheme Image")
            s_file = st.file_uploader("Marking Scheme Image", type=["jpg", "jpeg", "png"], key="s_file")
            if s_file:
                global_store["scheme_img"] = Image.open(s_file)
                st.image(global_store["scheme_img"], caption="Marking Scheme Active Globally", width=250)

        st.markdown("---")
        st.header("📊 Class Results Grid")
        
        if st.button("🔄 Refresh Student Submissions"):
            st.rerun()

        if global_store["results"]:
            df = pd.DataFrame(global_store["results"])
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results as Excel (CSV)",
                data=csv,
                file_name="student_grades.csv",
                mime="text/csv",
            )
            
            if st.button("Clear Question & Results (For Next Question)"):
                global_store["results"] = []
                global_store["question_img"] = None
                global_store["scheme_img"] = None
                st.rerun()
        else:
            st.info("No submissions received yet.")

    elif passcode != "":
        st.error("Incorrect passcode.")

# ==================== STUDENT PORTAL ====================
else:
    st.header("📤 Student Answer Submission")
    
    has_key = bool(global_store["api_key"])
    has_q = global_store["question_img"] is not None
    has_s = global_store["scheme_img"] is not None

    if not (has_key and has_q and has_s):
        st.warning("The question is not active yet. Please wait for your teacher to set up the question.")
        if st.button("🔄 Refresh Page / Check Again"):
            st.rerun()
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
                        client = genai.Client(api_key=global_store["api_key"])
                        student_ans_img = Image.open(ans_file)

                        prompt = """
                        You are an accurate exam evaluator. You are provided with 3 images:
                        1. Image 1: Question
                        2. Image 2: Official Marking Scheme
                        3. Image 3: Student's Handwritten Answer

                        Compare Image 3 against Image 1 and Image 2.
                        Return your evaluation in two distinct sections:
                        Score: [Numeric mark or fraction]
                        Missing Ideas/Keywords: [Concise 1-2 sentence description of missing or incorrect points]
                        """

                        # List of candidate model names to guarantee a hit
                        candidate_models = [
                            'gemini-2.5-flash',
                            'gemini-1.5-flash-latest',
                            'gemini-1.5-flash-002',
                            'gemini-1.5-flash',
                            'gemini-2.0-flash'
                        ]

                        response = None
                        last_exception = None

                        # Try each candidate model until one succeeds
                        for m_name in candidate_models:
                            try:
                                response = client.models.generate_content(
                                    model=m_name,
                                    contents=[
                                        global_store["question_img"], 
                                        global_store["scheme_img"], 
                                        student_ans_img, 
                                        prompt
                                    ]
                                )
                                break
                            except Exception as e:
                                last_exception = e
                                continue

                        if response is None:
                            raise last_exception

                        full_text = response.text
                        score = "Evaluated"
                        missing_ideas = full_text

                        if "Score:" in full_text and "Missing Ideas/Keywords:" in full_text:
                            parts = full_text.split("Missing Ideas/Keywords:")
                            score = parts[0].replace("Score:", "").strip()
                            missing_ideas = parts[1].strip()

                        global_store["results"].append({
                            "Student Name": student_name,
                            "Score": score,
                            "Missing Ideas / Keywords": missing_ideas
                        })
                        
                        st.success(f"Successfully submitted! Your answer has been evaluated, {student_name}.")

                except Exception as e:
                    st.error(f"Submission error: {str(e)}")
