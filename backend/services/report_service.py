import json
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.db.database import save_report

model = ChatGoogleGenerativeAI(model='models/gemini-2.5-flash')

def generate_interview_report(session_id: str, state_values: dict, interview_type: str):
    """
    Generate a highly structured JSON report and save it to the DB.
    """
    prompt = f"""You are an expert technical recruiter analyzing an interview session.
Interview Type: {interview_type}
Candidate Final Score/Feedback Log: {state_values}

Generate a final strict JSON report containing ONLY this structure, no markdown boundaries just raw parsable JSON:
{{
  "overall_score": 8.2,
  "per_question_scores": [],
  "strengths": ["string", "string"],
  "weaknesses": ["string"],
  "communication_score": 7.5,
  "technical_score": 8.5,
  "confidence_score": 7.0,
  "improvement_suggestions": ["string"],
  "model_answer_comparison": ["string"],
  "readiness_level": "Interview Ready"
}}"""

    response = model.invoke(prompt)
    json_str = response.content.strip()
    
    # Clean up MD formatting if it leaked
    if json_str.startswith("```json"):
        json_str = json_str[7:-3]
    elif json_str.startswith("```"):
        json_str = json_str[3:-3]
        
    try:
        report_data = json.loads(json_str)
    except:
        # Fallback to empty shell to not break if Gemini hallucinates
        report_data = {
          "overall_score": 0.0,
          "per_question_scores": [],
          "strengths": ["Failed to parse AI format"],
          "weaknesses": ["Failed to parse AI format"],
          "communication_score": 0.0,
          "technical_score": 0.0,
          "confidence_score": 0.0,
          "improvement_suggestions": [],
          "model_answer_comparison": [],
          "readiness_level": "Needs Improvement"
        }
        
    # Save into SQLite DB
    save_report(session_id, report_data)
    
    return report_data
