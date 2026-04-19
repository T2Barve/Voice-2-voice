# # from fastapi import FastAPI
# # from fastapi.middleware.cors import CORSMiddleware
# # from pydantic import BaseModel
# # from dotenv import load_dotenv
# # import uuid
# # import sqlite3
# # from typing import TypedDict

# # from langgraph.graph import StateGraph, START, END
# # from langgraph.checkpoint.sqlite import SqliteSaver
# # from langchain_google_genai import ChatGoogleGenerativeAI

# # # --------------------------------------------------
# # # INIT
# # # --------------------------------------------------
# # load_dotenv()

# # app = FastAPI()

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],  # dev only
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # llm = ChatGoogleGenerativeAI(
# #     model="models/gemini-2.5-flash",
# #     temperature=0.7
# # )

# # conn = sqlite3.connect("interview.db", check_same_thread=False)
# # checkpointer = SqliteSaver(conn)

# # # --------------------------------------------------
# # # REQUEST MODELS
# # # --------------------------------------------------
# # class StartInterviewRequest(BaseModel):
# #     role: str
# #     experience: str


# # class AnswerRequest(BaseModel):
# #     thread_id: str
# #     answer: str


# # # --------------------------------------------------
# # # LANGGRAPH STATE
# # # --------------------------------------------------
# # class InterviewState(TypedDict):
# #     role: str
# #     experience: str
# #     question: str
# #     answer: str
# #     score: int
# #     round: int
# #     feedback: str
# #     done: bool


# # # --------------------------------------------------
# # # GRAPH NODES
# # # --------------------------------------------------
# # def generate_question(state: InterviewState):
# #     prompt = f"""
# #     You are a senior interviewer.
# #     Role: {state['role']}
# #     Experience: {state['experience']}

# #     Ask ONE hard interview question.
# #     No explanation. Question only.
# #     """

# #     question = llm.invoke(prompt).content.strip()

# #     return {
# #         "question": question,
# #         "round": state.get("round", 0) + 1,
# #         "done": False
# #     }


# # def evaluate_answer(state: InterviewState):
# #     prompt = f"""
# #     Evaluate the candidate answer from 1 to 10.

# #     Question: {state['question']}
# #     Answer: {state['answer']}

# #     Respond ONLY with a number.
# #     """

# #     raw_score = llm.invoke(prompt).content.strip()

# #     try:
# #         score = int(raw_score[0])
# #     except:
# #         score = 5

# #     return {"score": score}


# # def decide_next_step(state: InterviewState):
# #     if state["round"] >= 5:
# #         return {
# #             "feedback": "Interview completed. Thank you.",
# #             "done": True
# #         }

# #     if state["score"] >= 7:
# #         return {"feedback": "Good answer. Next question."}
# #     else:
# #         return {"feedback": "Needs improvement. Try another question."}


# # # --------------------------------------------------
# # # BUILD LANGGRAPH
# # # --------------------------------------------------
# # graph = StateGraph(InterviewState)

# # graph.add_node("generate_question", generate_question)
# # graph.add_node("evaluate_answer", evaluate_answer)
# # graph.add_node("decide_next_step", decide_next_step)

# # graph.add_edge(START, "generate_question")
# # graph.add_edge("generate_question", END)

# # graph.add_edge("evaluate_answer", "decide_next_step")
# # graph.add_edge("decide_next_step", "generate_question")

# # workflow = graph.compile(
# #     checkpointer=checkpointer,
# #     interrupt_before=["evaluate_answer"]
# # )

# # # --------------------------------------------------
# # # API ROUTES
# # # --------------------------------------------------
# # @app.post("/start")
# # def start_interview(data: StartInterviewRequest):
# #     thread_id = str(uuid.uuid4())

# #     state = {
# #         "role": data.role,
# #         "experience": data.experience,
# #         "round": 0
# #     }

# #     result = workflow.invoke(
# #         state,
# #         config={"thread_id": thread_id}
# #     )

# #     return {
# #         "thread_id": thread_id,
# #         "question": result["question"]
# #     }


