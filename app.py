import io
import json
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

st.set_page_config(page_title="AI Answer Grader", layout="wide")

# Initialize session storage for results
if "results" not in st.session_state:
    st.session_state.results = []

st.title("📝 AI Answer Assessment System")

# Sidebar for API Key and Question Setup
with st.sidebar:
    st.header("⚙️ Teacher Setup")
    api_key = st.text_input("Enter Gemini API Key", type="password")

    st.subheader("Question & Scheme")
    question_text = st.text_area("Question", placeholder="e.g., Explain the process of photosynthesis.")
    scheme_text = st.text_area("Marking Scheme / Expected Answer", placeholder="e.g., Must mention: Light energy, Chlorophyll, Water + CO2 -> Glucose + O2.")

st.markdown("---")

# Main Page - Student Submission
st.header("📤 Student Portal")

col1, col2 = st.columns([1, 2])

with col1:
    student_name = st.text_input("Enter Student Name")
    uploaded_file = st.file_uploader("Upload Handwritten Answer (Photo)", type=["jpg", "jpeg", "png"])
    submit_button = st.button("Submit Answer for Grading")

if submit_button:
    if not api_key:
        st.error("Please enter the Gemini API Key in the sidebar.")
    elif not question_text or not scheme_text:
        st.error("Teacher must set the Question and Marking Scheme in the sidebar.")
    elif not student_name:
        st.error("Please enter your name.")
    elif not uploaded_file:
        st.error("Please upload an image of your answer.")
    else:
        try:
            with st.spinner("Grading answer... Please wait."):
                client = genai.Client(api_key=api_key)
                
                # Load image
                image = Image.open(uploaded_file)

                # Construct prompt
                prompt = f"""
                You are an strict exam evaluator. Grade the handwritten answer in the image against the provided question and marking scheme.

                Question: {question_text}
                Marking Scheme: {scheme_text}

                Evaluate carefully and provide the output strictly matching this structure:
                - Score: numerical grade or brief fraction (e.g., '4/5' or '80%')
                - Missing Keywords/Ideas: A concise summary (1-2 sentences) of key ideas or terms missing from the student's answer.
                """

                # Call Gemini API
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[image, prompt]
                )

                # Save response to session state
                result_entry = {
                    "Student Name": student_name,
                    "Score": response.text,
                    "Uploaded File": uploaded_file.name
                }
                st.session_state.results.append(result_entry)
                st.success(f"Graded successfully for {student_name}!")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Display Grading Results Grid
st.markdown("---")
st.header("📊 Results Dashboard")

if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df, use_container_width=True)

    # Excel / CSV Export
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Results as CSV (Excel)",
        data=csv,
        file_name="grading_results.csv",
        mime="text/csv",
    )
    
    if st.button("Clear Results for Next Question"):
        st.session_state.results = []
        st.experimental_rerun()
else:
    st.info("No submissions graded yet for this session.")
