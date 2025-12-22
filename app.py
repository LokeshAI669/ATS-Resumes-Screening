import base64
import io
import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
import streamlit as st

# Load environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_prompt, pdf_content, job_description):
    """
    Calls the Gemini 2.5 Flash model which supports image and text input.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content([input_prompt, pdf_content[0], job_description])
    return response.text

def input_pdf_setup(uploaded_file):
    """
    Converts the first page of the uploaded PDF into an image format 
    that Gemini can understand, without requiring Poppler.
    """
    if uploaded_file is not None:
        # Read the file bytes
        file_bytes = uploaded_file.read()
        
        # Open PDF using PyMuPDF (fitz)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Get the first page
        page = doc.load_page(0)
        
        # Convert page to an image (pixmap)
        pix = page.get_pixmap()
        
        # Convert pixmap to JPEG bytes
        img_byte_arr = pix.tobytes("jpeg")

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No PDF file uploaded.")

# --- Streamlit UI Configuration ---
st.set_page_config(page_title="ATS Resume Screener", page_icon=":robot_face:", layout="wide")

st.header("ATS Resume Screener :robot_face:")
st.subheader("Optimize your resume for AI-driven hiring systems")

# Input sections
input_text = st.text_area("Job Description:", placeholder="Paste the Job Description here...", key="input", height=200)
uploaded_file = st.file_uploader("Upload Resume (PDF format only):", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ PDF uploaded successfully!")

# Buttons for interaction
col1, col2, col3, col4 = st.columns(4)

with col1:
    submit1 = st.button("Resume Summary")
with col2:
    submit2 = st.button("Skills Improvement")
with col3:
    submit3 = st.button("Keyword Analysis")
with col4:
    submit4 = st.button("Percentage Match")

# --- Prompts ---
prompt_summary = """
You are an experienced HR professional. Review the provided resume against the job description. 
Provide a professional evaluation: what are the candidate's strengths and weaknesses, 
and are they a good fit for this specific role?
"""

prompt_keywords = """
You are an ATS (Applicant Tracking System) expert. Compare the resume to the job description 
and list the specific technical and soft skill keywords that are missing from the resume.
"""

prompt_skills = """
Based on the Job Description and the candidate's current resume, what specific certifications, 
projects, or technical skills should the candidate acquire to become a 100% match?
"""

prompt_match = """
You are an ATS scanner. Give a percentage match for this resume against the job description. 
Provide the percentage first, then a list of missing keywords, and finally a concluding thought.
"""

# --- Execution Logic ---
if any([submit1, submit2, submit3, submit4]):
    if uploaded_file is not None and input_text.strip() != "":
        with st.spinner("Analyzing with AI..."):
            pdf_content = input_pdf_setup(uploaded_file)
            
            # Determine which prompt to use
            if submit1:
                response = get_gemini_response(prompt_summary, pdf_content, input_text)
            elif submit2:
                response = get_gemini_response(prompt_skills, pdf_content, input_text)
            elif submit3:
                response = get_gemini_response(prompt_keywords, pdf_content, input_text)
            elif submit4:
                response = get_gemini_response(prompt_match, pdf_content, input_text)
                
            st.divider()
            st.subheader("AI Analysis Result:")
            st.write(response)
    else:
        st.warning("Please provide both a Job Description and a Resume PDF.")