# # @app.post("/answer")
# # def submit_answer(data: AnswerRequest):
# #     result = workflow.invoke(
# #         {"answer": data.answer},
# #         config={"thread_id": data.thread_id}
# #     )

# #     if result.get("done"):
# #         return {
# #             "done": True,
# #             "message": result["feedback"]
# #         }

# #     return {
# #         "done": False,
# #         "feedback": result["feedback"],
# #         "next_question": result["question"]
# #     }





# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional
# import uvicorn

# # Import your LangGraph workflow
# from main import workflow

# app = FastAPI(title="AI Interview Platform API")

# # Enable CORS for frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify your frontend domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Request/Response Models
# class StartInterviewRequest(BaseModel):
#     role: str
#     experience: str
#     thread_id: str


# class StartInterviewResponse(BaseModel):
#     question: str
#     status: str


# class SubmitAnswerRequest(BaseModel):
#     user_answer: str
#     thread_id: str


# class SubmitAnswerResponse(BaseModel):
#     score: int
#     strengths: str
#     weakness: str
#     final_response: str
#     next_question: Optional[str] = None
#     status: str  # continue, success, fail


# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {"status": "API is running", "message": "AI Interview Platform"}


# @app.post("/api/start-interview", response_model=StartInterviewResponse)
# async def start_interview(request: StartInterviewRequest):
#     """
#     Start a new interview session
    
#     Args:
#         role: The job role (Software Engineer, ML Engineer, etc.)
#         experience: Years of experience (0-2 years, 3-5 years, 5+ years)
#         thread_id: Unique session identifier
    
#     Returns:
#         First interview question
#     """
#     try:
#         # Initialize state
#         initial_state = {
#             "role": request.role,
#             "experience": request.experience,
#             "user_message": f"Interview for {request.role} with {request.experience} experience",
#             "attempt_count": 0
#         }
        
#         # Configuration with thread_id for checkpointing
#         config = {
#             "configurable": {
#                 "thread_id": request.thread_id
#             }
#         }
        
#         # Run workflow until first interrupt (ask_human)
#         result = workflow.invoke(initial_state, config=config)
        
#         # Extract the generated question
#         question = result.get("interview_question", "")
        
#         if not question:
#             raise HTTPException(
#                 status_code=500,
#                 detail="Failed to generate interview question"
#             )
        
#         return StartInterviewResponse(
#             question=question,
#             status="waiting_for_answer"
#         )
        
#     except Exception as e:
#         print(f"Error in start_interview: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to start interview: {str(e)}"
#         )


# @app.post("/api/submit-answer", response_model=SubmitAnswerResponse)
# async def submit_answer(request: SubmitAnswerRequest):
#     """
#     Submit user's answer and get feedback
    
#     Args:
#         user_answer: The user's spoken/typed answer
#         thread_id: Session identifier to continue the conversation
    
#     Returns:
#         Score, feedback, and next question (if applicable)
#     """
#     try:
#         # Configuration with thread_id
#         config = {
#             "configurable": {
#                 "thread_id": request.thread_id
#             }
#         }
        
#         # Get current state to check if we're at the interrupt
#         state_snapshot = workflow.get_state(config)
        
#         if not state_snapshot:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No active interview session found. Please start a new interview."
#             )
        
#         # Resume from interrupt with user's answer
#         result = workflow.invoke(
#             {"user_answer": request.user_answer},
#             config=config
#         )
        
#         # Extract evaluation results
#         score = result.get("score", 0)
#         strengths = result.get("strengths", "")
#         weakness = result.get("weakness", "")
#         final_response = result.get("final_response", "")
#         interview_status = result.get("interview_status", "continue")
        
#         response_data = {
#             "score": score,
#             "strengths": strengths,
#             "weakness": weakness,
#             "final_response": final_response,
#             "status": interview_status
#         }
        
#         # If interview continues, include next question
#         if interview_status == "continue":
#             next_question = result.get("interview_question", "")
#             response_data["next_question"] = next_question
        
