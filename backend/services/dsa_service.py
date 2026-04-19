from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Import DSA workflow
from backend.workflows.dsa_workflow import workflow

router = APIRouter(prefix="/api/dsa", tags=["DSA Interview"])


# ── Request/Response Models ─────────────────────────────────────

class StartDSAInterviewRequest(BaseModel):
    difficulty: str = "medium"
    thread_id: str


class StartDSAInterviewResponse(BaseModel):
    question: str
    status: str


class SubmitDSAAnswerRequest(BaseModel):
    user_answer: str
    thread_id: str


class SubmitDSAAnswerResponse(BaseModel):
    feedback: str
    next_question: Optional[str] = None
    status: str  # continue / end


# ── Start Interview ─────────────────────────────────────────────

@router.post("/start", response_model=StartDSAInterviewResponse)
def start_dsa_interview(request: StartDSAInterviewRequest):
    try:
        initial_state = {
            "difficulty": request.difficulty,
            "phase": "problem",
            "hint_level": 0
        }

        config = {
            "configurable": {
                "thread_id": request.thread_id
            }
        }

        # Run workflow until first interrupt
        workflow.invoke(initial_state, config=config)

        state = workflow.get_state(config)

        question = state.values.get("interview_question", "") if state else ""

        if not question:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate DSA question"
            )

        return StartDSAInterviewResponse(
            question=question,
            status="waiting_for_approach"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ── Submit Answer ───────────────────────────────────────────────

@router.post("/answer", response_model=SubmitDSAAnswerResponse)
def submit_dsa_answer(request: SubmitDSAAnswerRequest):
    try:
        config = {
            "configurable": {
                "thread_id": request.thread_id
            }
        }

        state_snapshot = workflow.get_state(config)

        if not state_snapshot:
            raise HTTPException(
                status_code=400,
                detail="No active DSA session found"
            )

        # Update answer
        workflow.update_state(
            config,
            {"user_answer": request.user_answer},
            as_node="ask_human"
        )

        # Run next steps
        for event in workflow.stream(None, config=config):
            if "__interrupt__" in event:
                break

        final_state = workflow.get_state(config)
        state_values = final_state.values if final_state else {}

        next_q = state_values.get("interview_question", "")
        status = state_values.get("interview_status", "continue")

        return SubmitDSAAnswerResponse(
            feedback=state_values.get("final_response", ""),
            next_question=next_q,
            status=status
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ── Session Debug (Optional but useful) ─────────────────────────

@router.get("/session/{thread_id}")
def get_dsa_session(thread_id: str):
    try:
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        state = workflow.get_state(config)

        if not state:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "state": state.values,
            "next_node": state.next
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))