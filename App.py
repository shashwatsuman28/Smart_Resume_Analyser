# smart_resume_analyser_final.py
import io
import re
import streamlit as st
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import PyPDF2

# ----------------------------
# Helper Functions (Backend)
# ----------------------------

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)
        return "\n".join(pages_text).strip()
    except Exception:
        return ""

def extract_name(text: str) -> str:
    if not text:
        return "Not found"
    blacklist = {
        "RESUME", "CURRICULUM VITAE", "CV", "CONTACT", "SUMMARY", "OBJECTIVE",
        "EXPERIENCE", "EDUCATION", "SKILLS", "PROJECTS", "WORK", "PROFILE"
    }
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:8]:
        up = line.upper()
        if up in blacklist:
            continue
        if "@" in line or any(ch.isdigit() for ch in line):
            continue
        words = line.split()
        if 1 <= len(words) <= 4:
            if any(w[0].isupper() for w in words if w):
                return line
    return "Not found"

def extract_email(text: str) -> str:
    if not text:
        return "Not found"
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    m = re.search(email_pattern, text, flags=re.IGNORECASE)
    return m.group(0) if m else "Not found"

def extract_phone(text: str) -> str:
    if not text:
        return "Not found"
    patterns = [
        r'(?<!\d)\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}(?!\d)',
        r'(?<!\d)\d{10}(?!\d)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0).strip()
    return "Not found"

def extract_skills(text: str):
    if not text:
        return []
    skill_keywords = [
        "Python", "Java", "C++", "C", "JavaScript", "HTML", "CSS", "React",
        "Node.js", "Node", "SQL", "MongoDB", "PostgreSQL", "MySQL", "R", "Scala",
        "AI", "ML", "Machine Learning", "Artificial Intelligence", "Data Science",
        "Data Analysis", "Big Data", "Deep Learning", "Neural Networks",
        "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
        "Excel", "PowerBI", "Tableau", "Git", "Docker", "Kubernetes",
        "AWS", "Azure", "GCP", "Linux", "Windows", "MacOS"
    ]
    found = set()
    up = text.upper()
    for sk in skill_keywords:
        if sk.upper() in up:
            found.add(sk)
    return sorted(found)

# ----------------------------
# Improved ATS Scoring
# ----------------------------

def calculate_ats_score(skills, text, jd_text=""):
    if not text:
        return 0

    score = 20  # base score for just having a resume

    # ---- Skill Matching ----
    jd_text_upper = jd_text.upper() if jd_text else ""
    matched_skills = [s for s in skills if jd_text_upper and s.upper() in jd_text_upper]

    if jd_text:  # If JD provided, weigh more on overlap
        skill_match_score = min(len(matched_skills) * 8, 50)
    else:  # If no JD, fallback to generic skill count
        skill_match_score = min(len(skills) * 5, 40)

    score += skill_match_score

    # ---- Section Presence ----
    section_keywords = ["experience", "education", "project", "certification"]
    section_score = sum(5 for kw in section_keywords if kw in text.lower())
    score += section_score

    # ---- Penalties for Missing Sections ----
    if "experience" not in text.lower():
        score -= 5
    if "education" not in text.lower():
        score -= 5

    # ---- Coverage Bonus ----
    if jd_text and skills:
        coverage = int((len(matched_skills) / max(1, len(set(jd_text.split())))) * 30)
        score += coverage

    # Final clamp
    return max(0, min(score, 100))

def improvement_suggestions(skills, all_skills, ats_score, jd_text=""):
    suggestions = []
    if ats_score < 60:
        suggestions.append("🔴 ATS score is below average. Add more relevant skills & keywords.")
    elif ats_score < 75:
        suggestions.append("🟡 ATS score is good but can be improved with more technical skills.")
    else:
        suggestions.append("🟢 Great ATS score! Resume is fairly optimized.")

    if jd_text:
        suggestions.append("📌 Tailor your resume to better match the job description provided.")

    missing = [s for s in all_skills if s not in skills]
    if missing:
        suggestions.append(f"💡 Consider adding: {', '.join(missing[:4])}")
    if len(skills) < 5:
        suggestions.append("📈 Add more technical skills to increase marketability.")

    suggestions.append("✨ Use action verbs and quantify achievements.")
    return suggestions

# ----------------------------
# Streamlit UI (Frontend)
# ----------------------------

st.set_page_config(page_title="Smart Resume Analyser", layout="wide", initial_sidebar_state="auto")

st.markdown("""
<style>
.app-title { text-align:center; color:#2E86AB; font-size:28px; margin-bottom:8px; }
.upload-box { background:#f7fbfe; padding:12px; border-radius:8px; margin: 10px auto; max-width:680px; border:1px dashed #bcdff8; text-align:center; }
.small-muted { color:#666; font-size:14px; }
.section-header { font-size:20px; font-weight:bold; color:#2E86AB; margin-top:16px; margin-bottom:6px; border-bottom:1px solid #e0e0e0; padding-bottom:4px; }
.info-line { margin:4px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-title">📄 Smart Resume Analyser — Final</div>', unsafe_allow_html=True)
st.markdown('<div class="small-muted" style="text-align:center;margin-bottom:12px;">Upload a text-based PDF (not a scanned image) for best results.</div>', unsafe_allow_html=True)

# Job description input
st.markdown("### 📑 Job Description (Optional)")
jd_text = st.text_area("Paste the job description here to improve ATS relevance scoring", height=150)

st.markdown('<div class="upload-box">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    uploaded_bytes = uploaded_file.read()
    extracted_text = extract_text_from_pdf_bytes(uploaded_bytes)

    with st.expander("🔎 Raw extracted text (first 3000 chars)"):
        if extracted_text:
            st.text_area("Preview", value=extracted_text[:3000], height=250)
        else:
            st.write("No selectable text found. Your PDF might be scanned.")

    name = extract_name(extracted_text)
    email = extract_email(extracted_text)
    phone = extract_phone(extracted_text)
    skills = extract_skills(extracted_text)

    st.markdown("### 📌 Extracted Information")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="section-header">👤 Personal Details</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">📝 <b>Name:</b> {name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">📧 <b>Email:</b> {email}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">📱 <b>Phone:</b> {phone}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="section-header">🛠️ Skills Detected</div>', unsafe_allow_html=True)
        if skills:
            st.markdown(f'<div class="info-line">{" | ".join(skills)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-line">No skills detected</div>', unsafe_allow_html=True)

    # ATS score with JD support
    ats_score = calculate_ats_score(skills, extracted_text, jd_text)

    st.markdown("### 📊 ATS Score & Summary")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.metric(label="ATS Score", value=f"{ats_score}")
        st.metric(label="Skills found", value=len(skills))
    with col2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=ats_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "ATS Compatibility Score"},
            delta={'reference': 75},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': 'lightgray'},
                    {'range': [50, 75], 'color': 'yellow'},
                    {'range': [75, 100], 'color': 'lightgreen'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max(ats_score, 85)
                }
            }
        ))
        fig.update_layout(height=260)
        st.plotly_chart(fig, use_container_width=True)
    with col3:
        if ats_score >= 80:
            st.success("Excellent!")
        elif ats_score >= 60:
            st.info("Good")
        else:
            st.error("Needs Work")

    st.markdown("### ☁️ Skills WordCloud")
    if skills:
        wc = WordCloud(width=800, height=400, background_color="white", max_words=100).generate(" ".join(skills))
        fig_wc, ax = plt.subplots(figsize=(9, 4.5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig_wc)
        plt.close(fig_wc)
    else:
        st.info("No skills to build a wordcloud.")

    st.markdown("### 💡 Suggested Improvements")
    all_skills = [
        "Python", "Java", "C++", "C", "R", "JavaScript", "HTML", "CSS",
        "AI", "ML", "Data Science", "Machine Learning", "Deep Learning",
        "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch",
        "SQL", "MongoDB", "PostgreSQL", "Git", "Docker", "AWS", "Azure"
    ]
    suggestions = improvement_suggestions(skills, all_skills, ats_score, jd_text)
    for i, s in enumerate(suggestions, 1):
        st.write(f"{i}. {s}")

    # Simple demo job DB (unchanged)
    job_database = {
        "Python": ["Python Developer at Infosys", "Data Scientist at TCS"],
        "SQL": ["Data Engineer at Snowflake", "DB Admin at Oracle"],
        "JavaScript": ["Frontend Dev at Zomato", "Full Stack at Paytm"],
        "AI": ["AI Engineer at Google", "ML Engineer at OpenAI"]
    }
    matched_jobs = set()
    for sk in skills:
        if sk in job_database:
            matched_jobs.update(job_database[sk])
    if matched_jobs:
        st.markdown("### 💼 Sample Job Matches")
        for job in list(matched_jobs)[:6]:
            st.write("- " + job)
    else:
        st.info("No direct job matches found for detected skills (demo DB).")
else:
    st.info("Upload a PDF resume and I'll extract details, score ATS, and suggest improvements.")
