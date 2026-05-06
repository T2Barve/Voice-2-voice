from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from pathlib import Path
import sqlite3
import json
import re
import requests
import datetime

model = ChatGoogleGenerativeAI(model='gemini-flash-latest', temperature=0.7)

_DB_PATH = Path(__file__).resolve().parent.parent / 'case_study_checkpoints.db'
conn = sqlite3.connect(database=str(_DB_PATH), check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# ─────────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────────

class CaseStudyState(TypedDict):
    session_id: str
    user_id: str
    role: str
    company: str
    interview_type: str

    resume_data: dict
    question_index: int
    questions_asked: list

    resume_questions: list
    answers: list
    scores: list

    interview_question: str
    user_answer: str
    final_response: str
    interview_status: str
    report: str

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _parse_json_list(raw: str) -> list:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[-1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    return json.loads(raw)


def _extract_project_keywords(resume_data: dict) -> list:
    """Extract rich project/tech keywords from resume for targeted RAG queries."""
    keywords = []
    for p in resume_data.get("projects_detail", []):
        if isinstance(p, dict):
            keywords.extend(p.get("tech_stack", [])[:3])
            if p.get("name"):
                keywords.append(p["name"])
    for w in resume_data.get("work_experience", []):
        if isinstance(w, dict) and w.get("company"):
            keywords.append(w["company"])
    seen = set()
    result = []
    for k in keywords:
        if k and k.lower() not in seen:
            seen.add(k.lower())
            result.append(k)
    return result[:6]


def _fetch_rag_question(company: str, role: str, skills: list,
                        project_keywords: list, asked: list) -> str:
    """Fetch ONE case study question from RAG using full resume context."""
    from backend.rag.retriever import retrieve_questions

    context = retrieve_questions(
        company, "case_study", "medium", role,
        skills=skills, project_keywords=project_keywords, k=6
    )

    if asked:
        avoid_lines = "\n".join(f"  - {q[:120].strip()}" for q in asked[-6:])
        avoid_section = f"""CRITICAL — Do NOT repeat any of these already-asked questions:
{avoid_lines}
Pick a COMPLETELY DIFFERENT topic."""
    else:
        avoid_section = "This is the first question — pick the most relevant system design scenario."

    prompt = f"""You are a FAANG system design interviewer for {company} hiring for {role}.
Candidate Skills: {', '.join(skills[:8]) if skills else 'General'}
Project Context: {', '.join(project_keywords[:4]) if project_keywords else 'N/A'}

{avoid_section}

Knowledge Base (use ONLY content from here):
{context}

Pick ONE unique case study or system design question that:
- Is DIFFERENT from all already-asked questions
- Is specific to {company}'s domain and engineering scale
- Explores meaningful architectural trade-offs
- Connects to the candidate's skill set where possible

Return ONLY the question text. No JSON, no numbering, no extra formatting."""

    response = model.invoke(prompt)
    content = response.content
    if isinstance(content, list):
        content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
    return content.strip()


def _generate_resume_questions(resume_data: dict) -> list:
    """Generate 3 deep case study / project deep-dive questions from full resume context."""
    skills          = resume_data.get("skills", [])
    projects        = resume_data.get("projects", [])
    projects_detail = resume_data.get("projects_detail", [])
    work_experience = resume_data.get("work_experience", [])
    key_achievements = resume_data.get("key_achievements", [])

    # Build rich project context
    project_context = ""
    selected_project = "your most significant project"
    if projects_detail:
        p = projects_detail[0]
        if isinstance(p, dict):
            selected_project = p.get("name", projects[0] if projects else "your project")
            project_context = (
                f"Project: {selected_project}\n"
                f"Description: {p.get('description', 'N/A')}\n"
                f"Tech Stack: {', '.join(p.get('tech_stack', []))}\n"
                f"Highlights: {', '.join(p.get('highlights', []))}"
            )
    elif projects:
        selected_project = projects[0]
        project_context = f"Project: {selected_project}"

    experience_context = ""
    if work_experience:
        w = work_experience[0]
        if isinstance(w, dict):
            experience_context = f"{w.get('title', '')} at {w.get('company', '')} — {', '.join(w.get('responsibilities', [])[:2])}"

    prompt = f"""You are a FAANG system design and case study interviewer.
Generate EXACTLY 3 deep, personalized case study questions based on this candidate's resume.

CANDIDATE PROFILE:
Skills: {', '.join(skills[:10])}
{project_context}
Work Context: {experience_context if experience_context else 'Not specified'}
Achievements: {', '.join(key_achievements[:2]) if key_achievements else 'Not specified'}

QUESTION REQUIREMENTS:
- Q1: Deep-dive project overview — ask them to walk through the architecture, key decisions, and their personal contributions to {selected_project}.
- Q2: Scalability challenge — how would they scale {selected_project} or their current system to handle 100x load? What breaks first?
- Q3: Real-world trade-off — based on their tech stack, ask about a specific design decision (e.g., SQL vs NoSQL, monolith vs microservices, caching strategy).

RULES:
- Questions must be specific to THIS candidate's background
- Focus on architectural thinking, trade-offs, and real-world constraints
- Return ONLY a valid JSON array of 3 strings"""

    try:
        res = model.invoke(prompt).content.strip()
        qs = _parse_json_list(res)
        return [q for q in qs if isinstance(q, str)][:3]
    except Exception as e:
        print(f"Case Study Resume Q Gen Error: {e}")
        return [
            f"Walk me through the complete architecture of **{selected_project}** — what it does, the core components, and the most significant technical decision you made.",
            f"If {selected_project} suddenly needed to handle 100x more traffic, what would break first and how would you redesign it?",
            f"Describe a specific trade-off you made in {selected_project} — what did you choose and why? What did you sacrifice?"
        ]

# ─────────────────────────────────────────────────────────────────
# NODES
# ─────────────────────────────────────────────────────────────────

def initialize_session(state: CaseStudyState):
    """Fast init: pre-generate 3 resume questions only. RAG fetched on-demand."""
    resume_data = state.get('resume_data', {})
    company     = state.get('company', 'Google')
    role        = state.get('role', 'SDE')

    print(f"--- Initializing Case Study Interview: {role} @ {company} ---")
    resume_qs = _generate_resume_questions(resume_data)

    return {
        'question_index':   0,
        'resume_questions': resume_qs,
        'questions_asked':  [],
        'answers':          [],
        'scores':           [],
        'interview_status': 'ongoing',
        'final_response':   '',
    }


def generate_question(state: CaseStudyState):
    """
    Alternating controller:
      Even index (0, 2, 4) → Resume/project deep-dive question
      Odd  index (1, 3, 5) → RAG company/domain question
    """
    idx         = state.get('question_index', 0)
    resume_data = state.get('resume_data', {})
    skills      = resume_data.get('skills', [])
    company     = state.get('company', 'Google')
    role        = state.get('role', 'SDE')
    asked       = state.get('questions_asked', [])
    project_kws = _extract_project_keywords(resume_data)

    if idx % 2 == 0:
        source    = "RESUME"
        resume_qs = state.get('resume_questions', [])
        q_idx     = idx // 2
        if q_idx < len(resume_qs):
            question = resume_qs[q_idx]
        else:
            question = _fetch_rag_question(company, role, skills, project_kws, asked)
            source   = "RAG (FALLBACK)"
    else:
        source   = "RAG"
        question = _fetch_rag_question(company, role, skills, project_kws, asked)

    print(f"\n[Case Study Q{idx + 1}] Source: {source}")

    return {
        'interview_question': question,
        'questions_asked':    asked + [question],
        'question_index':     idx + 1,
        'final_response':     '',
    }


def ask_human(state: CaseStudyState):
    """Interrupt point — waits for user's answer."""
    return state


def evaluate_answer(state: CaseStudyState):
    """Score and give dynamic feedback on the candidate's case study answer."""
    q   = state.get('interview_question', '')
    ans = state.get('user_answer', '')
    resume_data = state.get('resume_data', {})
    skills = resume_data.get('skills', [])

    prompt = f"""You are a FAANG system design interviewer evaluating a case study response.

Question: {q}
Candidate's Answer: {ans}
Candidate's Tech Stack: {', '.join(skills[:6]) if skills else 'Not specified'}

Evaluate based on FAANG system design standards:
1. Did they identify the right requirements and constraints?
2. Did they propose a reasonable architecture with clear components?
3. Did they discuss trade-offs (consistency vs availability, SQL vs NoSQL, etc.)?
4. Did they address scalability and reliability concerns?
5. Was the answer structured and communicated clearly?

Provide:
- 2-3 sentences of direct, specific feedback referencing their actual answer
- ONE concrete thing they did well
- ONE specific gap with a suggestion to improve it

End with exactly: SCORE: [number 1-10]"""

    try:
        res   = model.invoke(prompt).content.strip()
        match = re.search(r"SCORE:\s*(\d+)", res)
        score = int(match.group(1)) if match else 5
        score = max(1, min(10, score))
        feedback = res.split("SCORE:")[0].strip()
    except Exception as e:
        print(f"Case Study evaluate error: {e}")
        score    = 5
        feedback = "Good attempt. Try to be more explicit about trade-offs and quantify expected scale."

    return {
        'scores':         state.get('scores', []) + [score],
        'answers':        state.get('answers', []) + [ans],
        'final_response': feedback,
    }


def should_end(state: CaseStudyState) -> Literal["generate_question", "generate_report"]:
    """End after 6 questions (3 resume + 3 RAG)."""
    if state.get('question_index', 0) >= 6:
        return "generate_report"
    return "generate_question"


def generate_report(state: CaseStudyState):
    """Generate fully dynamic AI report and save to MongoDB."""
    scores      = state.get('scores', [])
    answers     = state.get('answers', [])
    questions   = state.get('questions_asked', [])
    resume_data = state.get('resume_data', {})

    total_score   = sum(scores) / max(1, len(scores))
    resume_scores = [scores[i] for i in range(len(scores)) if i % 2 == 0]
    rag_scores    = [scores[i] for i in range(len(scores)) if i % 2 != 0]
    avg_resume    = sum(resume_scores) / max(1, len(resume_scores))
    avg_rag       = sum(rag_scores)    / max(1, len(rag_scores))

    session_id = state.get('session_id', 'sess_cs_' + str(int(datetime.datetime.now().timestamp())))
    user_id    = state.get('user_id', 'user_default')

    # Build Q&A summary for dynamic feedback generation
    qa_summary = ""
    for i, (q, a, s) in enumerate(zip(questions, answers, scores)):
        source = "resume/project" if i % 2 == 0 else "company/domain"
        qa_summary += f"\nQ{i+1} [{source}] (Score {s}/10): {q[:100]}...\nA: {a[:150]}...\n"

    prompt = f"""You are an expert FAANG system design interviewer writing a final case study evaluation.

Candidate: {state.get('role', 'SDE')} applying to {state.get('company', 'Unknown')}
Skills: {', '.join(resume_data.get('skills', [])[:8])}
Average Score: {total_score:.1f}/10
Project Deep-dive avg: {avg_resume:.1f}/10
System Design avg: {avg_rag:.1f}/10

Interview Summary:
{qa_summary}

Write a SPECIFIC, non-generic evaluation referencing their actual answers.
Return ONLY a valid JSON object:
- "closing_message": 1-2 sentence warm closing mentioning their score and specific strength.
- "strengths": 2-3 sentences citing SPECIFIC things they demonstrated in their answers.
- "weakness": 2-3 sentences with SPECIFIC gaps and concrete improvement advice.
- "hire_recommendation": One of ["Strong Hire", "Hire", "No Hire", "Strong No Hire"]

Return ONLY valid JSON. No markdown."""

    try:
        response = model.invoke(prompt).content.strip()
        if "```json" in response:
            response = response.split("```json")[-1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        feedback  = json.loads(response)
        message   = feedback.get("closing_message", f"Case Study complete! Score: {total_score:.1f}/10.")
        strengths = feedback.get("strengths", "Good architectural thinking demonstrated.")
        weaknesses= feedback.get("weakness", "Work on quantifying trade-offs and constraints.")
        hire_rec  = feedback.get("hire_recommendation", "Hire")
    except Exception as e:
        print(f"Case Study report gen error: {e}")
        message    = f"Case Study interview complete! Average score: {total_score:.1f}/10."
        strengths  = "Demonstrated solid understanding of system components."
        weaknesses = "Practice discussing scalability trade-offs with concrete metrics."
        hire_rec   = "Hire" if total_score >= 6 else "No Hire"

    final_report = {
        "session_id":     session_id,
        "user_id":        user_id,
        "role":           state.get('role', 'SDE'),
        "company":        state.get('company', 'Unknown'),
        "interview_type": "case_study",         # ✅ correct field name
        "score":          round(total_score, 1), # ✅ correct field name
        "breakdown": {
            "resume_based":  round(avg_resume, 1),
            "company_based": round(avg_rag, 1)
        },
        "questions": [
            {
                "question": questions[i] if i < len(questions) else "",
                "source":   "resume" if i % 2 == 0 else "rag",
                "answer":   answers[i]  if i < len(answers)  else "Not provided",
                "score":    scores[i]   if i < len(scores)   else 0,
                "feedback": {"strengths": [strengths], "weaknesses": [weaknesses]}
            }
            for i in range(len(questions))
        ],
        "strengths":  [strengths],
        "weaknesses": [weaknesses],
        "resume_summary": {
            "skills":     resume_data.get("skills", []),
            "projects":   resume_data.get("projects", []),
            "experience": resume_data.get("experience", "Not specified")
        },
        "metadata": {
            "total_questions":  len(questions),
            "duration_seconds": 0,
            "difficulty_level": "medium",
            "started_at":       datetime.datetime.now().isoformat(),
            "completed_at":     datetime.datetime.now().isoformat()
        }
    }

    try:
        headers = {"x-internal-secret": "interview_ai_internal_secret_2026"}
        res = requests.post(
            "http://localhost:5000/api/report/save",
            json=final_report, headers=headers, timeout=10
        )
        if res.ok:
            print(f"[OK] Case Study report saved. Score: {total_score:.1f}/10 | Rec: {hire_rec}")
        else:
            print(f"[ERROR] Express error: {res.status_code} - {res.text[:200]}")
    except Exception as e:
        print(f"[ERROR] Report save failed: {e}")

    return {
        'report':           message,
        'final_response':   f"{message}\n\n**Hire Recommendation:** {hire_rec}",
        'strengths':        strengths,
        'weakness':         weaknesses,
        'interview_status': 'ended'
    }

# ─────────────────────────────────────────────────────────────────
# GRAPH
# ─────────────────────────────────────────────────────────────────

builder = StateGraph(CaseStudyState)

builder.add_node("initialize_session", initialize_session)
builder.add_node("generate_question",  generate_question)
builder.add_node("ask_human",          ask_human)
builder.add_node("evaluate_answer",    evaluate_answer)
builder.add_node("generate_report",    generate_report)

builder.add_edge(START,                "initialize_session")
builder.add_edge("initialize_session", "generate_question")
builder.add_edge("generate_question",  "ask_human")
builder.add_edge("ask_human",          "evaluate_answer")
builder.add_conditional_edges("evaluate_answer", should_end)
builder.add_edge("generate_report",    END)

workflow = builder.compile(checkpointer=checkpointer, interrupt_before=["ask_human"])

print("[OK] Case Study workflow compiled (rich resume + RAG, dynamic reports).")
