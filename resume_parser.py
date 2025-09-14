import re
import fitz  # PyMuPDF for clean PDF reading

# ---------- PDF TEXT EXTRACTION ----------
def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text("text")
    return text


# ---------- CLEAN EXTRACTIONS ----------
def clean_name(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        return re.sub(r'[^\x00-\x7F]+', '', lines[0])  # remove weird chars
    return "Not Found"

def extract_email(text):
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else "Not Found"

def extract_phone(text):
    match = re.search(r"(\+?\d{1,3})?[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}", text)
    return match.group(0) if match else "Not Found"


# ---------- SKILL EXTRACTION ----------
# Extend keyword sets
ds_keywords = [
    "machine learning", "deep learning", "tensorflow", "keras", "pytorch",
    "scikit-learn", "data science", "pandas", "numpy", "statistics", "sql"
]

web_keywords = [
    "html", "css", "javascript", "react", "angular", "vue", "django",
    "flask", "php", "laravel", "wordpress", "node.js"
]

android_keywords = ["android", "kotlin", "java", "xml", "flutter"]
ios_keywords = ["ios", "swift", "xcode", "objective-c"]
uiux_keywords = [
    "ui", "ux", "figma", "adobe xd", "sketch", "photoshop", "illustrator",
    "zeplin", "wireframe", "prototyping", "user research", "interaction design"
]

all_keywords = ds_keywords + web_keywords + android_keywords + ios_keywords + uiux_keywords

def extract_skills(text):
    skills = []
    for skill in all_keywords:
        if skill.lower() in text.lower():
            skills.append(skill)
    return list(set(skills)) if skills else ["Not Found"]


# ---------- EDUCATION & EXPERIENCE ----------
def extract_education(text):
    education_keywords = ["b.sc", "m.sc", "b.tech", "m.tech", "mba", "bachelor", "master", "phd", "degree"]
    for line in text.lower().split("\n"):
        for word in education_keywords:
            if word in line:
                return line.strip()
    return "Not Found"

def extract_experience(text):
    exp_match = re.findall(r"(\d+)\+?\s*(years|yrs|year)", text.lower())
    if exp_match:
        return [f"{num} {unit}" for num, unit in exp_match]
    return ["Not Found"]


# ---------- MAIN FUNCTION ----------
def parse_resume(file_path):
    try:
        text = extract_text_from_pdf(file_path)

        data = {
            "name": clean_name(text),
            "email": extract_email(text),
            "mobile_number": extract_phone(text),
            "skills": extract_skills(text),
            "education": extract_education(text),
            "experience": extract_experience(text),
            "no_of_pages": len(fitz.open(file_path))
        }
        return data
    except Exception as e:
        print("Error parsing resume:", e)
        return None
