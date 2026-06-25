import os
import json
import re
import google.generativeai as genai


def _get_model():
    """Configure and return Gemini Flash model."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it in the sidebar.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash-lite")
    # return genai.GenerativeModel("gemini-1.5-flash")


def _safe_json(text: str) -> list:
    """Strip markdown fences and parse JSON safely."""
    text = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        result = json.loads(text)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


# ── 1. Extract Skills from Resume ────────────────────────────────────────
def extract_skills_from_resume(resume_text: str) -> list[str]:
    """
    Ask Gemini to extract all technical + soft skills from resume text.
    Returns a list of skill strings.
    """
    prompt = f"""
You are an expert resume parser.

Extract ALL skills from the resume below — include:
- Programming languages (Python, Java, SQL, etc.)
- Frameworks and libraries (React, TensorFlow, Spring, etc.)
- Tools and platforms (Git, Docker, AWS, etc.)
- Soft skills (Leadership, Communication, Problem-solving, etc.)
- Concepts (Machine Learning, Agile, REST APIs, etc.)

Return ONLY a valid JSON array of strings. No explanation, no markdown.
Example: ["Python", "Machine Learning", "Leadership", "REST APIs"]

Resume:
{resume_text[:4000]}
"""
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        skills = _safe_json(response.text)
        # Fallback: split by comma if JSON parse fails
        if not skills and response.text:
            skills = [s.strip().strip('"') for s in response.text.split(",") if s.strip()]
        return skills
    except Exception as e:
        return [f"Error: {str(e)}"]


# ── 2. Extract Keywords from Job Description ──────────────────────────────
def extract_keywords_from_jd(jd_text: str) -> list[str]:
    """
    Ask Gemini to extract required skills/keywords from a job description.
    Returns a list of keyword strings.
    """
    prompt = f"""
You are an ATS (Applicant Tracking System) expert.

Extract all required skills, technologies, and qualifications from this job description.
Include: programming languages, frameworks, tools, certifications, domain knowledge.
Exclude: company descriptions, benefits, salary info.

Return ONLY a valid JSON array of strings. No explanation, no markdown.
Example: ["Python", "AWS", "3+ years experience", "REST APIs", "Agile"]

Job Description:
{jd_text[:4000]}
"""
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        keywords = _safe_json(response.text)
        if not keywords and response.text:
            keywords = [s.strip().strip('"') for s in response.text.split(",") if s.strip()]
        return keywords
    except Exception as e:
        return [f"Error: {str(e)}"]


# ── 3. Skill Gap Analysis ─────────────────────────────────────────────────
def get_skill_gap_analysis(missing_skills: list[str], job_context: str) -> list[dict]:
    """
    For each missing skill, get a learning resource and priority level.
    Returns list of dicts: {skill, resource_name, url, priority}
    """
    if not missing_skills:
        return []
    skills_str = ", ".join(list(missing_skills)[:15])
    # skills_str = ", ".join(missing_skills[:15])  # limit to top 15

    prompt = f"""
You are a career coach helping a software engineering student in India prepare for placements.

For each missing skill below, suggest ONE free online learning resource.
Consider resources available in India (prefer free: YouTube, Coursera free tier, official docs, GeeksForGeeks, etc.)

Rate priority as "High", "Medium", or "Low" based on how critical it is for the job context.

Return ONLY a valid JSON array. No explanation, no markdown.
Format exactly like this:
[
  {{
    "skill": "Docker",
    "resource_name": "Docker Official Getting Started Guide",
    "url": "https://docs.docker.com/get-started/",
    "priority": "High"
  }}
]

Missing skills: {skills_str}
Job context: {job_context}
"""
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        gaps = _safe_json(response.text)
        return gaps if gaps else []
    except Exception as e:
        return [{"skill": f"Error: {str(e)}", "resource_name": "", "url": "#", "priority": "High"}]


# ── 4. Improve Resume Bullet Points ──────────────────────────────────────
def improve_resume_bullets(bullets: str) -> str:
    """
    Rewrite weak resume bullet points to be stronger and ATS-friendly.
    Returns improved bullet points as a plain string.
    """
    prompt = f"""
You are an expert resume writer helping a software engineering student.

Rewrite these weak resume bullet points to be:
1. Action-verb first (Built, Developed, Optimized, Implemented, etc.)
2. Quantified where possible (add realistic numbers/percentages for a student project)
3. ATS-friendly (include relevant tech keywords)
4. Concise (one line each)

Return ONLY the improved bullet points, one per line starting with •
No explanation needed.

Original bullets:
{bullets}
"""
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error improving bullets: {str(e)}"
