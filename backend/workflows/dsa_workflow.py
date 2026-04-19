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

model = ChatGoogleGenerativeAI(model='models/gemini-2.5-flash')

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

    candidate_approach: str
    approach_verdict: str
    candidate_code: str
    code_verdict: str
    hints_given: int
    opt_status: str
    candidate_complexity: str
    complexity_correct: bool

    score: int
    strengths: str
    weakness: str
    final_response: str
    
    question_count: int
    interview_stage: str
    interview_status: str
    asked_question_ids: list
    difficulty: str

# ─────────────────────────────────────────────
# HELPER — pick a question using RAG
# ─────────────────────────────────────────────

def pick_question_rag(state: InterviewState) -> dict:
    difficulty = state.get('difficulty', 'medium')
    company = state.get('company', 'Google')
    role = state.get('role', 'Software Engineer')
    skills = state.get('resume_data', {}).get('skills', [])
    
    context = retrieve_questions(company, "dsa", difficulty, role, skills=skills, k=3)
    
    prompt = f"""You are an expert FAANG interviewer. Extract ONE coding problem from the provided Context.
    
Context:
{context}

Format the output strictly as JSON with the following keys:
- id: a unique string ID
- difficulty: {difficulty}
- title: Problem title
- problem: The detailed problem description and constraints
- hints: A list of 2-3 string hints
- optimal: The optimal algorithmic approach
- time_complexity: e.g., O(n)
- space_complexity: e.g., O(1)
- edge_cases: A list of 2-3 string edge cases

Ensure the problem is challenging and directly relevant to the Context provided. Return ONLY valid JSON."""

    res = model.invoke(prompt).content.strip()
    if res.startswith("```json"):
        res = res[7:-3].strip()
    elif res.startswith("```"):
        res = res[3:-3].strip()
        
    try:
        q_data = json.loads(res)
        return q_data
    except Exception as e:
        print(f"Failed to parse RAG question into JSON: {e}")
        # RAG must not fail silently, but if JSON parsing fails from a valid doc, we have to raise.
        raise Exception("Failed to generate structured question from RAG documents")


# ─────────────────────────────────────────────
# NODES
# ─────────────────────────────────────────────

def initialize(state: InterviewState):
    """Initialize the interview session."""
    print(f"\n- Starting DSA interview for session: {state.get('session_id')} -")
    return {
        'question_count': 0,
        'hints_given': 0,
        'opt_status': 'needed',
        'interview_stage': 'clarifying',
        'interview_status': 'ongoing',
        'asked_question_ids': [],
        'score': 0,
        'difficulty': 'medium'
    }


def select_question(state: InterviewState):
    """Pick next question using RAG."""
    asked_ids = state.get('asked_question_ids', [])
    q = pick_question_rag(state)

    print(f"\n- Selected: [{q.get('difficulty', 'unknown').upper()}] {q.get('title', 'Question')}")

    return {
        'current_question_data': q,
        'interview_question': f"[Question {state.get('question_count', 0) + 1}] **{q.get('title', 'Problem')}**\n\n{q.get('problem', '')}",
        'question_count': state.get('question_count', 0) + 1,
        'asked_question_ids': asked_ids + [q.get('id', 'temp_id')],
        'interview_stage': 'clarifying',
        'hints_given': 0,
        'opt_status': 'needed',
        'candidate_approach': '',
        'candidate_code': '',
        'candidate_complexity': '',
        'approach_verdict': '',
        'code_verdict': '',
        'complexity_correct': False,
    }


def ask_clarifying(state: InterviewState):
    """Ask candidate if they have clarifying questions."""
    q = state.get('current_question_data', {})
    print(f"\n- Stage: CLARIFYING - waiting for candidate...")

    prompt = f"""You are a FAANG interviewer. You just showed the candidate this problem:

Title: {q.get('title')}
Problem: {q.get('problem')}

Now ask them: "Do you have any clarifying questions before we begin? Feel free to ask about constraints, input format, or edge cases."

Keep your message short (2-3 sentences max). Do NOT reveal hints or the solution."""

    response = model.invoke(prompt)
    message = response.content.strip()
    return {
        'final_response': message,
        'interview_question': message,
        'interview_stage': 'clarifying'
    }