#         return SubmitAnswerResponse(**response_data)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in submit_answer: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to process answer: {str(e)}"
#         )


# @app.get("/api/session/{thread_id}")
# async def get_session_state(thread_id: str):
#     """
#     Get the current state of an interview session
    
#     Args:
#         thread_id: Session identifier
    
#     Returns:
#         Current state of the interview
#     """
#     try:
#         config = {
#             "configurable": {
#                 "thread_id": thread_id
#             }
#         }
        
#         state = workflow.get_state(config)
        
#         if not state:
#             raise HTTPException(
#                 status_code=404,
#                 detail="Session not found"
#             )
        
#         return {
#             "thread_id": thread_id,
#             "state": state.values,
#             "next_node": state.next
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in get_session_state: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to retrieve session: {str(e)}"
#         )


# @app.delete("/api/session/{thread_id}")
# async def delete_session(thread_id: str):
#     """
#     Delete an interview session
    
#     Args:
#         thread_id: Session identifier
    
#     Returns:
#         Success message
#     """
#     try:
#         # Note: LangGraph doesn't have a direct delete method
#         # The session will naturally expire or be overwritten
#         return {
#             "message": f"Session {thread_id} marked for cleanup",
#             "thread_id": thread_id
#         }
        
#     except Exception as e:
#         print(f"Error in delete_session: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to delete session: {str(e)}"
#         )


# if __name__ == "__main__":
#     print("🚀 Starting AI Interview Platform API...")
#     print("📍 Server running on: http://localhost:8000")
#     print("📖 API docs available at: http://localhost:8000/docs")
    
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8000,
#         log_level="info"
#     )




# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional
# import uvicorn

# # Import your LangGraph workflow
# from main import workflow

# app = FastAPI(title="AI Interview Platform API")

# # Enable CORS for frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify your frontend domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Request/Response Models
# class StartInterviewRequest(BaseModel):
#     role: str
#     experience: str
#     thread_id: str


# class StartInterviewResponse(BaseModel):
#     question: str
#     status: str


# class SubmitAnswerRequest(BaseModel):
#     user_answer: str
#     thread_id: str


# class SubmitAnswerResponse(BaseModel):
#     score: int
#     strengths: str
#     weakness: str
#     final_response: str
#     next_question: Optional[str] = None
#     status: str  # continue, success, fail


# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {"status": "API is running", "message": "AI Interview Platform"}


# @app.post("/api/start-interview", response_model=StartInterviewResponse)
# async def start_interview(request: StartInterviewRequest):
#     """
#     Start a new interview session
    
#     Args:
#         role: The job role (Software Engineer, ML Engineer, etc.)
#         experience: Years of experience (0-2 years, 3-5 years, 5+ years)
#         thread_id: Unique session identifier
    
#     Returns:
#         First interview question
#     """
#     try:
#         # Initialize state
#         initial_state = {
#             "role": request.role,
#             "experience": request.experience,
#             "user_message": f"Interview for {request.role} with {request.experience} experience",
#             "attempt_count": 0
#         }
        
#         # Configuration with thread_id for checkpointing
#         config = {
#             "configurable": {
#                 "thread_id": request.thread_id
#             }
#         }
        
#         # Run workflow until first interrupt (ask_human)
#         # This will stop at ask_human node
#         result = workflow.invoke(initial_state, config=config)
        
#         print("DEBUG - Initial workflow result:", result)
        
#         # After interrupt, get the state to retrieve the question
#         state = workflow.get_state(config)
        
#         print("DEBUG - State after interrupt:", state.values if state else "No state")
        
#         # Extract the generated question from state
#         question = state.values.get("interview_question", "") if state else ""
        
#         if not question:
#             raise HTTPException(
#                 status_code=500,
#                 detail="Failed to generate interview question. State: " + str(state.values if state else "No state")
#             )
        
#         return StartInterviewResponse(
#             question=question,
#             status="waiting_for_answer"
#         )
        
#     except Exception as e:
#         print(f"Error in start_interview: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to start interview: {str(e)}"
#         )


