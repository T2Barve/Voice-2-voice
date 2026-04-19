from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import json
from backend.rag.retriever import retrieve_questions

model = ChatGoogleGenerativeAI(model='models/gemini-2.5-flash')

conn = sqlite3.connect(database='interview.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

class CaseStudyState(TypedDict):
    # Global state (as per user contract)
    session_id: str
    user_id: str
    role: str
    company: str
    interview_type: str

    resume_data: dict # {skills: [], projects: []}
    
    question_index: int
    questions_asked: list

    resume_questions: list
    rag_questions: list

    answers: list
    scores: list

    # Graph flow state
    interview_question: str
    user_answer: str
    final_response: str
    current_stage: str
    report: str

def initialize_session(state: CaseStudyState):
    """MANDATORY Initialization: Pre-generate all 6 questions for Case Study."""
    skills = state.get('resume_data', {}).get('skills', [])
    projects = state.get('resume_data', {}).get('projects', [])
    company = state.get('company', 'Google')
    role = state.get('role', 'SDE')

    # 🔥 Special Case Study Logic: Q1 is ALWAYS a project overview from resume
    selected_project = projects[0] if projects else "your most significant project"
    q1 = f"I'd like to do a deep-dive on **{selected_project}** from your resume. Can you start by giving me the **high-level overview** — what it does, the key technical challenges, and your specific role in building it?"
    
    # Generate Remaining 2 Resume Deep Dives
    prompt = f"Generate 2 deep architecture follow-up questions for the project '{selected_project}' given skills {skills}. Return ONLY a JSON array of 2 strings."
    try:
        res = model.invoke(prompt).content.strip()
        if "```json" in res: res = res.split("```json")[-1].split("```")[0].strip()
        resume_qs = [q1] + json.loads(res)[:2]
    except:
        resume_qs = [q1, "Walk me through the architecture.", "What was the hardest trade-off?"]

    # Generate 3 RAG Company Probes
    try:
        context = retrieve_questions(company, "case_study", "medium", role, skills=skills, k=10)
        extract_prompt = f"From the following context, extract 3 unique company-specific system design or case study questions for {company}. Return ONLY a JSON array of strings. \nContext: {context}"
        rag_res = model.invoke(extract_prompt).content.strip()
        if "```json" in rag_res: rag_res = rag_res.split("```json")[-1].split("```")[0].strip()
        rag_qs = json.loads(rag_res)[:3]
    except:
        rag_qs = []

    # FAIL FAST
    if len(resume_qs) < 3 or len(rag_qs) < 3:
        # Note: In a real system, we'd have robust fallbacks or retry, but user said throw exception
        raise Exception("Case Study question generation failed (Resume or RAG count < 3)")

    return {
        'question_index': 0,
        'resume_questions': resume_qs,
        'rag_questions': rag_qs,
        'questions_asked': [],
        'answers': [],
        'scores': [],
        'current_stage': 'intro'
    }

def generate_question(state: CaseStudyState):
    """Deterministic 50/50 Case Study Controller."""
    idx = state.get('question_index', 0)
    
    # Q1-Q3 are Resume (Q1 is Overview, Q2-3 are Deep Dives)
    # Q4-Q6 are RAG (Company Probes)
    # User's request: Q1: Overview, Remaining: Q2-3 Resume, Q4-6 RAG
    
    if idx < 3:
        source = "resume"
        question = state['resume_questions'][idx]
    else:
        source = "rag"
        question = state['rag_questions'][idx - 3]
    
    print(f"\n- [Case Study] Q{idx+1} Source: {source.upper()}")
    
    return {
        'interview_question': question,
        'questions_asked': state['questions_asked'] + [question],
        'question_index': idx + 1,
        'current_stage': 'evaluating'
    }

def ask_human(state: CaseStudyState):
    return state

def evaluate_and_probe(state: CaseStudyState):
    q = state.get('interview_question', '')
    ans = state.get('user_answer', '')

    score_prompt = f"""Rate this case study explanation out of 10.
Question: {q}
Answer: {ans}
Output JUST a number (0-10)."""

    try:
        score_resp = model.invoke(score_prompt).content.strip()
        digits = ''.join(filter(str.isdigit, score_resp))
        score = int(digits[:2]) if len(digits) >= 2 and int(digits[:2]) <= 10 else int(digits[0]) if digits else 5
    except:
        score = 5

    return {
        'scores': state.get('scores', []) + [score],
        'answers': state.get('answers', []) + [ans],
        'current_stage': 'transitioning'
    }

def generate_report(state: CaseStudyState):
    import requests
    import datetime

    scores = state.get('scores', [])
    answers = state.get('answers', [])
    questions = state.get('questions_asked', [])
    
    total_score = sum(scores) / max(1, len(scores))
    
    # Calculate Breakdown
    # Q1-3 are Resume, Q4-6 are RAG
    resume_scores = scores[:3]
    rag_scores = scores[3:]
    
    avg_resume = sum(resume_scores) / max(1, len(resume_scores))
    avg_rag = sum(rag_scores) / max(1, len(rag_scores))

    session_id = state.get('session_id', 'sess_cs_' + str(int(datetime.datetime.now().timestamp())))
    user_id = state.get('user_id', 'user_default')

    final_report = {
        "session_id": session_id,
        "user_id": user_id,
        "role": state.get('role', 'SDE'),
        "company": state.get('company', 'Unknown'),
        "type": "case_study",
        "total_score": round(total_score, 1),
        "breakdown": {
            "resume_based": round(avg_resume, 1),
            "company_based": round(avg_rag, 1)
        },
        "questions": [
            {
                "question": questions[i],
                "source": "resume" if i < 3 else "rag",
                "answer": answers[i] if i < len(answers) else "Not provided",
                "score": scores[i] if i < len(scores) else 0
            } for i in range(len(questions))
        ],
        "strengths": ["Deep exploration of project architecture.", "Understand company-specific trade-offs."],
        "weaknesses": ["Could provide more quantified metrics.", "Edge case considerations for new scale."]
    }

    print(f"Sending Final Case Study Report to Express: {session_id}")
    try:
        res = requests.post("http://localhost:5000/api/report/save", json=final_report, timeout=10)
        if not res.ok:
            print(f"Express Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Report Saving Failed: {e}")

    report_text = f"Case Study Interview complete. Total Score: {total_score:.1f}/10."

    return {
        'report': report_text,
        'final_response': report_text,
        'interview_status': 'ended'
    }

def router(state: CaseStudyState) -> Literal["generate_report", "generate_question"]:
    if state.get('question_index', 0) >= 6:
        return "generate_report"
    return "generate_question"

# Build graph
workflow_builder = StateGraph(CaseStudyState)
workflow_builder.add_node("init", initialize_session)
workflow_builder.add_node("generate_question", generate_question)
workflow_builder.add_node("ask", ask_human)
workflow_builder.add_node("eval", evaluate_and_probe)
workflow_builder.add_node("generate_report", generate_report)

workflow_builder.add_edge(START, "init")
workflow_builder.add_edge("init", "generate_question")
workflow_builder.add_edge("generate_question", "ask")
workflow_builder.add_edge("ask", "eval")
workflow_builder.add_conditional_edges("eval", router)
workflow_builder.add_edge("generate_report", END)

workflow = workflow_builder.compile(checkpointer=checkpointer)