def handle_clarifying(state: InterviewState):
    """Human answers clarifying questions — interrupt node."""
    print("DEBUG — waiting for clarifying answer from candidate...")
    return state


def respond_to_clarification(state: InterviewState):
    answer = state.get('user_answer', '')
    q = state.get('current_question_data', {})

    ready_signals = ['no', 'ready', 'ok', 'start']

    if any(sig in answer.lower() for sig in ready_signals):
        message = "Great! Walk me through your approach at a high level."

        return {
            'final_response': message,
            'interview_question': message,  
            'interview_stage': 'approach'
        }

    prompt = f"""You are a FAANG interviewer. Answer the candidate's clarifying question about this problem.

Problem: {q.get('title')} — {q.get('problem')}
Constraints: edges cases include {', '.join(q.get('edge_cases', [])[:2])}
Candidate asked: "{answer}"

Rules:
- Answer questions about input format, constraints, and edge cases directly
- If they're probing for the solution, say "That's a great thing to think about as you work through it"
- End with: "Any other questions, or shall we start?"
- Keep it under 3 sentences."""

    response = model.invoke(prompt)
    message = response.content.strip()

    return {
        'final_response': message,
        'interview_question': message,  
        'interview_stage': 'clarifying'
    }


def should_move_from_clarify(state: InterviewState) -> Literal["stay", "approach"]:
    """Stay in clarifying or move to approach phase."""
    stage = state.get('interview_stage', 'clarifying')
    if stage == 'approach':
        return "approach"
    return "stay"


def ask_approach(state: InterviewState):
    """Ask candidate to explain their approach."""
    message = "Explain your approach at a high level"

    return {
        'final_response': "Before you start coding, walk me through your approach at a high level. What algorithm or data structure are you thinking of using, and why?",
        'interview_question' : message,
        'interview_stage': 'approach'
    }


def handle_approach(state: InterviewState):
    """Human explains their approach — interrupt node."""
    print("DEBUG — waiting for approach from candidate...")
    return state


def evaluate_approach(state: InterviewState):
    """Evaluate the candidate's explained approach."""
    q = state.get('current_question_data', {})
    approach = state.get('user_answer', '')

    print(f"DEBUG — Evaluating approach: {approach[:60]}...")

    prompt = f"""You are a FAANG interviewer evaluating a candidate's approach.

Problem: {q.get('title')} — {q.get('problem')}
Correct approach: {q.get('optimal')}
Edge cases to probe: {', '.join(q.get('edge_cases', []))}
Candidate's approach: "{approach}"

Determine if the approach is:
- VALID: logically correct and complete → say "Your approach sounds solid, go ahead and implement it."
- FLAWED: has a bug → challenge with ONE specific counterexample from edge cases, do NOT fix it
- UNCLEAR: too vague → ask one follow-up question

Rules:
- Do NOT mention time/space complexity yet
- Do NOT write any code
- Keep response to 2-3 sentences max

At the end of your response, on a new line write exactly one of: VERDICT:VALID or VERDICT:FLAWED or VERDICT:UNCLEAR"""

    response = model.invoke(prompt)
    content = response.content.strip()

    # Extract verdict
    verdict = "unclear"
    if "VERDICT:VALID" in content:
        verdict = "valid"
    elif "VERDICT:FLAWED" in content:
        verdict = "flawed"
    elif "VERDICT:UNCLEAR" in content:
        verdict = "unclear"

    # Clean message (remove the VERDICT line)
    message = content.replace("VERDICT:VALID", "").replace("VERDICT:FLAWED", "").replace("VERDICT:UNCLEAR", "").strip()

    next_stage = 'coding' if verdict == 'valid' else 'approach'

    print(f"DEBUG — Approach verdict: {verdict}")

    return {
        'candidate_approach': approach,
        'approach_verdict': verdict,
        'final_response': message,
        'interview_question' : message,
        'interview_stage': next_stage
    }


def should_move_from_approach(state: InterviewState) -> Literal["coding", "retry_approach"]:
    """Move to coding if approach is valid, else retry."""
    verdict = state.get('approach_verdict', 'unclear')
    if verdict == 'valid':
        return "coding"
    return "retry_approach"


def ask_coding(state: InterviewState):
    """Invite candidate to write code."""
    message = "Go ahead and implement your solution"
    return {
        'final_response': "Great! Go ahead and implement your solution. Take your time, and think out loud if that helps.",
        'interview_question' : message,
        'interview_stage': 'coding'
    }


def handle_coding(state: InterviewState):
    """Human writes code — interrupt node."""
    print("DEBUG — waiting for code from candidate...")
    return state


def evaluate_code(state: InterviewState):
    """Evaluate the submitted code."""
    q = state.get('current_question_data', {})
    code = state.get('user_answer', '')

    print(f"DEBUG — Evaluating code: {code[:60]}...")

    prompt = f"""You are a FAANG interviewer reviewing code.

Problem: {q.get('title')}
Expected approach: {q.get('optimal')}
Candidate's code:
{code}

Evaluate on: correctness, algorithm logic, readability, potential bugs.

Rules:
- Do NOT reveal time/space complexity yet
- Do NOT rewrite or fix the code  
- If bugs: point to the specific logic issue without giving the fix
- Keep feedback to 3-4 sentences

At the end write exactly one of: VERDICT:CORRECT or VERDICT:PARTIAL or VERDICT:INCORRECT"""

    response = model.invoke(prompt)
    content = response.content.strip()

    verdict = "partial"
    if "VERDICT:CORRECT" in content:
        verdict = "correct"
    elif "VERDICT:PARTIAL" in content:
        verdict = "partial"
    elif "VERDICT:INCORRECT" in content:
        verdict = "incorrect"

    message = content.replace("VERDICT:CORRECT", "").replace("VERDICT:PARTIAL", "").replace("VERDICT:INCORRECT", "").strip()

    print(f"DEBUG — Code verdict: {verdict}")

    return {
        'candidate_code': code,
        'code_verdict': verdict,
        'final_response': message,
        'interview_question' : message,
        'interview_stage': 'edge_cases'
    }


def ask_edge_cases(state: InterviewState):
    """Ask about edge case handling."""
    q = state.get('current_question_data', {})
    edge_cases = q.get('edge_cases', [])

    print("\n- Stage: EDGE CASES - waiting for candidate...")

    prompt = f"""You are a FAANG interviewer. Ask the candidate about edge cases.

Problem: {q.get('title')}
Edge cases to probe: {', '.join(edge_cases)}

Pick 2 of these edge cases and ask: "How would your solution handle [case1] or [case2]?"
Do NOT tell them the answer. Keep it to 1-2 sentences."""

    response = model.invoke(prompt)
    message = response.content.strip()
    return {
        'final_response': response.content.strip(),
        'interview_question' : message,
        'interview_stage': 'edge_cases'
    }


def handle_edge_cases(state: InterviewState):
    """Human answers edge cases — interrupt node."""
    print("DEBUG — waiting for edge case response...")
    return state


def evaluate_edge_cases(state: InterviewState):
    """Evaluate edge case response and move to optimization."""
    q = state.get('current_question_data', {})
    answer = state.get('user_answer', '')

    prompt = f"""You are a FAANG interviewer. Evaluate this edge case response.

Problem: {q.get('title')}
Known edge cases: {', '.join(q.get('edge_cases', []))}
Candidate said: "{answer}"

Give brief feedback (2 sentences). Then say: "Now, do you think there's a way to make your solution more efficient?"
Don't reveal the optimal complexity."""

    response = model.invoke(prompt)
    return {
        'final_response': response.content.strip(),
        'interview_stage': 'optimization'
    }


def handle_optimization(state: InterviewState):
    """Human attempts optimization — interrupt node."""
    print("\n- Stage: OPTIMIZATION - waiting for candidate...")
    print("DEBUG — waiting for optimization response...")
    return state