# @app.post("/api/submit-answer", response_model=SubmitAnswerResponse)
# async def submit_answer(request: SubmitAnswerRequest):
#     """
#     Submit user's answer and get feedback
#     """
#     try:
#         config = {
#             "configurable": {
#                 "thread_id": request.thread_id
#             }
#         }
        
#         # Get current state
#         state_snapshot = workflow.get_state(config)
        
#         print("DEBUG - Current state snapshot:", state_snapshot.values if state_snapshot else "No state")
        
#         if not state_snapshot:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No active interview session found. Please start a new interview."
#             )
        
#         # Resume from interrupt with user's answer - use stream to get all updates
#         print(f"DEBUG - Resuming workflow with answer: {request.user_answer[:50]}...")
        
#         # Stream through all updates to ensure all nodes run
#         for event in workflow.stream(
#             {"user_answer": request.user_answer},
#             config=config
#         ):
#             print(f"DEBUG - Event: {event}")
        
#         # Get the final state after all nodes have executed
#         final_state = workflow.get_state(config)
#         state_values = final_state.values if final_state else {}
        
#         print("DEBUG - Final state values:", state_values)
        
#         # Extract evaluation results
#         score = state_values.get("score", 0)
#         strengths = state_values.get("strengths", "")
#         weakness = state_values.get("weakness", "")
#         final_response = state_values.get("final_response", "")
#         interview_status = state_values.get("interview_status", "continue")
        
#         print(f"DEBUG - Extracted: score={score}, status={interview_status}")
        
#         response_data = {
#             "score": score,
#             "strengths": strengths,
#             "weakness": weakness,
#             "final_response": final_response,
#             "status": interview_status
#         }
        
#         # If interview continues, include next question
#         if interview_status == "continue":
#             next_question = state_values.get("interview_question", "")
#             if next_question:
#                 response_data["next_question"] = next_question
        
#         return SubmitAnswerResponse(**response_data)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in submit_answer: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to process answer: {str(e)}"
#         )


# @app.get("/api/session/{thread_id}")
# async def get_session_state(thread_id: str):
#     """
#     Get the current state of an interview session
    
#     Args:
#         thread_id: Session identifier
    
#     Returns:
#         Current state of the interview
#     """
#     try:
#         config = {
#             "configurable": {
#                 "thread_id": thread_id
#             }
#         }
        
#         state = workflow.get_state(config)
        
#         if not state:
#             raise HTTPException(
#                 status_code=404,
#                 detail="Session not found"
#             )
        
#         return {
#             "thread_id": thread_id,
#             "state": state.values,
#             "next_node": state.next
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in get_session_state: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to retrieve session: {str(e)}"
#         )


# @app.delete("/api/session/{thread_id}")
# async def delete_session(thread_id: str):
#     """
#     Delete an interview session
    
#     Args:
#         thread_id: Session identifier
    
#     Returns:
#         Success message
#     """
#     try:
#         # Note: LangGraph doesn't have a direct delete method
#         # The session will naturally expire or be overwritten
#         return {
#             "message": f"Session {thread_id} marked for cleanup",
#             "thread_id": thread_id
#         }
        
#     except Exception as e:
#         print(f"Error in delete_session: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to delete session: {str(e)}"
#         )


# if __name__ == "__main__":
#     print("🚀 Starting AI Interview Platform API...")
#     print("📍 Server running on: http://localhost:8000")
#     print("📖 API docs available at: http://localhost:8000/docs")
    
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8000,
#         log_level="info"
#     )



# chalta hai
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional
# import uvicorn

# # Import your LangGraph workflow
# from main import workflow

# app = FastAPI(title="AI Interview Platform API")

# # Enable CORS for frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify your frontend domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Request/Response Models
# class StartInterviewRequest(BaseModel):
#     role: str
#     experience: str
#     thread_id: str


# class StartInterviewResponse(BaseModel):
#     question: str
#     status: str


# class SubmitAnswerRequest(BaseModel):
#     user_answer: str
#     thread_id: str


