from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import random
import json

load_dotenv()

model = ChatGoogleGenerativeAI(model='models/gemini-2.5-flash', temperature=0.7)

conn = sqlite3.connect(database='interview.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

class InterviewState(TypedDict):
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
    interview_status: str
    difficulty: str

def pick_question_rag(state: InterviewState) -> str:
    from backend.rag.retriever import retrieve_questions
    
    company = state.get('company', 'Google')
    role = state.get('role', 'Software Engineer')
    skills = state.get('resume_skills', [])
    difficulty = state.get('difficulty', 'medium')
    asked = state.get('asked_questions', [])
    
    context = retrieve_questions(company, "technical", difficulty, role, skills=skills, k=3)
    
    prompt = f"""You are an expert FAANG interviewer for {company}.
Candidate Skills: {', '.join(skills[:5])}
Questions Already Asked: {asked}

Extracted Knowledge Context:
{context}

Select one high-quality technical interview question from the Context above that hasn't been asked yet.
Return ONLY the question text (no JSON, no json blocks, no quotes, no extra formatting)."""

    res = model.invoke(prompt).content.strip()
    return res

def _generate_resume_questions(skills: list, projects: list) -> list:
    """Generate Exactly 3 deep technical questions based on resume."""
    prompt = f"""You are an elite FAANG tech interviewer.
Generate EXACTLY 3 deep technical interview questions based on the candidate's resume:
Skills: {skills}
Projects: {projects}

Rules:
- No generic questions.
- Focus on internals, trade-offs, and edge cases.
- Return ONLY a valid JSON array of strings. 
Example Output: ["Question 1", "Question 2", "Question 3"]"""

    try:
        res = model.invoke(prompt).content.strip()
        # Clean markdown
        if "```json" in res: res = res.split("```json")[-1].split("```")[0].strip()
        elif "```" in res: res = res.split("```")[-1].split("```")[0].strip()
        
        qs = json.loads(res)
        return qs[:3]
    except Exception as e:
        print(f"Resume Q Gen Error: {e}")
        return []

def remove_overlap(rag_questions: list, skills: list) -> list:
    """Filter RAG questions that overlap with resume skills."""
    filtered = []
    skill_set = set([s.lower() for s in skills])
    for q in rag_questions:
        # Assuming RAG returns list of strings or dicts with 'question' and 'tags'
        # If retriever.py returns raw context, we need to extract questions first
        # But here we'll assume we pass the raw strings for simplicity or extract them
        q_text = q if isinstance(q, str) else q.get('question', '')
        q_tags = [] if isinstance(q, str) else q.get('tags', [])
        
        if not any(tag.lower() in skill_set for tag in q_tags):
            filtered.append(q_text)
    return filtered

def initialize(state: InterviewState):
    """MANDATORY Initialization: Pre-generate all 6 questions."""
    skills = state.get('resume_data', {}).get('skills', [])
    projects = state.get('resume_data', {}).get('projects', [])
    company = state.get('company', 'Google')
    role = state.get('role', 'SDE')
    
    print(f"--- Initializing Deterministic Interview for {role} at {company} ---")
    
    # 1. Generate Resume Questions
    resume_qs = _generate_resume_questions(skills, projects)
    
    # 2. Retrieve RAG Questions
    from backend.rag.retriever import retrieve_questions
    try:
        # Retrieve context
        context = retrieve_questions(company, "technical", "medium", role, skills=skills, k=10)
        
        # Extract 5 questions from context to allow for overlap filtering
        extract_prompt = f"From the following context, extract 5 unique technical interview questions. Return ONLY a JSON array of strings. \nContext: {context}"
        rag_res = model.invoke(extract_prompt).content.strip()
        if "```json" in rag_res: rag_res = rag_res.split("```json")[-1].split("```")[0].strip()
        raw_rag_qs = json.loads(rag_res)
        
        # 3. Filter Overlap
        filtered_rag = remove_overlap(raw_rag_qs, skills)
        rag_qs = filtered_rag[:3]
    except Exception as e:
        print(f"RAG Retrieval Error: {e}")
        rag_qs = []

    # FAIL FAST (STRICT RULE)
    if len(resume_qs) < 3:
        raise Exception("Resume question generation failed (less than 3 generated)")
    if len(rag_qs) < 3:
        raise Exception("RAG retrieval failed (less than 3 generated after filtering)")

    return {
        'question_index': 0,
        'resume_questions': resume_qs,
        'rag_questions': rag_qs,
        'questions_asked': [],
        'answers': [],
        'scores': [],
        'interview_status': 'ongoing'
    }

def generate_question(state: InterviewState):
    """Deterministic 50/50 Controller logic."""
    idx = state.get('question_index', 0)
    
    if idx % 2 == 0:
        source = "resume"
        question = state['resume_questions'][idx // 2]
    else:
        source = "rag"
        question = state['rag_questions'][idx // 2]
    
    print(f"\n- Q{idx+1} Source: {source.upper()}")
    
    return {
        'interview_question': f"[Q{idx + 1}] {question}",
        'questions_asked': state['questions_asked'] + [question],
        'question_index': idx + 1
    }

def ask_human(state: InterviewState):
    return state
    
def evaluate_answer(state: InterviewState):
    q = state.get('interview_question', '')
    ans = state.get('user_answer', '')
    
    prompt = f"""You are a FAANG interviewer. Evaluate the candidate's answer to the technical question.

Question: {q}
Answer: {ans}

Provide concise feedback (max 3 sentences). 
End your feedback with a precise score out of 10, formatted exactly as:
SCORE: [number]"""

    response = model.invoke(prompt).content.strip()
    
    try:
        import re
        match = re.search(r"SCORE:\s*(\d+)", response)
        score_val = int(match.group(1)) if match else 5
    except:
        score_val = 5
        
    feedback_text = response.split("SCORE:")[0].strip()
    
    return {
        'scores': state.get('scores', []) + [score_val],
        'answers': state.get('answers', []) + [ans],
        'final_response': feedback_text,
    }
    
def transition(state: InterviewState):
    return {}

def should_end(state: InterviewState) -> Literal["generate_question", "end_interview"]:
    # 🔥 Deterministic 6-question limit
    if state.get('question_index', 0) >= 6:
        return "end_interview"
    return "generate_question"

def end_interview(state: InterviewState):
    """Final summary of interview and Analytics Report Generation."""
    import requests
    import datetime
    
    scores = state.get('scores', [])
    answers = state.get('answers', [])
    questions = state.get('questions_asked', [])
    
    total_score = sum(scores) / max(1, len(scores))
    
    # Calculate Breakdown
    resume_scores = [scores[i] for i in range(len(scores)) if i % 2 == 0]
    rag_scores = [scores[i] for i in range(len(scores)) if i % 2 != 0]
    
    avg_resume = sum(resume_scores) / max(1, len(resume_scores))
    avg_rag = sum(rag_scores) / max(1, len(rag_scores))

    session_id = state.get('session_id', 'sess_' + str(int(datetime.datetime.now().timestamp())))
    user_id = state.get('user_id', 'user_default')

    final_report = {
        "session_id": session_id,
        "user_id": user_id,
        "role": state.get('role', 'SDE'),
        "company": state.get('company', 'Unknown'),
        "type": "technical",
        "total_score": round(total_score, 1),
        "breakdown": {
            "resume_based": round(avg_resume, 1),
            "company_based": round(avg_rag, 1)
        },
        "questions": [
            {
                "question": questions[i],
                "source": "resume" if i % 2 == 0 else "rag",
                "answer": answers[i] if i < len(answers) else "Not provided",
                "score": scores[i] if i < len(scores) else 0
            } for i in range(len(questions))
        ],
        "strengths": ["Solid foundation in core skills.", "Good problem solving approach."],
        "weaknesses": ["Edge case handling can be improved.", "Consider more optimized alternatives."]
    }

    print(f"Sending Final Report to Express: {session_id}")
    try:
        res = requests.post("http://localhost:5000/api/report/save", json=final_report, timeout=10)
        if not res.ok:
            print(f"Express Error: {res.status_code} - {res.text}")
        else:
            print("Report successfully stored in MongoDB")
    except Exception as e:
        print(f"Report Saving Failed: {e}")
    
    return {
        'final_response': f"The interview is complete. Your total score is {total_score:.1f}/10. Thank you!",
        'interview_status': 'ended'
    }

graph = StateGraph(InterviewState)

graph.add_node('initialize', initialize)
graph.add_node('generate_question', generate_question)
graph.add_node('ask_human', ask_human)
graph.add_node('evaluate_answer', evaluate_answer)
graph.add_node('transition', transition)
graph.add_node('end_interview', end_interview)

graph.add_edge(START, 'initialize')
graph.add_edge('initialize', 'generate_question')
graph.add_edge('generate_question', 'ask_human')
graph.add_edge('ask_human', 'evaluate_answer')
graph.add_edge('evaluate_answer', 'transition')

graph.add_conditional_edges('transition', should_end)
graph.add_edge('end_interview', END)

workflow = graph.compile(checkpointer=checkpointer, interrupt_before=['ask_human'])