def process_optimization(state: InterviewState):
    hints_given = state.get('hints_given', 0)

    if hints_given == 0:
        message = "Think if a better data structure can optimize this."

        return {
            'hints_given': 1,
            'final_response': message,
            'interview_question': message,  
            'interview_stage': 'optimization'
        }

    if hints_given == 1:
        message = "Try using a hashmap or similar structure."

        return {
            'hints_given': 2,
            'final_response': message,
            'interview_question': message,  
            'interview_stage': 'optimization'
        }

    message = "Good. Now tell me time and space complexity."

    return {
        'opt_status': 'done',
        'final_response': message,
        'interview_question': message,  
        'interview_stage': 'complexity'
    }


def should_continue_optimization(state: InterviewState) -> Literal["retry", "complexity"]:
    """Stay in optimization or move to complexity."""
    stage = state.get('interview_stage', 'optimization')
    if stage == 'complexity':
        return "complexity"
    return "retry"


def ask_complexity(state: InterviewState):
    """Ask for time and space complexity."""
    message = "Explain time and space complexity"
    return {
        'final_response': "Can you walk me through the time complexity and space complexity of your solution? Please explain your reasoning.",
        'interview_question' : message,
        'interview_stage': 'complexity'
    }


def handle_complexity(state: InterviewState):
    """Human explains complexity — interrupt node."""
    print("DEBUG — waiting for complexity explanation...")
    return state


def evaluate_complexity(state: InterviewState):
    """Evaluate complexity explanation and score the whole question."""
    q = state.get('current_question_data', {})
    answer = state.get('user_answer', '')

    prompt = f"""Evaluate this complexity analysis.

Problem: {q.get('title')}
Correct time complexity: {q.get('time_complexity')}
Correct space complexity: {q.get('space_complexity')}
Candidate said: "{answer}"

Give specific feedback (2-3 sentences). If wrong, ask them to reconsider.
At the end write exactly: CORRECT:YES or CORRECT:NO"""

    response = model.invoke(prompt)
    content = response.content.strip()

    complexity_correct = "CORRECT:YES" in content
    message = content.replace("CORRECT:YES", "").replace("CORRECT:NO", "").strip()

    print(f"DEBUG — Complexity correct: {complexity_correct}")

    return {
        'candidate_complexity': answer,
        'complexity_correct': complexity_correct,
        'final_response': message,
        'interview_stage': 'scoring'
    }


def score_and_feedback(state: InterviewState):
    """Score the question and give comprehensive feedback."""
    q = state.get('current_question_data', {})
    approach_verdict = state.get('approach_verdict', '')
    code_verdict = state.get('code_verdict', '')
    hints_given = state.get('hints_given', 0)
    opt_status = state.get('opt_status', 'needed')
    complexity_correct = state.get('complexity_correct', False)

    print(f"DEBUG — Scoring: approach={approach_verdict}, code={code_verdict}, hints={hints_given}")

    # Base scoring logic
    scores = {
        'approach': 2 if approach_verdict == 'valid' else 1,
        'code':     2 if code_verdict == 'correct' else (1 if code_verdict == 'partial' else 0),
        'opt':      2 if (opt_status == 'done' and hints_given == 0) else (1 if opt_status == 'done' else 0),
        'complexity': 1 if complexity_correct else 0,
        'communication': random.choice([1, 1, 2])
    }

    total = sum(scores.values())
    total = max(0, min(10, total + random.choice([-1, 0, 1])))

    prompt = f"""Give interview feedback for this question.

Problem: {q.get('title')}
Approach: {approach_verdict}, Code: {code_verdict}, Hints used: {hints_given}/2, Score: {total}/10

Write:
STRENGTHS: [2 sentences about what they did well]
IMPROVEMENTS: [2 sentences about what to improve]"""

    try:
        response = model.invoke(prompt)
        content = response.content.strip()

        if "STRENGTHS:" in content and "IMPROVEMENTS:" in content:
            parts = content.split("IMPROVEMENTS:")
            strengths = parts[0].replace("STRENGTHS:", "").strip()
            weakness = parts[1].strip()
        else:
            strengths = "Showed solid problem-solving skills."
            weakness = "Could improve explanation clarity and edge case coverage."

    except Exception as e:
        print(f"DEBUG — Feedback error: {e}")
        strengths = "Good attempt overall."
        weakness = "Try to be more structured and detailed."

    print(f"DEBUG — Final score: {total}/10")

    return {
        'score': total,
        'strengths': strengths,
        'weakness': weakness,
        'final_response': f"Score for this question: {total}/10\n\nStrengths: {strengths}\n\nTo improve: {weakness}",
        'interview_stage': 'done'
    }