# class SubmitAnswerResponse(BaseModel):
#     score: int
#     strengths: str
#     weakness: str
#     final_response: str
#     next_question: Optional[str] = None
#     status: str  # continue, success, fail


# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {"status": "API is running", "message": "AI Interview Platform"}


# @app.post("/api/start-interview", response_model=StartInterviewResponse)
# async def start_interview(request: StartInterviewRequest):
#     """
#     Start a new interview session
    
#     Args:
#         role: The job role (Software Engineer, ML Engineer, etc.)
#         experience: Years of experience (0-2 years, 3-5 years, 5+ years)
#         thread_id: Unique session identifier
    
#     Returns:
#         First interview question
#     """
#     try:
#         # Initialize state
#         initial_state = {
#             "role": request.role,
#             "experience": request.experience,
#             "user_message": f"Interview for {request.role} with {request.experience} experience",
#             "attempt_count": 0
#         }
        
#         # Configuration with thread_id for checkpointing
#         config = {
#             "configurable": {
#                 "thread_id": request.thread_id
#             }
#         }
        
#         # Run workflow until first interrupt (ask_human)
#         # This will stop at ask_human node
#         result = workflow.invoke(initial_state, config=config)
        
#         print("DEBUG - Initial workflow result:", result)
        
#         # After interrupt, get the state to retrieve the question
#         state = workflow.get_state(config)
        
#         print("DEBUG - State after interrupt:", state.values if state else "No state")
        
#         # Extract the generated question from state
#         question = state.values.get("interview_question", "") if state else ""
        
#         if not question:
#             raise HTTPException(
#                 status_code=500,
#                 detail="Failed to generate interview question. State: " + str(state.values if state else "No state")
#             )
        
#         return StartInterviewResponse(
#             question=question,
#             status="waiting_for_answer"
#         )
        
#     except Exception as e:
#         print(f"Error in start_interview: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to start interview: {str(e)}"
#         )


# @app.post("/api/submit-answer", response_model=SubmitAnswerResponse)
# async def submit_answer(request: SubmitAnswerRequest):
#     """
#     Submit user's answer and get feedback
#     """
#     try:
#         config = {
#             "configurable": {
#                 "thread_id": request.thread_id
#             }
#         }
        
#         # Get current state
#         state_snapshot = workflow.get_state(config)
        
#         print("DEBUG - Current state snapshot:", state_snapshot.values if state_snapshot else "No state")
#         print(f"DEBUG - Current next nodes: {state_snapshot.next if state_snapshot else 'None'}")
        
#         if not state_snapshot:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No active interview session found. Please start a new interview."
#             )
        
#         # Update the state with user's answer - this resumes from the interrupt
#         print(f"DEBUG - Updating state with answer: {request.user_answer[:50]}...")
        
#         # Use update_state to properly resume from interrupt
#         workflow.update_state(
#             config,
#             {"user_answer": request.user_answer}
#         )
        
#         print("DEBUG - State updated, now streaming to execute evaluation nodes...")
        
#         # Now stream to execute the next set of nodes (scoring, evaluation)
#         for event in workflow.stream(None, config=config):
#             print(f"DEBUG - Event: {list(event.keys())}")
#             # Check if we hit another interrupt
#             if '__interrupt__' in event:
#                 print("DEBUG - Hit next interrupt (new question ready)")
#                 break
        
#         # Get the final state after all nodes have executed
#         final_state = workflow.get_state(config)
#         state_values = final_state.values if final_state else {}
        
#         print(f"DEBUG - Final state - Score: {state_values.get('score')}, Status: {state_values.get('interview_status')}")
        
#         # Extract evaluation results
#         score = state_values.get("score", 0)
#         strengths = state_values.get("strengths", "")
#         weakness = state_values.get("weakness", "")
#         final_response = state_values.get("final_response", "")
#         interview_status = state_values.get("interview_status", "continue")
        
#         response_data = {
#             "score": score,
#             "strengths": strengths,
#             "weakness": weakness,
#             "final_response": final_response,
#             "status": interview_status
#         }
        
