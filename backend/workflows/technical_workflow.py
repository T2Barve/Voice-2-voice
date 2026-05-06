from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import json
import re
import requests
import datetime
from pathlib import Path

load_dotenv()

model = ChatGoogleGenerativeAI(model='gemini-flash-latest', temperature=0.7)

_DB_PATH = Path(__file__).resolve().parent.parent / 'technical_checkpoints.db'
conn = sqlite3.connect(database=str(_DB_PATH), check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# ─────────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────────

class InterviewState(TypedDict):
    session_id: str
    user_id: str
    role: str
    company: str
    interview_type: str

    resume_data: dict           # {skills, projects, projects_detail, work_experience, ...}
    question_index: int
    questions_asked: list

    resume_questions: list      # Pre-generated from resume (3 questions)
    answers: list
    scores: list

    interview_question: str
    user_answer: str
    final_response: str
    interview_status: str
    difficulty: str

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _parse_json_list(raw: str) -> list:
    """Safely parse a JSON list from model output, stripping markdown."""
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[-1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    return json.loads(raw)


def _extract_project_keywords(resume_data: dict) -> list:
    """Extract rich project keywords from resume_data for RAG query enrichment."""
    keywords = []

    # From detailed projects (rich format from new resume parser)
    for p in resume_data.get("projects_detail", []):
        if isinstance(p, dict):
            keywords.extend(p.get("tech_stack", [])[:3])
            name = p.get("name", "")
            if name:
                keywords.append(name)

    # From work experience
    for w in resume_data.get("work_experience", []):
        if isinstance(w, dict):
            for r in w.get("responsibilities", [])[:1]:
                # Extract first 3 words as keyword hints
                words = r.split()[:3]
                keywords.append(" ".join(words))

    # Deduplicate and limit
    seen = set()
    result = []
    for k in keywords:
        if k and k.lower() not in seen:
            seen.add(k.lower())
            result.append(k)

    return result[:6]


def _fetch_rag_question(company: str, role: str, difficulty: str, skills: list,
                        project_keywords: list, asked: list) -> str:
    """Fetch ONE question from RAG on-demand using full resume context. Never repeat."""
    from backend.rag.retriever import retrieve_questions

    context = retrieve_questions(
        company, "technical", difficulty, role,
        skills=skills, project_keywords=project_keywords, k=6
    )

    if asked:
        avoid_lines = "\n".join(f"  - {q[:120].strip()}" for q in asked[-6:])
        avoid_section = f"""CRITICAL — Do NOT ask any of these already-asked questions:
{avoid_lines}

You MUST pick a COMPLETELY DIFFERENT question on a different topic."""
    else:
        avoid_section = "This is the first RAG question — pick the most relevant one."

    prompt = f"""You are a FAANG interviewer for {company} hiring for {role}.
Candidate Skills: {', '.join(skills[:8]) if skills else 'General'}
Project Keywords: {', '.join(project_keywords[:4]) if project_keywords else 'N/A'}

{avoid_section}

Knowledge Base (use ONLY content from here, no hallucination):
{context}

Pick ONE unique technical interview question from the Knowledge Base that:
- Is DIFFERENT from all already-asked questions
- Is highly relevant to the candidate's skills and projects
- Tests deep technical understanding, trade-offs, or system internals

Return ONLY the question text. No JSON, no quotes, no numbering, no extra formatting."""

    return model.invoke(prompt).content.strip()


def _generate_resume_questions(resume_data: dict) -> list:
    """Generate 3 deep technical questions based on the full resume context."""
    skills = resume_data.get("skills", [])
    projects = resume_data.get("projects", [])
    projects_detail = resume_data.get("projects_detail", [])
    work_experience = resume_data.get("work_experience", [])
    key_achievements = resume_data.get("key_achievements", [])

    # Build rich context for the prompt
    project_context = ""
    if projects_detail:
        for p in projects_detail[:3]:
            if isinstance(p, dict):
                project_context += f"\n- {p.get('name', 'Project')}: {p.get('description', '')} | Stack: {', '.join(p.get('tech_stack', []))}"
    elif projects:
        project_context = "\n- " + "\n- ".join(projects[:3])

    experience_context = ""
    if work_experience:
        for w in work_experience[:2]:
            if isinstance(w, dict):
                experience_context += f"\n- {w.get('title', '')} at {w.get('company', '')} ({w.get('duration', '')})"

    achievements_context = ""
    if key_achievements:
        achievements_context = "\n".join(f"- {a}" for a in key_achievements[:3])

    prompt = f"""You are an elite FAANG technical interviewer.
Generate EXACTLY 3 deep, personalized technical interview questions based on this candidate's specific resume.

CANDIDATE PROFILE:
Skills: {', '.join(skills[:10])}
Projects:{project_context}
Work Experience:{experience_context if experience_context else ' Not specified'}
Key Achievements:{achievements_context if achievements_context else ' Not specified'}

QUESTION REQUIREMENTS:
- Q1: Deep-dive into their most complex project — ask about a specific technical decision, architecture choice, or challenge.
- Q2: Test internals of a skill they listed — ask about implementation details, trade-offs, or edge cases.
- Q3: Ask about a real-world scenario related to their work experience or achievements.

RULES:
- No generic questions (avoid "what is X?", "explain Y")
- Each question must be specific to THIS candidate's background
- Test depth of understanding, not just surface knowledge
- Return ONLY a valid JSON array of 3 strings
Example: ["Q1 text", "Q2 text", "Q3 text"]"""

    try:
        response = model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
        res = content.strip()
        qs = _parse_json_list(res)
        return [q for q in qs if isinstance(q, str)][:3]
    except Exception as e:
        print(f"Resume Q Gen Error: {e}")
        project_name = projects[0] if projects else "your most recent project"
        skill_name = skills[0] if skills else "your primary skill"
        skill2 = skills[1] if len(skills) > 1 else "a secondary tool"
        return [
            f"Walk me through the most technically challenging decision you made in {project_name}. What trade-offs did you consider?",
            f"Explain how {skill_name} handles concurrency/memory management internally. What pitfalls have you encountered?",
            f"If you had to redesign {project_name} to handle 10x the load, what would be your first 3 architectural changes and why?"
        ]

# ─────────────────────────────────────────────────────────────────
# NODES
# ─────────────────────────────────────────────────────────────────

def initialize(state: InterviewState):
    """Init: pre-generate 3 resume questions. RAG is fetched on-demand."""
    resume_data = state.get('resume_data', {})
    company = state.get('company', 'Google')
    role = state.get('role', 'SDE')

    print(f"--- Initializing Technical Interview: {role} @ {company} ---")
    resume_qs = _generate_resume_questions(resume_data)
    print(f"    Generated {len(resume_qs)} resume-based questions")

    return {
        'question_index':   0,
        'resume_questions': resume_qs,
        'questions_asked':  [],
        'answers':          [],
        'scores':           [],
        'interview_status': 'ongoing',
        'difficulty':       'medium',
        'final_response':   '',
    }


def generate_question(state: InterviewState):
    """
    Strict alternating controller:
      Even index (0, 2, 4) → Resume-based question (personalized)
      Odd  index (1, 3, 5) → RAG question (company/role specific)
    """
    idx         = state.get('question_index', 0)
    resume_data = state.get('resume_data', {})
    skills      = resume_data.get('skills', [])
    company     = state.get('company', 'Google')
    role        = state.get('role', 'SDE')
    difficulty  = state.get('difficulty', 'medium')
    asked       = state.get('questions_asked', [])
    project_kws = _extract_project_keywords(resume_data)

    if idx % 2 == 0:
        # ── Resume question ──────────────────────────────────────
        source    = "RESUME"
        resume_qs = state.get('resume_questions', [])
        q_idx     = idx // 2
        if q_idx < len(resume_qs):
            question = resume_qs[q_idx]
        else:
            question = _fetch_rag_question(company, role, difficulty, skills, project_kws, asked)
            source   = "RAG (FALLBACK)"
    else:
        # ── RAG question (on-demand) ─────────────────────────────
        source   = "RAG"
        question = _fetch_rag_question(company, role, difficulty, skills, project_kws, asked)

    print(f"\n[Technical Q{idx + 1}] Source: {source}")

    return {
        'interview_question': question,
        'questions_asked':    asked + [question],
        'question_index':     idx + 1,
        'final_response':     '',
    }


def ask_human(state: InterviewState):
    """Interrupt point — waits for user's answer."""
    return state


def evaluate_answer(state: InterviewState):
    """Evaluate the user's answer with rigorous, dynamic FAANG-style feedback."""
    q   = state.get('interview_question', '')
    ans = state.get('user_answer', '')
    resume_data = state.get('resume_data', {})
    skills = resume_data.get('skills', [])

    prompt = f"""You are a senior FAANG engineer conducting a technical interview.

Question Asked: {q}
Candidate's Answer: {ans}
Candidate's Skill Set: {', '.join(skills[:6]) if skills else 'Not specified'}

Evaluate this answer as a real FAANG interviewer would:
1. Did the candidate demonstrate depth of understanding or just surface knowledge?
2. Were trade-offs and edge cases considered?
3. Was the answer structured and clear?
4. What specific knowledge gap was revealed (if any)?

Provide:
- 2-3 sentences of direct, actionable feedback (FAANG style — honest, not generic)
- Highlight exactly ONE thing they did well
- Highlight exactly ONE specific area to improve with a concrete suggestion

End with exactly: SCORE: [number 1-10]
(10 = FAANG hire, 7-9 = strong candidate, 4-6 = needs work, 1-3 = significant gaps)"""

    try:
        response = model.invoke(prompt).content.strip()
        match = re.search(r"SCORE:\s*(\d+)", response)
        score_val = int(match.group(1)) if match else 5
        score_val = max(1, min(10, score_val))
        feedback_text = response.split("SCORE:")[0].strip()
    except Exception as e:
        print(f"Evaluate error: {e}")
        score_val = 5
        feedback_text = "Decent attempt. Focus on adding concrete examples and discussing trade-offs explicitly."

    return {
        'scores':         state.get('scores', []) + [score_val],
        'answers':        state.get('answers', []) + [ans],
        'final_response': feedback_text,
    }


def should_end(state: InterviewState) -> Literal["generate_question", "end_interview"]:
    """End after exactly 6 questions (3 resume + 3 RAG)."""
    if state.get('question_index', 0) >= 6:
        return "end_interview"
    return "generate_question"


def end_interview(state: InterviewState):
    """Generate fully dynamic AI feedback and save report to MongoDB."""
    scores    = state.get('scores', [])
    answers   = state.get('answers', [])
    questions = state.get('questions_asked', [])
    resume_data = state.get('resume_data', {})

    total_score   = sum(scores) / max(1, len(scores))
    resume_scores = [scores[i] for i in range(len(scores)) if i % 2 == 0]
    rag_scores    = [scores[i] for i in range(len(scores)) if i % 2 != 0]
    avg_resume    = sum(resume_scores) / max(1, len(resume_scores))
    avg_rag       = sum(rag_scores)    / max(1, len(rag_scores))

    session_id = state.get('session_id', 'sess_' + str(int(datetime.datetime.now().timestamp())))
    user_id    = state.get('user_id', 'user_default')

    # Build Q&A summary for dynamic AI feedback
    qa_summary = ""
    for i, (q, a, s) in enumerate(zip(questions, answers, scores)):
        source = "resume" if i % 2 == 0 else "technical"
        qa_summary += f"\nQ{i+1} [{source}] (Score: {s}/10): {q[:100]}...\nA: {a[:150]}...\n"

    prompt = f"""You are an expert FAANG technical interviewer writing a final evaluation report.

Candidate Profile:
- Skills: {', '.join(resume_data.get('skills', [])[:8])}
- Role Applied: {state.get('role', 'SDE')} at {state.get('company', 'Unknown')}
- Average Score: {total_score:.1f}/10
- Resume-based Q avg: {avg_resume:.1f}/10
- RAG/Technical Q avg: {avg_rag:.1f}/10

Interview Q&A Summary:
{qa_summary}

Generate a professional, SPECIFIC evaluation (not generic boilerplate):
Return ONLY a valid JSON object with these keys:
- "closing_message": Warm 1-2 sentence closing that references their specific score and role.
- "strengths": 2-3 sentence paragraph citing SPECIFIC things they did well based on their answers.
- "weakness": 2-3 sentence paragraph with SPECIFIC improvement areas with actionable advice.
- "hire_recommendation": One of ["Strong Hire", "Hire", "No Hire", "Strong No Hire"]

Return ONLY valid JSON. No markdown."""

    try:
        response = model.invoke(prompt).content.strip()
        if "```json" in response:
            response = response.split("```json")[-1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        feedback = json.loads(response)
        message      = feedback.get("closing_message", f"Technical interview complete! Average score: {total_score:.1f}/10.")
        strengths    = feedback.get("strengths", "Demonstrated solid technical foundation.")
        weaknesses   = feedback.get("weakness", "Focus on depth of explanation and trade-off analysis.")
        hire_rec     = feedback.get("hire_recommendation", "Hire")
    except Exception as e:
        print(f"End interview feedback error: {e}")
        message    = f"Technical interview complete! Your average score is {total_score:.1f}/10. Great effort today!"
        strengths  = "Good general technical knowledge across the topics covered."
        weaknesses = "Practice providing concrete examples and discussing system-level trade-offs."
        hire_rec   = "Hire" if total_score >= 6 else "No Hire"

    # Build unified report payload
    final_report = {
        "session_id":    session_id,
        "user_id":       user_id,
        "role":          state.get('role', 'SDE'),
        "company":       state.get('company', 'Unknown'),
        "interview_type": "technical",          # ✅ correct field name
        "score":         round(total_score, 1), # ✅ correct field name
        "breakdown": {
            "resume_based":  round(avg_resume, 1),
            "company_based": round(avg_rag, 1)
        },
        "questions": [
            {
                "question": questions[i] if i < len(questions) else "",
                "source":   "resume" if i % 2 == 0 else "rag",
                "answer":   answers[i]   if i < len(answers)   else "Not provided",
                "score":    scores[i]    if i < len(scores)     else 0,
                "feedback": {
                    "strengths":  [strengths],
                    "weaknesses": [weaknesses]
                }
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
            "difficulty_level": state.get("difficulty", "medium"),
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
            print(f"[OK] Technical report saved. Score: {total_score:.1f}/10 | Rec: {hire_rec}")
        else:
            print(f"[ERROR] Express error saving report: {res.status_code} - {res.text[:200]}")
    except Exception as e:
        print(f"[ERROR] Report save failed: {e}")

    return {
        'final_response':   f"{message}\n\n**Hire Recommendation:** {hire_rec}",
        'strengths':        strengths,
        'weakness':         weaknesses,
        'interview_status': 'ended'
    }

# ─────────────────────────────────────────────────────────────────
# GRAPH
# ─────────────────────────────────────────────────────────────────

graph = StateGraph(InterviewState)

graph.add_node('initialize',        initialize)
graph.add_node('generate_question', generate_question)
graph.add_node('ask_human',         ask_human)
graph.add_node('evaluate_answer',   evaluate_answer)
graph.add_node('end_interview',     end_interview)

graph.add_edge(START,               'initialize')
graph.add_edge('initialize',        'generate_question')
graph.add_edge('generate_question', 'ask_human')
graph.add_edge('ask_human',         'evaluate_answer')
graph.add_conditional_edges('evaluate_answer', should_end)
graph.add_edge('end_interview',     END)

workflow = graph.compile(checkpointer=checkpointer, interrupt_before=['ask_human'])

print("[OK] Technical workflow compiled (rich resume + RAG alternation, dynamic reports).")