def transition(state: InterviewState):
    """Transition to next question or end."""
    count = state.get('question_count', 0)
    transitions = [
        "Great work! Let's move on to the next question.",
        "Good effort. Let's continue with another problem.",
        "Alright, moving on to the next one.",
        "Let's tackle the next question."
    ]
    return {'final_response': random.choice(transitions)}


def should_end(state: InterviewState) -> Literal["continue", "end"]:
    """End after 3 questions."""
    count = state.get('question_count', 0)
    print(f"DEBUG — Question count: {count}")
    if count >= 3:
        return "end"
    return "continue"


def end_interview(state: InterviewState):
    """Final summary of interview and Analytics Report Generation."""
    
    score = state.get('score', 0)
    company = state.get('company', 'Unknown')
    role = state.get('role', 'SDE')
    difficulty = state.get('difficulty', 'medium')
    session_id = state.get('session_id', 'sess_' + str(int(datetime.datetime.now().timestamp())))
    user_id = state.get('user_id', 'user_default')

    print("DEBUG — Generating Final Analytics Report...")
    user_id = state.get('user_id', 'user_default')

    prompt = f"""Write a brief interview closing for user {user_id}.

They completed DSA questions. Final score on last question: {score}/10.

Include:
- Thank them
- 1 line on overall performance
- 1-2 topics to improve

Keep it under 4 sentences. Be warm and professional."""

    try:
        response = model.invoke(prompt)
        message = response.content.strip()
    except Exception as e:
        print(f"DEBUG — End interview error: {e}")
        message = "Thank you for your time! You performed well overall. Keep practicing DSA and problem-solving."
        
    final_report = {
        "session_id": session_id,
        "user_id": user_id,
        "company": company,
        "role": role,
        "interview_type": "dsa",
        "score": score,
        "skills": {
            "dsa": min(10, max(0, score + 1)),
            "communication": 8,
            "problem_solving": min(10, max(0, score)),
            "system_design": 6,
            "core_cs": 7
        },
        "strengths": [state.get('strengths', 'Solid problem solving abilities.')],
        "weaknesses": [state.get('weakness', 'Edge case handling issues.')],
        "questions": [
            {
                "question": state.get('interview_question', 'Question text missing'),
                "userAnswer": state.get('user_answer', 'Answer missing'),
                "score": score,
                "feedback": {
                    "strengths": [state.get('strengths', 'Good approach')],
                    "weaknesses": [state.get('weakness', 'Optimization needed')]
                }
            }
        ],
        "resume_summary": {
            "skills": state.get('resume_data', {}).get('skills', []),
            "projects": state.get('resume_data', {}).get('projects', []),
            "experience": "Not specified"
        },
        "metadata": {
            "total_questions": state.get('question_count', 1),
            "duration_seconds": 180, # Placeholder or can calculate if timestamps added to state
            "difficulty_level": difficulty,
            "started_at": datetime.datetime.now().isoformat(),
            "completed_at": datetime.datetime.now().isoformat()
        }
    }

    print(f"Sending report to Express: {session_id}")
    try:
        res = requests.post("http://localhost:5000/api/report/save", json=final_report, timeout=10)
        if not res.ok:
            print(f"Express Error: {res.status_code} - {res.text}")
            raise Exception(f"Express rejected report save: {res.text}")
        print("Report successfully accepted by Express")
    except Exception as e:
        print(f"FATAL: Failed to submit final_report: {e}")
        # We don't want to crash the whole interview if reporting fails, but we should log it heavily
        # raise Exception(f"Report Saving Pipeline Failed: {e}") 

    return {
        'final_response': message,
        'interview_status': 'ended'
    }