#         # If interview continues, include next question
#         if interview_status == "continue":
#             next_question = state_values.get("interview_question", "")
#             if next_question:
#                 response_data["next_question"] = next_question
        
#         return SubmitAnswerResponse(**response_data)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in submit_answer: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to process answer: {str(e)}"
#         )


# @app.get("/api/session/{thread_id}")
# async def get_session_state(thread_id: str):
#     """
#     Get the current state of an interview session
    
#     Args:
#         thread_id: Session identifier
    
#     Returns:
#         Current state of the interview
#     """
#     try:
#         config = {
#             "configurable": {
#                 "thread_id": thread_id
#             }
#         }
        
#         state = workflow.get_state(config)
        
#         if not state:
#             raise HTTPException(
#                 status_code=404,
#                 detail="Session not found"
#             )
        
#         return {
#             "thread_id": thread_id,
#             "state": state.values,
#             "next_node": state.next
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in get_session_state: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to retrieve session: {str(e)}"
#         )


# @app.delete("/api/session/{thread_id}")
# async def delete_session(thread_id: str):
#     """
#     Delete an interview session
    
#     Args:
#         thread_id: Session identifier
    
#     Returns:
#         Success message
#     """
#     try:
#         # Note: LangGraph doesn't have a direct delete method
#         # The session will naturally expire or be overwritten
#         return {
#             "message": f"Session {thread_id} marked for cleanup",
#             "thread_id": thread_id
#         }
        
#     except Exception as e:
#         print(f"Error in delete_session: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to delete session: {str(e)}"
#         )


# if __name__ == "__main__":
#     print("🚀 Starting AI Interview Platform API...")
#     print("📍 Server running on: http://localhost:8000")
#     print("📖 API docs available at: http://localhost:8000/docs")
    
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8000,
#         log_level="info"
#     )


# working

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional
# import uvicorn

# from backend.services.technical_service import (
#     start_technical_interview,
#     submit_technical_answer
# )

# # Import your LangGraph workflow
# # from backend.workflows.technical_workflow import workflow



# app = FastAPI(title="AI Interview Platform API")


# # Enable CORS for frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify your frontend domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Request/Response Models
# class StartInterviewRequest(BaseModel):
#     role: str
#     experience: str
#     thread_id: str


# class StartInterviewResponse(BaseModel):
#     question: str
#     status: str


# class SubmitAnswerRequest(BaseModel):
#     user_answer: str
#     thread_id: str


# class SubmitAnswerResponse(BaseModel):
#     score: int
#     strengths: str
#     weakness: str
#     final_response: str
#     next_question: Optional[str] = None
#     status: str  # continue, success, fail


# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {"status": "API is running", "message": "AI Interview Platform"}


# @app.post("/api/start-interview", response_model=StartInterviewResponse)
# async def start_interview(request: StartInterviewRequest):
#     """
#     Start a new interview session
#     """
#     try:
#         initial_state = {
#             "role": request.role,
#             "experience": request.experience,
#             "user_message": f"Interview for {request.role} with {request.experience} experience",
#             "attempt_count": 0
#         }
        
#         config = {
#             "configurable": {
#                 "thread_id": request.thread_id
#             }
#         }
        
#         print(f"DEBUG - Starting interview for {request.role}, {request.experience}")
        
#         # Run workflow until first interrupt (ask_human)
#         result = workflow.invoke(initial_state, config=config)
        
#         # Get state after interrupt to retrieve the question
#         state = workflow.get_state(config)
        
#         question = state.values.get("interview_question", "") if state else ""
        
#         if not question:
#             raise HTTPException(
#                 status_code=500,
#                 detail="Failed to generate interview question"
#             )
        
#         print(f"DEBUG - First question generated: {question[:50]}...")
        
#         return StartInterviewResponse(
#             question=question,
#             status="waiting_for_answer"
#         )
        
#     except Exception as e:
#         print(f"Error in start_interview: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to start interview: {str(e)}"
#         )


