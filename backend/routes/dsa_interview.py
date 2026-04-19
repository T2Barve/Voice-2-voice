# """
# DSA Interview API — main.py
# ============================
# Entry point for the FastAPI application.

# Run with:
#     uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or from the project root if app/ is a package:
#     uvicorn app.main:app --reload
# """

# import logging
# import sys
# from contextlib import asynccontextmanager

# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse

# from app.routes.interview import router as interview_router

# # ── Logging setup ─────────────────────────────────────────────────────────────

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     handlers=[
#         logging.StreamHandler(sys.stdout),
#         logging.FileHandler("interview_api.log", encoding="utf-8"),
#     ],
# )
# logger = logging.getLogger(__name__)


# # ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logger.info("🚀 DSA Interview API starting up...")
#     # Eagerly import the workflow to catch any import errors at boot time,
#     # not on the first request.
#     try:
#         from app.services import interview_service  # noqa: F401
#         logger.info("✅ LangGraph workflow loaded successfully.")
#     except Exception as exc:
#         logger.critical(f"❌ Failed to load LangGraph workflow: {exc}")
#         # Don't block startup — let the health endpoint report the issue.
#     yield
#     logger.info("🛑 DSA Interview API shutting down.")


# # ── App instance ──────────────────────────────────────────────────────────────

# app = FastAPI(
#     title="DSA Interview API",
#     description=(
#         "A production-ready FastAPI backend for AI-powered DSA mock interviews. "
#         "Powered by LangGraph + Google Gemini."
#     ),
#     version="1.0.0",
#     lifespan=lifespan,
#     docs_url="/docs",
#     redoc_url="/redoc",
# )


# # ── CORS ──────────────────────────────────────────────────────────────────────
# # Allow all origins in development; tighten this in production.

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],          # Replace with your frontend URL in prod
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # ── Global exception handler ──────────────────────────────────────────────────

# @app.exception_handler(Exception)
# async def unhandled_exception_handler(request: Request, exc: Exception):
#     logger.exception(f"Unhandled exception on {request.method} {request.url}")
#     return JSONResponse(
#         status_code=500,
#         content={
#             "error": "Internal server error",
#             "detail": str(exc),
#         },
#     )


# # ── Routers ───────────────────────────────────────────────────────────────────

# app.include_router(interview_router)


# # ── Root health check ─────────────────────────────────────────────────────────

# @app.get("/", tags=["Health"])
# def root():
#     return {
#         "service": "DSA Interview API",
#         "version": "1.0.0",
#         "status":  "running",
#         "docs":    "/docs",
#     }


# @app.get("/health", tags=["Health"])
# def health():
#     return {"status": "ok"}


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# ✅ Import SERVICE instead of workflow
from backend.services.dsa_service import (
    start_dsa_interview,
    submit_dsa_answer
)

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
def start_dsa_interview_route(request: StartDSAInterviewRequest):
    try:
        question = start_dsa_interview(
            thread_id=request.thread_id,
            difficulty=request.difficulty
        )

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
def submit_dsa_answer_route(request: SubmitDSAAnswerRequest):
    try:
        result = submit_dsa_answer(
            thread_id=request.thread_id,
            user_answer=request.user_answer
        )

        return SubmitDSAAnswerResponse(
            feedback=result.get("feedback", ""),
            next_question=result.get("next_question", ""),
            status=result.get("status", "continue")
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ── Session Debug ───────────────────────────────────────────────

@router.get("/session/{thread_id}")
def get_dsa_session(thread_id: str):
    try:
        from backend.workflows.dsa_workflow import workflow

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        state = workflow.get_state(config)

        if not state:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )

        return {
            "thread_id": thread_id,
            "state": state.values,
            "next_node": state.next
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )