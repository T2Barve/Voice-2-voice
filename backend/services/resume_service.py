import fitz  # PyMuPDF
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import UploadFile

load_dotenv()

model = ChatGoogleGenerativeAI(model='gemini-flash-latest', temperature=0.2)

async def process_resume(file: UploadFile) -> dict:
    """
    Extracts text from a PDF resume and parses it into a rich structured schema
    using Gemini. Returns comprehensive context needed for personalized interviewing.
    """
    temp_path = f"temp_{file.filename}"
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Extract all text from all pages using PyMuPDF
        doc = fitz.open(temp_path)
        full_text = "\n".join([page.get_text() for page in doc])
        doc.close()

        if not full_text.strip():
            print("[WARN] No text extracted from PDF. Possible image-based scan.")
            raise Exception("Empty text content in PDF — may be scanned image.")

        # Truncate to safe token length (roughly 6000 chars ≈ ~1500 tokens)
        resume_text = full_text[:6000]

        prompt = f"""You are an expert technical recruiter conducting deep resume analysis.
Parse the following resume text into a comprehensive, structured JSON object.

EXTRACT ALL of the following with maximum detail:

1. "skills": Array of ALL technical skills mentioned — languages, frameworks, libraries, tools, cloud platforms, databases (max 15 most relevant).
2. "projects": Array of objects, each with:
   - "name": Project name
   - "description": What the project does (1-2 sentences)
   - "tech_stack": Array of technologies used
   - "highlights": Key achievements or metrics (e.g., "Reduced latency by 40%")
3. "work_experience": Array of objects, each with:
   - "title": Job title
   - "company": Company name
   - "duration": Duration (e.g., "Jan 2022 - Present")
   - "responsibilities": Array of 2-3 key technical responsibilities
4. "education": Object with:
   - "degree": Degree name
   - "institution": University/college name
   - "year": Graduation year or expected year
5. "experience_level": Exactly one of ["Entry-level", "Mid-level", "Senior"] — inferred from years of experience and complexity.
6. "primary_role": Primary role title (e.g., "Full Stack Engineer", "ML Engineer", "Backend Developer").
7. "certifications": Array of certification names (empty array if none).
8. "key_achievements": Array of 2-3 most impressive measurable achievements from the entire resume.

RESUME TEXT:
{resume_text}

STRICT RULES:
- Return ONLY valid JSON. No markdown, no code blocks, no preamble.
- If a field has no data in the resume, use an empty array [] or empty string "".
- Be thorough — extract every technical detail mentioned.

OUTPUT FORMAT (return this exact structure):
{{
  "skills": [],
  "projects": [],
  "work_experience": [],
  "education": {{}},
  "experience_level": "",
  "primary_role": "",
  "certifications": [],
  "key_achievements": []
}}"""

        response = model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
        
        json_str = content.strip()

        # Robust markdown block cleaning
        if "```json" in json_str:
            json_str = json_str.split("```json")[-1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_str)

        # Normalize and ensure backward-compat fields for existing workflow consumers
        # "skills" must be a flat list of strings
        raw_skills = parsed.get("skills", [])
        flat_skills = [s if isinstance(s, str) else str(s) for s in raw_skills]

        # "projects" — keep rich format but also provide flat names for backward compat
        raw_projects = parsed.get("projects", [])
        flat_project_names = []
        for p in raw_projects:
            if isinstance(p, dict):
                flat_project_names.append(p.get("name", "Unknown Project"))
            elif isinstance(p, str):
                flat_project_names.append(p)

        result = {
            # ── Backward-compatible flat fields (used by workflow state) ──
            "skills": flat_skills,
            "projects": flat_project_names,
            "experience": parsed.get("experience_level", "Entry-level"),
            "role": parsed.get("primary_role", "Software Engineer"),

            # ── Rich fields (stored in localStorage for enhanced context) ──
            "projects_detail": raw_projects,
            "work_experience": parsed.get("work_experience", []),
            "education": parsed.get("education", {}),
            "certifications": parsed.get("certifications", []),
            "key_achievements": parsed.get("key_achievements", []),
        }

        print(f"[OK] Resume parsed: {len(flat_skills)} skills, {len(flat_project_names)} projects, "
              f"{len(parsed.get('work_experience', []))} work entries")
        return result

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error in resume: {e}")
        return _fallback_resume(warning="Resume text was parsed but AI output was not valid JSON. Using generic skills.")
    except Exception as e:
        err = str(e)
        print(f"[ERROR] Resume processing error: {err}")
        if "RESOURCE_EXHAUSTED" in err or "quota" in err.lower() or "429" in err:
            return _fallback_resume(warning="Gemini API quota exceeded. Upload your resume again tomorrow or use a paid API key.")
        return _fallback_resume(warning=f"Resume parsing failed: {err[:120]}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _fallback_resume(warning: str = "") -> dict:
    """Returns a minimal fallback when resume parsing fails."""
    return {
        "skills": ["Python", "JavaScript", "React", "Node.js"],
        "projects": ["Web Application", "API Service"],
        "experience": "Entry-level",
        "role": "Software Engineer",
        "projects_detail": [],
        "work_experience": [],
        "education": {},
        "certifications": [],
        "key_achievements": [],
        "_warning": warning  # passed through to frontend so user can see what failed
    }

def analyze_resume_for_roast(resume_text: str):
    """
    Separate analysis logic for the 'Resume Roaster' feature.
    Generates ATS score, strengths, weaknesses, and a funny roast.
    """
    try:
        model = ChatGoogleGenerativeAI(model='gemini-flash-latest', temperature=0.8) # High temp for better roasts
        
        prompt = f"""You are a cynical, brutally honest, yet elite Senior Tech Recruiter from a top FAANG company.
You are reviewing a resume to either "Roast" it or give it a professional "ATS Score".

RESUME TEXT:
{resume_text}

Analyze the resume and return a JSON object with:
1. "ats_score": (0-100) Be very strict. Most resumes are 50-70.
2. "roast": (String) A funny, mean, and brutally honest roast of the resume. Point out cliches, bad formatting, or lack of impact.
3. "strengths": (Array) 2-3 genuine technical strengths.
4. "weaknesses": (Array) 2-3 critical areas for improvement.
5. "ats_optimization_tips": (Array) 3-4 specific keywords or formatting tips to beat the ATS.

OUTPUT FORMAT:
{{
  "ats_score": 0,
  "roast": "",
  "strengths": [],
  "weaknesses": [],
  "ats_optimization_tips": []
}}"""

        response = model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
        
        json_str = content.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[-1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        return json.loads(json_str)
    except Exception as e:
        print(f"Roast failed: {e}")
        return {
            "ats_score": 45,
            "roast": "Your resume is so bad the AI couldn't even finish reading it. Try again when you have more than 2 lines of code.",
            "strengths": ["Reading"],
            "weaknesses": ["Everything else"],
            "ats_optimization_tips": ["Use a standard font", "Add more keywords"]
        }