# @app.post("/api/submit-answer", response_model=SubmitAnswerResponse)
# async def submit_answer(request: SubmitAnswerRequest):
#     """
#     Submit user's answer and get feedback
#     """
#     try:
#         config = {
#             "configurable": {
#                 "thread_id": request.thread_id
#             }
#         }
        
#         # Get current state
#         state_snapshot = workflow.get_state(config)
        
#         if not state_snapshot:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No active interview session found. Please start a new interview."
#             )
        
#         print(f"DEBUG - Submitting answer: {request.user_answer[:50]}...")
#         print(f"DEBUG - Current next nodes: {state_snapshot.next}")
        
#         # Update the state with user's answer - specify as_node='ask_human'
#         workflow.update_state(
#             config,
#             {"user_answer": request.user_answer},
#             as_node="ask_human"
#         )
        
#         print("DEBUG - State updated, now streaming to execute evaluation nodes...")
        
#         # Now stream to execute the next set of nodes (scoring, evaluation)
#         event_count = 0
#         for event in workflow.stream(None, config=config):
#             event_count += 1
#             event_keys = list(event.keys())
#             print(f"DEBUG - Event {event_count}: {event_keys}")
            
#             # Check if we hit another interrupt
#             if '__interrupt__' in event:
#                 print("DEBUG - Hit next interrupt (new question ready)")
#                 break
        
#         # Get the final state after all nodes have executed
#         final_state = workflow.get_state(config)
#         state_values = final_state.values if final_state else {}
        
#         # Extract evaluation results
#         score = state_values.get("score", 0)
#         strengths = state_values.get("strengths", "")
#         weakness = state_values.get("weakness", "")
#         final_response = state_values.get("final_response", "")
#         interview_status = state_values.get("interview_status", "continue")
        
#         print(f"DEBUG - Results: score={score}, status={interview_status}")
        
#         response_data = {
#             "score": score,
#             "strengths": strengths,
#             "weakness": weakness,
#             "final_response": final_response,
#             "status": interview_status
#         }
        
#         # If interview continues, include next question
#         if interview_status == "continue":
#             next_question = state_values.get("interview_question", "")
#             if next_question:
#                 response_data["next_question"] = next_question
#                 print(f"DEBUG - Next question: {next_question[:50]}...")
        
#         return SubmitAnswerResponse(**response_data)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in submit_answer: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to process answer: {str(e)}"
#         )


# @app.get("/api/session/{thread_id}")
# async def get_session_state(thread_id: str):
#     """
#     Get the current state of an interview session
#     """
#     try:
#         config = {
#             "configurable": {
#                 "thread_id": thread_id
#             }
#         }
        
#         state = workflow.get_state(config)
        
#         if not state:
#             raise HTTPException(
#                 status_code=404,
#                 detail="Session not found"
#             )
        
#         return {
#             "thread_id": thread_id,
#             "state": state.values,
#             "next_node": state.next
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error in get_session_state: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to retrieve session: {str(e)}"
#         )


# @app.delete("/api/session/{thread_id}")
# async def delete_session(thread_id: str):
#     """
#     Delete an interview session
#     """
#     try:
#         return {
#             "message": f"Session {thread_id} marked for cleanup",
#             "thread_id": thread_id
#         }
        
#     except Exception as e:
#         print(f"Error in delete_session: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to delete session: {str(e)}"
#         )


# if __name__ == "__main__":
#     print("🚀 Starting AI Interview Platform API...")
#     print("📍 Server running on: http://localhost:8000")
#     print("📖 API docs available at: http://localhost:8000/docs")
    
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8000,
#         log_level="info"
#     )



from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from backend.workflows.technical_workflow import workflow

from backend.services.technical_service import (
    start_technical_interview,
    submit_technical_answer
)

# Import your LangGraph workflow
# from backend.workflows.technical_workflow import workflow



app = FastAPI(title="AI Interview Platform API")


# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class StartInterviewRequest(BaseModel):
    role: str
    experience: str
    thread_id: str


class StartInterviewResponse(BaseModel):
    question: str
    status: str


