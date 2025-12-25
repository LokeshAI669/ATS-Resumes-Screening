import base64
import io
import os
import re
import html
import json
import fitz  # PyMuPDF
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
import streamlit as st
import streamlit.components.v1 as components

# -------------------------------------------
# Load environment variables & configure Gemini
# -------------------------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# -------------------------------------------
# Original Functions (UNCHANGED)
# -------------------------------------------
def get_gemini_response(input_prompt, pdf_content, job_description):
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content([input_prompt, pdf_content[0], job_description])
    return response.text

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page = doc.load_page(0)
        pix = page.get_pixmap()
        img_byte_arr = pix.tobytes("jpeg")

        return [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()
        }]
    else:
        raise FileNotFoundError("No PDF uploaded")

# -------------------------------------------
# Page Config
# -------------------------------------------
st.set_page_config(page_title="ATS Resume Screener", layout="wide")

st.title("🤖 ATS Resume Screener")

# -------------------------------------------
# Inputs (UNCHANGED)
# -------------------------------------------
job_description = st.text_area("Paste Job Description", height=200)
uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

# -------------------------------------------
# Buttons (ONLY ONE ADDED)
# -------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    submit1 = st.button("🧾 Resume Summary")
with c2:
    submit2 = st.button("🛠 Skills Improvement")
with c3:
    submit3 = st.button("🔎 Keyword Analysis")
with c4:
    submit4 = st.button("📊 Percentage Match")
with c5:
    submit5 = st.button("🧮 ATS Resume Score")  # ✅ ONLY NEW BUTTON

# -------------------------------------------
# Prompts (UNCHANGED)
# -------------------------------------------
prompt_summary = """
You are an experienced HR professional. Review the resume against the job description.
Give strengths, weaknesses, and suitability.
"""

prompt_skills = """
Suggest missing skills, certifications, and projects to improve ATS match.
"""

prompt_keywords = """
List missing ATS keywords compared to the job description.
"""

prompt_match = """
Give ATS match percentage with short explanation.
"""

# -------------------------------------------
# ✅ NEW PROMPT (ONLY ADDITION)
# -------------------------------------------
prompt_ats_score = """
You are an ATS (Applicant Tracking System).

1. Calculate ATS Resume Score (0–100)
2. List Matched Skills
3. List Missing Skills
4. Give short HR conclusion

Format strictly:

ATS Score: XX%

Matched Skills:
- skill1
- skill2

Missing Skills:
- skill1
- skill2

Conclusion:
Short HR feedback.
"""

# -------------------------------------------
# Execution Logic (UNCHANGED + ONE ADD)
# -------------------------------------------
if uploaded_file and job_description.strip():

    pdf_content = input_pdf_setup(uploaded_file)

    if submit1:
        response = get_gemini_response(prompt_summary, pdf_content, job_description)
        st.subheader("🧾 Resume Summary")
        st.write(response)

    elif submit2:
        response = get_gemini_response(prompt_skills, pdf_content, job_description)
        st.subheader("🛠 Skills Improvement")
        st.write(response)

    elif submit3:
        response = get_gemini_response(prompt_keywords, pdf_content, job_description)
        st.subheader("🔎 Keyword Analysis")
        st.write(response)

    elif submit4:
        response = get_gemini_response(prompt_match, pdf_content, job_description)
        st.subheader("📊 Percentage Match")
        st.write(response)

    # -------------------------------------------
    # ✅ ATS RESUME SCORE (ONLY NEW FEATURE)
    # -------------------------------------------
    elif submit5:
        response = get_gemini_response(prompt_ats_score, pdf_content, job_description)

        match = re.search(r'(\d{1,3})\s*%', response)
        score = int(match.group(1)) if match else 0

        st.subheader("🧮 ATS Resume Score")

        # Circular Score UI
        components.html(f"""
        <div style="
            width:160px;
            height:160px;
            border-radius:50%;
            background:conic-gradient(#4CAF50 {score}%, #e0e0e0 0%);
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:28px;
            font-weight:bold;
            margin-bottom:20px;">
            {score}%
        </div>
        """, height=180)

        st.markdown("### 📄 ATS Analysis")
        st.write(response)

else:
    st.warning("Upload resume and paste job description")
