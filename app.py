
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

# -------------------------------------------
# Streamlit Page Config
# -------------------------------------------
st.set_page_config(page_title="ATS Resume Screener", page_icon="🤖", layout="wide")

# -------------------------------------------
# Global CSS (Impressive UI)
# -------------------------------------------
st.markdown(
    """
    <style>
    :root{
        --bg: #0b1021;
        --card: rgba(255,255,255,0.06);
        --card-border: rgba(255,255,255,0.12);
        --text: #e8eaf6;
        --muted: #b3b8d4;
        --accent: #7c4dff;
        --accent-2: #26c6da;
        --success: #34c759;
        --warn: #ffb020;
        --danger: #ff5252;
        --shadow: 0 20px 40px rgba(0,0,0,0.45);
        --radius: 16px;
    }
    /* Page background & font */
    .stApp {
        background: radial-gradient(1200px 600px at 20% -10%, #10173a, #0b1021 40%) fixed;
        color: var(--text);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, "Noto Sans", "Apple Color Emoji","Segoe UI Emoji";
    }

    /* Header hero */
    .hero {
        margin: 8px 0 24px;
        padding: 22px 28px;
        background: linear-gradient(135deg, rgba(124,77,255,0.18), rgba(38,198,218,0.16));
        border: 1px solid var(--card-border);
        box-shadow: var(--shadow);
        border-radius: var(--radius);
        display: grid;
        grid-template-columns: auto 1fr auto;
        gap: 18px;
        align-items: center;
    }
    .hero .icon {
        width: 64px; height: 64px;
        border-radius: 18px;
        background: radial-gradient(circle at 30% 20%, #7c4dff, #26c6da 70%);
        box-shadow: 0 8px 30px rgba(124,77,255,0.45);
        display: grid; place-items: center;
        color: #fff; font-size: 28px;
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0% { transform: translateY(0px) }
        50% { transform: translateY(-6px) }
        100% { transform: translateY(0px) }
    }
    .hero h1 {
        margin: 0 0 6px; font-size: 28px; letter-spacing: 0.2px;
    }
    .hero p {
        margin: 0;
        color: var(--muted);
        font-size: 14.5px;
    }
    .badge {
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px dashed rgba(255,255,255,0.24);
        color: #fff; font-weight: 600; letter-spacing: 0.4px;
        background: linear-gradient(135deg, rgba(124,77,255,0.22), rgba(38,198,218,0.18));
    }

    /* Glass card container */
    .card {
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        padding: 18px;
    }

    /* Section titles */
    .section-title{
        font-weight: 700; font-size: 16px;
        margin-bottom: 8px;
        color: #c6c9e8;
        letter-spacing: .3px;
    }

    /* Styled stTextArea and uploader */
    textarea, .stTextInput>div>div>input {
        background: rgba(255,255,255,0.08)!important;
        color: var(--text)!important;
        border-radius: 12px!important;
        border: 1px solid rgba(255,255,255,0.18)!important;
    }
    .stFileUploader>div>div {
        background: rgba(255,255,255,0.06)!important;
        border-radius: 12px!important;
        border: 1px dashed rgba(255,255,255,0.22)!important;
        color: var(--muted)!important;
    }

    /* Button glow */
    .stButton>button {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.25);
        color: #fff;
        background: linear-gradient(135deg, #7c4dff, #26c6da);
        box-shadow: 0 12px 24px rgba(124,77,255,0.35);
        transition: transform .08s ease, box-shadow .2s ease, filter .2s ease;
    }
    .stButton>button:hover { transform: translateY(-1px); filter: brightness(1.04); }
    .stButton>button:active { transform: translateY(1px); }

    /* Divider accent */
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent); }

    /* Radial gauge */
    .gauge-wrap {
        display:flex; align-items:center; gap:16px; margin: 14px 0 4px;
    }
    .gauge {
        --size: 116px;
        width: var(--size); height: var(--size);
        border-radius: 50%;
        background:
          conic-gradient(var(--accent) calc(var(--p) * 1%), rgba(255,255,255,0.12) 0);
        display:grid; place-items:center;
        box-shadow: 0 10px 24px rgba(124,77,255,0.25);
        border: 1px solid rgba(255,255,255,0.18);
    }
    .gauge .inner {
        width: calc(var(--size) - 18px);
        height: calc(var(--size) - 18px);
        border-radius: 50%;
        background: rgba(10,14,26,0.85);
        display:grid; place-items:center;
        color:#fff; font-weight:700; font-size: 22px;
        border: 1px solid rgba(255,255,255,0.15);
    }
    .gauge-desc { color: var(--muted); font-size: 13px; }

    /* Highlight mark */
    mark.kw {
        background: linear-gradient(180deg, rgba(124,77,255,0.25), rgba(124,77,255,0.08));
        color: #fff;
        padding: 1px 3px; border-radius: 6px;
        border: 1px solid rgba(124,77,255,0.26);
    }

    /* Copy & download row */
    .action-row { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
    .action-btn {
        padding: 8px 12px; border-radius:10px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.22);
        color: #fff; cursor:pointer; font-size: 13px;
    }
    .toast {
        position: fixed; bottom: 20px; right: 20px;
        background: rgba(20,24,40,0.9);
        color: #fff; padding: 10px 14px; border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: var(--shadow); z-index: 9999;
        opacity: 0; transform: translateY(10px);
        transition: all .2s ease;
    }
    .toast.show { opacity: 1; transform: translateY(0); }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------
# Header / Hero
# -------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="icon">🤖</div>
        <div>
            <h1>ATS Resume Screener</h1>
            <p>Optimize your resume for AI-driven hiring systems — summaries, skills, keywords, and match %</p>
        </div>
        <div class="badge">Gemini 2.5 Flash • Image + Text</div>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------
# Sidebar (help & tips)
# -------------------------------------------
with st.sidebar:
    st.markdown("### Tips")
    st.write(
        "- Paste a **clear job description** with role, skills, and tools.\n"
        "- Upload your **resume in PDF**.\n"
        "- Use the 4 actions: **Summary, Skills, Keywords, Match %**."
    )
    st.caption("Your data is processed client-side for UI, analysis via Gemini API on the server.")

# -------------------------------------------
# Main Inputs
# -------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Job Description</div>', unsafe_allow_html=True)
input_text = st.text_area(
    " ",  # label hidden visually
    placeholder="Paste the Job Description here...",
    key="input",
    height=200
)

st.markdown('<div class="section-title" style="margin-top:12px;">Upload Resume (PDF format only)</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(" ", type=["pdf"])
if uploaded_file is not None:
    st.success("✅ PDF uploaded successfully!")
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------
# Buttons
# -------------------------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    submit1 = st.button("🧾 Resume Summary")
with col2:
    submit2 = st.button("🛠️ Skills Improvement")
with col3:
    submit3 = st.button("🔎 Keyword Analysis")
with col4:
    submit4 = st.button("📊 Percentage Match")

# -------------------------------------------
# Prompts (UNCHANGED content)
# -------------------------------------------
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

# -------------------------------------------
# Helper: extract percentage if present
# -------------------------------------------
def extract_percent(text: str):
    if not text:
        return None
    m = re.search(r'(\d{1,3})\s*%', text)
    if m:
        val = int(m.group(1))
        return max(0, min(val, 100))
    return None

# -------------------------------------------
# Helper: keyword list from JD (basic tokenizer)
# -------------------------------------------
def jd_keywords(jd: str):
    if not jd:
        return []
    # Simple heuristic: words >= 3 chars, allow symbols like +, # and hyphen
    tokens = re.findall(r'[A-Za-z][A-Za-z0-9+\-#]{2,}', jd)
    # Normalize & dedup
    uniq = sorted(set(t.strip() for t in tokens), key=lambda x: (-len(x), x.lower()))
    return uniq[:120]  # cap for performance

# -------------------------------------------
# Execution Logic (Core UNCHANGED)
# -------------------------------------------
response = None
active_prompt_name = None

if any([submit1, submit2, submit3, submit4]):
    if uploaded_file is not None and input_text.strip() != "":
        with st.spinner("🔍 Analyzing with AI..."):
            pdf_content = input_pdf_setup(uploaded_file)
            if submit1:
                response = get_gemini_response(prompt_summary, pdf_content, input_text)
                active_prompt_name = "Resume Summary"
            elif submit2:
                response = get_gemini_response(prompt_skills, pdf_content, input_text)
                active_prompt_name = "Skills Improvement"
            elif submit3:
                response = get_gemini_response(prompt_keywords, pdf_content, input_text)
                active_prompt_name = "Keyword Analysis"
            elif submit4:
                response = get_gemini_response(prompt_match, pdf_content, input_text)
                active_prompt_name = "Percentage Match"

            # Original section
            st.divider()
            st.subheader("AI Analysis Result:")
            st.write(response)
    else:
        st.warning("Please provide both a Job Description and a Resume PDF.")

# -------------------------------------------
# Enhanced Presentation (HTML/CSS/JS highlight)
# -------------------------------------------
if response:
    # Build keyword list from JD for highlighting
    kws = jd_keywords(input_text)
    percent = extract_percent(response)

    # Top card container
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # If percentage exists, show gauge
    if percent is not None:
        components.html(
            f"""
            <div class="gauge-wrap">
                <div class="gauge" style="--p:{percent};">
                    <div class="inner">{percent}%</div>
                </div>
                <div>
                    <div style="font-weight:700; font-size:15px;">Match Score</div>
                    <div class="gauge-desc">Estimated ATS match for this role</div>
                </div>
            </div>
            """,
            height=140,
        )

    # Action row: copy + download
    safe_text = response or ""
    st.markdown(
        """
        <div class="action-row">
            <button class="action-btn" id="copyBtn">📋 Copy</button>
            <div id="toast" class="toast">Copied to clipboard</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Copy JS
    components.html(
        f"""
        <script>
        const btn = document.getElementById('copyBtn');
        const toast = document.getElementById('toast');
        btn?.addEventListener('click', async ()=>{{
            try {{
                await navigator.clipboard.writeText({json.dumps(safe_text)});
                toast.classList.add('show');
                setTimeout(()=>toast.classList.remove('show'), 1600);
            }} catch(e) {{ console.log(e); }}
        }});
        </script>
        """,
        height=0,
    )

    # Download button in Streamlit (no logic change)
    st.download_button(
        label="⬇️ Download Analysis (TXT)",
        data=safe_text,
        file_name=f"ATS_{(active_prompt_name or 'Analysis').replace(' ', '_')}.txt",
        mime="text/plain",
        help="Save the AI analysis locally"
    )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Tabs per action (visual organization only)
    if active_prompt_name == "Resume Summary":
        tabs = st.tabs(["🧾 Summary", "🖍 Highlighted View"])
    elif active_prompt_name == "Skills Improvement":
        tabs = st.tabs(["🛠️ Recommendations", "🖍 Highlighted View"])
    elif active_prompt_name == "Keyword Analysis":
        tabs = st.tabs(["🔎 Missing Keywords", "🖍 Highlighted View"])
    elif active_prompt_name == "Percentage Match":
        tabs = st.tabs(["📊 Match Breakdown", "🖍 Highlighted View"])
    else:
        tabs = st.tabs(["Analysis", "🖍 Highlighted View"])

    # Tab 1: plain formatted (HTML preserve line breaks)
    with tabs[0]:
        st.markdown('<div class="section-title">Detailed Output</div>', unsafe_allow_html=True)
        # Keep original text; just render with <pre> for fixed-width reading
        st.markdown(
            f"<pre style='white-space:pre-wrap; background:rgba(255,255,255,0.04); padding:14px; border-radius:10px; border:1px solid rgba(255,255,255,0.18);'>{html.escape(safe_text)}</pre>",
            unsafe_allow_html=True
        )

    # Tab 2: Highlighted keywords based on JD
    with tabs[1]:
        st.markdown('<div class="section-title">Highlighted Keywords Detected from Job Description</div>', unsafe_allow_html=True)

        # Build an HTML block with text to be highlighted
        # We escape the text then replace newlines with <br/>
        html_text = html.escape(safe_text).replace("\n", "<br/>")
        kw_json = json.dumps(kws)

        components.html(
            f"""
            <div id="hl-container" style="
                background:rgba(255,255,255,0.04);
                padding:16px; border-radius:12px;
                border:1px solid rgba(255,255,255,0.18);
                color:#e8eaf6; line-height:1.55;">
                {html_text}
            </div>
            <script>
              const KW = {kw_json};
              function escapeRegExp(string) {{
                return string.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
              }}
              function highlight(container) {{
                let html = container.innerHTML;
                // Sort keywords by length desc to avoid nested highlights
                KW.sort((a,b)=>b.length - a.length).forEach(k=>{{
                  const re = new RegExp("\\\\b" + escapeRegExp(k) + "\\\\b", "gi");
                  html = html.replace(re, '<mark class="kw">$&</mark>');
                }});
                container.innerHTML = html;
              }}
              const container = document.getElementById('hl-container');
              if(container && KW.length){{
                highlight(container);
              }}
            </script>
            """,
            height=400,
            scrolling=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------
# Footer / Micro note
# -------------------------------------------
st.caption("Built with Streamlit • UI enhanced using HTML/CSS/JS • Backend logic preserved.")