# ─────────────────────────────────────────────
# BUILD GRAPH
# ─────────────────────────────────────────────

graph = StateGraph(InterviewState)

# Add all nodes
graph.add_node('initialize',              initialize)
graph.add_node('select_question',         select_question)
graph.add_node('ask_clarifying',          ask_clarifying)
graph.add_node('handle_clarifying',       handle_clarifying)
graph.add_node('respond_to_clarification',respond_to_clarification)
graph.add_node('ask_approach',            ask_approach)
graph.add_node('handle_approach',         handle_approach)
graph.add_node('evaluate_approach',       evaluate_approach)
graph.add_node('ask_coding',              ask_coding)
graph.add_node('handle_coding',           handle_coding)
graph.add_node('evaluate_code',           evaluate_code)
graph.add_node('ask_edge_cases',          ask_edge_cases)
graph.add_node('handle_edge_cases',       handle_edge_cases)
graph.add_node('evaluate_edge_cases',     evaluate_edge_cases)
graph.add_node('handle_optimization',     handle_optimization)
graph.add_node('process_optimization',    process_optimization)
graph.add_node('ask_complexity',          ask_complexity)
graph.add_node('handle_complexity',       handle_complexity)
graph.add_node('evaluate_complexity',     evaluate_complexity)
graph.add_node('score_and_feedback',      score_and_feedback)
graph.add_node('transition',              transition)
graph.add_node('end_interview',           end_interview)

# ── Fixed edges ───────────────────────────────
graph.add_edge(START,                      'initialize')
graph.add_edge('initialize',               'select_question')
graph.add_edge('select_question',          'ask_clarifying')
graph.add_edge('ask_clarifying',           'handle_clarifying')
graph.add_edge('handle_clarifying',        'respond_to_clarification')

# ── Clarifying loop or move to approach ───────
graph.add_conditional_edges(
    'respond_to_clarification',
    should_move_from_clarify,
    {
        'stay':     'handle_clarifying',
        'approach': 'ask_approach'
    }
)

graph.add_edge('ask_approach',             'handle_approach')
graph.add_edge('handle_approach',          'evaluate_approach')

# ── Approach loop or move to coding ───────────
graph.add_conditional_edges(
    'evaluate_approach',
    should_move_from_approach,
    {
        'coding':         'ask_coding',
        'retry_approach': 'handle_approach'
    }
)

graph.add_edge('ask_coding',               'handle_coding')
graph.add_edge('handle_coding',            'evaluate_code')
graph.add_edge('evaluate_code',            'ask_edge_cases')
graph.add_edge('ask_edge_cases',           'handle_edge_cases')
graph.add_edge('handle_edge_cases',        'evaluate_edge_cases')
graph.add_edge('evaluate_edge_cases',      'handle_optimization')
graph.add_edge('handle_optimization',      'process_optimization')

# ── Optimization loop or move to complexity ───
graph.add_conditional_edges(
    'process_optimization',
    should_continue_optimization,
    {
        'retry':      'handle_optimization',
        'complexity': 'ask_complexity'
    }
)

graph.add_edge('ask_complexity',           'handle_complexity')
graph.add_edge('handle_complexity',        'evaluate_complexity')
graph.add_edge('evaluate_complexity',      'score_and_feedback')
graph.add_edge('score_and_feedback',       'transition')

# ── End or next question ──────────────────────
graph.add_conditional_edges(
    'transition',
    should_end,
    {
        'continue': 'select_question',
        'end':      'end_interview'
    }
)

graph.add_edge('end_interview', END)

# ─────────────────────────────────────────────
# COMPILE
# ─────────────────────────────────────────────

workflow = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=[
        'handle_clarifying',
        'handle_approach',
        'handle_coding',
        'handle_edge_cases',
        'handle_optimization',
        'handle_complexity',
    ]
)

print("DONE: DSA Interview workflow compiled!")
