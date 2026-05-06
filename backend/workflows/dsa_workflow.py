from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import random
import json
import requests
import datetime
import os
from pathlib import Path
from backend.rag.retriever import retrieve_questions

load_dotenv()

model = ChatGoogleGenerativeAI(model='gemini-flash-latest', temperature=0.5)

_DB_PATH = Path(__file__).resolve().parent.parent / 'dsa_checkpoints.db'
conn = sqlite3.connect(database=str(_DB_PATH), check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────

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

    # DSA Specific States
    interview_question: str
    current_question_data: dict
    user_answer: str

    candidate_code: str
    candidate_complexity: str

    score: int
    strengths: str
    weakness: str
    final_response: str
    
    question_count: int
    interview_stage: str
    interview_status: str
    asked_question_ids: list
    asked_question_titles: list   # Track titles to prevent repeats
    difficulty: str
    wrong_attempt_count: int

# ─────────────────────────────────────────────
# HELPER — pick a question using RAG
# ─────────────────────────────────────────────

def pick_question_rag(state: InterviewState) -> dict:
    difficulty = state.get('difficulty', 'medium')
    company = state.get('company', 'Google')
    role = state.get('role', 'Software Engineer')
    skills = state.get('resume_data', {}).get('skills', [])
    # Track asked titles so we can explicitly forbid them
    asked_titles = state.get('asked_question_titles', [])
    
    # Fetch more context (k=6) to give the model more variety to choose from
    context = retrieve_questions(company, "dsa", difficulty, role, skills=skills, k=6)
    
    # Build a clear "do not repeat" block
    if asked_titles:
        avoid_block = "\n".join(f"  - {t}" for t in asked_titles)
        avoid_section = f"""CRITICAL — Do NOT pick any of these already-asked problems:
{avoid_block}

You MUST select a DIFFERENT problem with a DIFFERENT title and algorithm."""
    else:
        avoid_section = "This is the first question — pick the best one from the context."
    
    prompt = f"""You are an expert FAANG interviewer for {company} hiring {role}.
Candidate skills: {', '.join(skills[:5]) if skills else 'General'}

{avoid_section}

Knowledge Base (extract from ONLY these):
{context}

Select ONE coding problem from the Knowledge Base above.
STRICT RULE: The "title" and "problem" MUST match the content in the Knowledge Base EXACTLY. Do not invent new problems or modify existing ones.

Return ONLY valid JSON with these keys (no markdown, no code fences):
{{
  "id": "unique_slug_id",
  "difficulty": "{difficulty}",
  "title": "Verbatim Problem Title from PDF",
  "problem": "Verbatim full problem description and constraints from PDF",
  "optimal": "Optimal algorithmic approach",
  "time_complexity": "O(?)",
  "space_complexity": "O(?)",
  "edge_cases": ["edge case 1", "edge case 2"]
}}"""

    try:
        response = model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
        res = content.strip()
        # Strip markdown code fences if present
        if "```json" in res:
            res = res.split("```json")[-1].split("```")[0].strip()
        elif "```" in res:
            res = res.split("```")[1].split("```")[0].strip()
            
        q_data = json.loads(res)
        return q_data
    except Exception as e:
        print(f"Failed to fetch/parse RAG question: {e}")
        # Fallback — pick a safe default that's unlikely to duplicate
        fallbacks = [
            {
                "id": "fallback_lru_cache",
                "difficulty": difficulty,
                "title": "LRU Cache",
                "problem": "Design a data structure that follows the Least Recently Used (LRU) cache constraints. Implement get(key) and put(key, value) in O(1).",
                "optimal": "Use a doubly linked list + hash map.",
                "time_complexity": "O(1)",
                "space_complexity": "O(capacity)",
                "edge_cases": ["Capacity 1", "Repeated key put", "Get on missing key"]
            },
            {
                "id": "fallback_word_ladder",
                "difficulty": difficulty,
                "title": "Word Ladder",
                "problem": "Given two words (beginWord, endWord) and a wordList, find the length of shortest transformation from beginWord to endWord, changing one letter at a time.",
                "optimal": "BFS with adjacency via wildcard patterns.",
                "time_complexity": "O(M^2 * N)",
                "space_complexity": "O(M^2 * N)",
                "edge_cases": ["endWord not in list", "Same begin/end word", "Empty list"]
            }
        ]
        # Pick whichever fallback hasn't been asked yet
        for fb in fallbacks:
            if fb['title'] not in asked_titles:
                return fb
        return fallbacks[0]


# ─────────────────────────────────────────────
# NODES - Streamlined 4-Stage Workflow
# ─────────────────────────────────────────────

def initialize(state: InterviewState):
    """Initialize the interview session."""
    print(f"\n- Starting DSA interview for session: {state.get('session_id')} -")
    return {
        'question_count': 0,
        'interview_stage': 'coding',
        'interview_status': 'ongoing',
        'asked_question_ids': [],
        'asked_question_titles': [],
        'score': 0,
        'difficulty': 'medium',
        'wrong_attempt_count': 0
    }

def select_question(state: InterviewState):
    """Pick next question using RAG — guaranteed to be different from previously asked."""
    asked_ids     = state.get('asked_question_ids', [])
    asked_titles  = state.get('asked_question_titles', [])
    q = pick_question_rag(state)

    title = q.get('title', 'Question')
    print(f"\n- Selected: [{q.get('difficulty', 'unknown').upper()}] {title}")

    return {
        'current_question_data': q,
        'question_count':        state.get('question_count', 0) + 1,
        'asked_question_ids':    asked_ids   + [q.get('id', title.lower().replace(' ', '_'))],
        'asked_question_titles': asked_titles + [title],
        'interview_stage':       'coding',   # Reset stage for new question
        'wrong_attempt_count':    0,          # Reset wrong count for new question
    }

def present_question(state: InterviewState):
    """Greets the user and presents the problem clearly."""
    q = state.get('current_question_data', {})
    is_first = state.get('question_count', 0) == 1
    
    if is_first:
        msg = f"""Hello! I'm your FAANG interviewer today. Let's get right into the technical portion.
        
**{q.get('title')}**
{q.get('problem')}

When you are ready, please walk me through your approach and write your code. Remember, I am looking for the most optimal solution."""
    else:
        msg = f"""Great work. Let's move on to the next problem.
        
**{q.get('title')}**
{q.get('problem')}

Please provide your approach and optimal code snippet when ready."""

    return {
        'interview_question': msg,
        'final_response': msg
    }

def ask_human(state: InterviewState):
    """Interrupt node to wait for user input (code or text)."""
    print("DEBUG — waiting for user input...")
    return state

def route_from_human(state: InterviewState) -> Literal["evaluate_code", "evaluate_complexity"]:
    """Routes the human response to the correct evaluation node based on the current stage."""
    stage = state.get('interview_stage', 'coding')
    if stage == 'complexity':
        return "evaluate_complexity"
    return "evaluate_code"

def evaluate_code(state: InterviewState):
    """Evaluates the submitted code, checking for optimality and bugs."""
    q = state.get('current_question_data', {})
    code = state.get('user_answer', '')
    
    print("DEBUG — Evaluating submitted code...")

    # IMPORTANT: Do NOT include expected time/space complexity in the prompt.
    # That would leak the answer before we ask the candidate to explain it.
    prompt = f"""You are a FAANG interviewer evaluating a code submission.

Problem: {q.get('title')}
{q.get('problem')}

Expected Optimal Approach: {q.get('optimal')}

Candidate's Submission:
{code}

Analyze the logic, edge cases, and whether the approach is optimal.
Return ONLY a valid JSON object with the following keys:
- "is_optimal": boolean (true ONLY if the code is both correct AND uses the optimal expected approach, false otherwise)
- "feedback": 2-3 sentences of concise feedback. Give a hint if not optimal, or brief praise if optimal. Do NOT mention exact time/space complexity values.

Return ONLY valid JSON."""

    try:
        response = model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
        response_str = content.strip()
        
        if "```json" in response_str:
            response_str = response_str.split("```json")[-1].split("```")[0].strip()
        elif "```" in response_str:
            response_str = response_str.split("```")[1].split("```")[0].strip()
            
        import json
        eval_data = json.loads(response_str)
        is_optimal = eval_data.get("is_optimal", False)
        msg = eval_data.get("feedback", "Please check your logic and try again.")
    except Exception as e:
        print(f"Evaluation error: {e}")
        # Re-raise so the frontend shows the actual API error instead of trapping the user in a "try again" loop
        raise Exception(f"Failed to evaluate code: {str(e)}")

    if is_optimal:
        next_stage = 'complexity'
        # Ask for TC/SC as a separate clean question — don't reveal the answer
        msg = f"{msg}\n\nNow, what is the **Time Complexity** and **Space Complexity** of your solution? Walk me through your reasoning."
        return {
            'interview_stage': next_stage,
            'interview_question': msg,
            'final_response': msg,
            'wrong_attempt_count': 0
        }
    else:
        attempts = state.get('wrong_attempt_count', 0) + 1
        if attempts >= 2:
            # Failure Exit
            msg = f"{msg}\n\nI think we should stop the interview here as we've hit the maximum attempts for this problem. Let's move to your final evaluation."
            return {
                'interview_stage': 'end_interview',
                'interview_status': 'ended',
                'interview_question': msg,
                'final_response': msg,
                'wrong_attempt_count': attempts
            }
        else:
            return {
                'interview_stage': 'coding',
                'interview_question': msg,
                'final_response': msg,
                'wrong_attempt_count': attempts
            }

def evaluate_complexity(state: InterviewState):
    """Evaluates the complexity explanation and triggers sequence transition."""
    q = state.get('current_question_data', {})
    ans = state.get('user_answer', '')
    
    print("DEBUG — Evaluating complexity...")

    prompt = f"""Evaluate this complexity analysis for {q.get('title')}.
Correct Time Complexity: {q.get('time_complexity')}
Correct Space Complexity: {q.get('space_complexity')}
Candidate said: "{ans}"

Provide very brief feedback (1-2 sentences). 
At the end write exactly: CORRECT:YES or CORRECT:NO"""
    
    try:
        response = model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
        res = content.strip()
        
        is_correct = "CORRECT:YES" in res
        msg = res.replace("CORRECT:YES", "").replace("CORRECT:NO", "").strip()
    except:
        is_correct = True
        msg = "Good analysis of the complexity."
        
    score_bump = random.choice([7, 8, 9]) if is_correct else random.choice([4, 5, 6])
    current_score = state.get('score', 0) + score_bump

    msg += f"\n\nPerfect, that concludes this question."

    return {
        'score': min(10, current_score // max(1, state.get('question_count', 1))),
        'interview_question': msg,
        'final_response': msg
    }

def route_after_complexity(state: InterviewState) -> Literal["select_question", "end_interview"]:
    """Decide whether to move to the next question or generate the final report."""
    count = state.get('question_count', 0)
    print(f"DEBUG — Question count: {count}")
    if count >= 3:
        return "end_interview"
    return "select_question"

def end_interview(state: InterviewState):
    """Final summary of interview and Analytics Report Generation."""
    
    score = state.get('score', 0)
    company = state.get('company', 'Unknown')
    role = state.get('role', 'SDE')
    difficulty = state.get('difficulty', 'medium')
    session_id = state.get('session_id', 'sess_' + str(int(datetime.datetime.now().timestamp())))
    user_id = state.get('user_id', 'user_default')

    print("DEBUG — Generating Final Analytics Report...")

    asked_titles = state.get('asked_question_titles', [])
    problems_str = ", ".join(asked_titles) if asked_titles else "DSA problems"

    prompt = f"""You are an expert FAANG interviewer closing a DSA interview.
The candidate attempted these problems: {problems_str}.
Their final score was {score}/30 (each of the 3 questions was worth up to 10 points).

Based on their score and the typical performance expected for FAANG, generate a professional, constructive evaluation. 
Return ONLY a valid JSON object with the following keys:
- "closing_message": A warm 1-2 sentence thank you and overall performance summary.
- "strengths": A 2-3 sentence paragraph detailing what they likely did well (their approach, logic, etc.).
- "weakness": A 2-3 sentence paragraph detailing the expected optimal approaches they should focus on and what they missed.

Return ONLY valid JSON."""

    try:
        response = model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
        response_str = content.strip()

        if "```json" in response_str:
            response_str = response_str.split("```json")[-1].split("```")[0].strip()
        elif "```" in response_str:
            response_str = response_str.split("```")[1].split("```")[0].strip()
            
        import json
        feedback_data = json.loads(response_str)
        message = feedback_data.get("closing_message", "Thank you for your time! Keep practicing.")
        strengths = feedback_data.get("strengths", "Solid problem solving abilities.")
        weaknesses = feedback_data.get("weakness", "Focus more on identifying the most optimal approach.")
    except Exception as e:
        print(f"DEBUG — End interview error: {e}")
        message = "Thank you for your time! You performed well overall. Keep practicing DSA and problem-solving."
        strengths = "Good fundamental understanding of data structures."
        weaknesses = "Practice identifying optimal space-time tradeoffs."
        
    resume_data = state.get('resume_data', {})
    final_report = {
        "session_id":     session_id,
        "user_id":        user_id,
        "company":        company,
        "role":           role,
        "interview_type": "dsa",           # ✅ correct field
        "score":          score,            # ✅ correct field
        "breakdown": {
            "resume_based":  round(score * 0.5, 1),
            "company_based": round(score * 0.5, 1)
        },
        "strengths":  [strengths],
        "weaknesses": [weaknesses],
        "questions": [
            {
                "question": f"DSA Problems Attempted: {problems_str}",
                "source":   "rag",
                "answer":   "Code submitted during session.",
                "score":    score,
                "feedback": {
                    "strengths":  [strengths],
                    "weaknesses": [weaknesses]
                }
            }
        ],
        "resume_summary": {
            "skills":     resume_data.get('skills', []),
            "projects":   resume_data.get('projects', []),
            "experience": resume_data.get('experience', 'Not specified')
        },
        "metadata": {
            "total_questions":  state.get('question_count', 1),
            "duration_seconds": 0,
            "difficulty_level": difficulty,
            "started_at":       datetime.datetime.now().isoformat(),
            "completed_at":     datetime.datetime.now().isoformat()
        }
    }

    try:
        headers = {"x-internal-secret": "interview_ai_internal_secret_2026"}
        res = requests.post("http://localhost:5000/api/report/save", json=final_report, headers=headers, timeout=10)
        if not res.ok:
            print(f"Express Error: {res.status_code} - {res.text}")
        else:
            print("Report successfully accepted by Express")
    except Exception as e:
        print(f"FATAL: Failed to submit final_report: {e}")

    return {
        'final_response':   message,
        'strengths':        strengths,
        'weakness':         weaknesses,
        'interview_status': 'ended'
    }

def route_after_evaluation(state: InterviewState) -> Literal["ask_human", "end_interview"]:
    """Route to human input for more attempts OR end interview if attempts exhausted."""
    if state.get('interview_stage') == 'end_interview':
        return "end_interview"
    return "ask_human"

# ─────────────────────────────────────────────
# BUILD GRAPH
# ─────────────────────────────────────────────

graph = StateGraph(InterviewState)

# Add all nodes
graph.add_node('initialize', initialize)
graph.add_node('select_question', select_question)
graph.add_node('present_question', present_question)
graph.add_node('ask_human', ask_human)
graph.add_node('evaluate_code', evaluate_code)
graph.add_node('evaluate_complexity', evaluate_complexity)
graph.add_node('end_interview', end_interview)

# Define Edges
graph.add_edge(START, 'initialize')
graph.add_edge('initialize', 'select_question')
graph.add_edge('select_question', 'present_question')

# After presenting the question, always pause for user code
graph.add_edge('present_question', 'ask_human')

# Logic branches after user submitted something
graph.add_conditional_edges(
    'ask_human',
    route_from_human,
    {
        'evaluate_code': 'evaluate_code',
        'evaluate_complexity': 'evaluate_complexity'
    }
)

# After evaluating code, it either asks for more code (loops) or asks for complexity OR ends
graph.add_conditional_edges(
    'evaluate_code',
    route_after_evaluation,
    {
        'ask_human': 'ask_human',
        'end_interview': 'end_interview'
    }
)

# After evaluating complexity, decide whether to ask next question or end
graph.add_conditional_edges(
    'evaluate_complexity',
    route_after_complexity,
    {
        'select_question': 'select_question',
        'end_interview': 'end_interview'
    }
)

graph.add_edge('end_interview', END)

# Compile with interrupt
workflow = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=['ask_human']
)

print("DONE: DSA 4-Stage Interview workflow compiled!")