class SubmitAnswerRequest(BaseModel):
    user_answer: str
    thread_id: str


class SubmitAnswerResponse(BaseModel):
    score: int
    strengths: str
    weakness: str
    final_response: str
    next_question: Optional[str] = None
    status: str  # continue, success, fail


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "API is running", "message": "AI Interview Platform"}


@app.post("/api/start-interview", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new interview session
    """
    try:
        initial_state = {
            "role": request.role,
            "experience": request.experience,
            "user_message": f"Interview for {request.role} with {request.experience} experience",
            "attempt_count": 0
        }
        
        config = {
            "configurable": {
                "thread_id": request.thread_id
            }
        }
        
        print(f"DEBUG - Starting interview for {request.role}, {request.experience}")
        
        # Run workflow until first interrupt (ask_human)
        result = workflow.invoke(initial_state, config=config)
        
        # Get state after interrupt to retrieve the question
        state = workflow.get_state(config)
        
        question = state.values.get("interview_question", "") if state else ""
        
        if not question:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate interview question"
            )
        
        print(f"DEBUG - First question generated: {question[:50]}...")
        
        return StartInterviewResponse(
            question=question,
            status="waiting_for_answer"
        )
        
    except Exception as e:
        print(f"Error in start_interview: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start interview: {str(e)}"
        )


@app.post("/api/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit user's answer and get feedback
    """
    try:
        config = {
            "configurable": {
                "thread_id": request.thread_id
            }
        }
        
        # Get current state
        state_snapshot = workflow.get_state(config)
        
        if not state_snapshot:
            raise HTTPException(
                status_code=400,
                detail="No active interview session found. Please start a new interview."
            )
        
        print(f"DEBUG - Submitting answer: {request.user_answer[:50]}...")
        print(f"DEBUG - Current next nodes: {state_snapshot.next}")
        
        # Update the state with user's answer - specify as_node='ask_human'
        workflow.update_state(
            config,
            {"user_answer": request.user_answer},
            as_node="ask_human"
        )
        
        print("DEBUG - State updated, now streaming to execute evaluation nodes...")
        
        # Now stream to execute the next set of nodes (scoring, evaluation)
        event_count = 0
        for event in workflow.stream(None, config=config):
            event_count += 1
            event_keys = list(event.keys())
            print(f"DEBUG - Event {event_count}: {event_keys}")
            
            # Check if we hit another interrupt
            if '__interrupt__' in event:
                print("DEBUG - Hit next interrupt (new question ready)")
                break
        
        # Get the final state after all nodes have executed
        final_state = workflow.get_state(config)
        state_values = final_state.values if final_state else {}
        
        # Extract evaluation results
        score = state_values.get("score", 0)
        strengths = state_values.get("strengths", "")
        weakness = state_values.get("weakness", "")
        final_response = state_values.get("final_response", "")
        interview_status = state_values.get("interview_status", "continue")
        
        print(f"DEBUG - Results: score={score}, status={interview_status}")
        
        response_data = {
            "score": score,
            "strengths": strengths,
            "weakness": weakness,
            "final_response": final_response,
            "status": interview_status
        }
        
        # If interview continues, include next question
        if interview_status == "continue":
            next_question = state_values.get("interview_question", "")
            if next_question:
                response_data["next_question"] = next_question
                print(f"DEBUG - Next question: {next_question[:50]}...")
        
        return SubmitAnswerResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in submit_answer: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answer: {str(e)}"
        )


@app.get("/api/session/{thread_id}")
async def get_session_state(thread_id: str):
    """
    Get the current state of an interview session
    """
    try:
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
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_session_state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@app.delete("/api/session/{thread_id}")
async def delete_session(thread_id: str):
    """
    Delete an interview session
    """
    try:
        return {
            "message": f"Session {thread_id} marked for cleanup",
            "thread_id": thread_id
        }
        
    except Exception as e:
        print(f"Error in delete_session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


if __name__ == "__main__":
    print("🚀 Starting AI Interview Platform API...")
    print("📍 Server running on: http://localhost:8000")
    print("📖 API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )