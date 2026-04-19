from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

# Import workflows
from backend.workflows.technical_workflow import workflow as technical_workflow
from backend.workflows.dsa_workflow import workflow as dsa_workflow
from backend.workflows.case_study_workflow import workflow as case_study_workflow
from backend.services.resume_service import process_resume
from backend.services.analytics_service import get_dashboard_metrics

app = FastAPI(title="AI Interview Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------
# REQUEST / RESPONSE MODELS
# ---------------------------------------------

class ResumeData(BaseModel):
    """Parsed resume context passed from frontend localStorage."""
    skills: List[str] = []
    projects: List[str] = []

class StartInterviewRequest(BaseModel):
    user_id: str
    session_id: str # Added session_id to match contract
    company: str = "Google"
    role: str = "SDE"
    interview_type: str = "technical"
    # Resume data is MANDATORY for personalized interviewing
    resume_data: ResumeData

class StartInterviewResponse(BaseModel):
    question: str
    status: str

class SubmitAnswerRequest(BaseModel):
    user_answer: str
    thread_id: str

class SubmitAnswerResponse(BaseModel):
    score: int = 0
    strengths: str = ""
    weakness: str = ""
    final_response: str = ""
    next_question: Optional[str] = None
    status: str

# ---------------------------------------------
# HELPERS
# ---------------------------------------------

def _build_base_state(request: StartInterviewRequest) -> dict:
    """Build the initial workflow state for the deterministic engine."""
    return {
        "session_id": request.session_id,
        "user_id": request.user_id,
        "role": request.role,
        "company": request.company,
        "interview_type": request.interview_type,
        "resume_data": {
            "skills": request.resume_data.skills,
            "projects": request.resume_data.projects
        },
        "question_index": 0,
        "questions_asked": [],
        "resume_questions": [],
        "rag_questions": [],
        "answers": [],
        "scores": [],
        "interview_status": "ongoing"
    }

async def handle_start(request: StartInterviewRequest, workflow_instance, interrupt_node: str = "ask_human"):
    try:
        initial_state = _build_base_state(request)
        config = {"configurable": {"thread_id": request.session_id}}

        workflow_instance.invoke(initial_state, config=config)
        state = workflow_instance.get_state(config)

        question = state.values.get("interview_question", "")
        if not question:
            raise Exception("Workflow failed to generate a question.")

        return StartInterviewResponse(question=question, status="waiting_for_answer")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def handle_submit(request: SubmitAnswerRequest, workflow_instance, interview_type: str, interrupt_node: str = "ask_human"):
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        state_snapshot = workflow_instance.get_state(config)

        if not state_snapshot:
            raise HTTPException(status_code=400, detail="No active session found. Start the interview first.")

        # Inject user answer at the interrupt node
        workflow_instance.update_state(
            config,
            {"user_answer": request.user_answer},
            as_node=interrupt_node
        )

        # Stream until next interrupt or end
        for event in workflow_instance.stream(None, config=config):
            if '__interrupt__' in event:
                break

        final_state = workflow_instance.get_state(config)
        st = final_state.values if final_state else {}

        is_ended = not final_state.next if final_state else True
        status = "ended" if is_ended else "continue"

        resp = SubmitAnswerResponse(
            score=st.get("score", 0),
            strengths=st.get("strengths", ""),
            weakness=st.get("weakness", ""),
            final_response=st.get("final_response", ""),
            status=status,
        )

        if status == "continue":
            q = st.get("interview_question", "")
            if q:
                resp.next_question = q

        return resp

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------
# ENDPOINTS
# ---------------------------------------------

@app.get("/")
async def root():
    return {"status": "AI Interview Platform API Running"}

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Actual resume parsing endpoint using LangChain service."""
    try:
        parsed_data = await process_resume(file)
        return {
            "status": "success",
            "data": parsed_data
        }
    except Exception as e:
        print(f"Resume Upload Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

@app.get("/api/analytics")
async def get_analytics():
    try:
        return {"status": "success", "data": get_dashboard_metrics()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# DSA Interviews
@app.post("/api/dsa/start", response_model=StartInterviewResponse)
async def start_dsa(request: StartInterviewRequest):
    return await handle_start(request, dsa_workflow, interrupt_node="ask_human")

@app.post("/api/dsa/submit", response_model=SubmitAnswerResponse)
async def submit_dsa(request: SubmitAnswerRequest):
    return await handle_submit(request, dsa_workflow, "DSA", interrupt_node="ask_human")

# Technical Interviews
@app.post("/api/technical/start", response_model=StartInterviewResponse)
async def start_tech(request: StartInterviewRequest):
    return await handle_start(request, technical_workflow, interrupt_node="ask_human")

@app.post("/api/technical/submit", response_model=SubmitAnswerResponse)
async def submit_tech(request: SubmitAnswerRequest):
    return await handle_submit(request, technical_workflow, "Technical", interrupt_node="ask_human")

# Case Study Interviews
@app.post("/api/case-study/start", response_model=StartInterviewResponse)
async def start_cs(request: StartInterviewRequest):
    return await handle_start(request, case_study_workflow, interrupt_node="ask")

@app.post("/api/case-study/submit", response_model=SubmitAnswerResponse)
async def submit_cs(request: SubmitAnswerRequest):
    return await handle_submit(request, case_study_workflow, "Case Study", interrupt_node="ask")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)