from backend.workflows.technical_workflow import workflow


# ── Start Technical Interview ───────────────────────────────────

def start_technical_interview(role: str, experience: str, thread_id: str):
    try:
        initial_state = {
            "role": role,
            "experience": experience,
            "user_message": f"Interview for {role} with {experience} experience",
            "attempt_count": 0
        }

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Run workflow until first interrupt
        workflow.invoke(initial_state, config=config)

        state = workflow.get_state(config)

        question = state.values.get("interview_question", "") if state else ""

        return question

    except Exception as e:
        raise Exception(f"Service Error (start interview): {str(e)}")


# ── Submit Answer ───────────────────────────────────────────────

def submit_technical_answer(thread_id: str, user_answer: str):
    try:
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Check session
        state_snapshot = workflow.get_state(config)

        if not state_snapshot:
            raise Exception("No active interview session")

        # Update state with user's answer
        workflow.update_state(
            config,
            {"user_answer": user_answer},
            as_node="ask_human"
        )

        # Execute next nodes
        for event in workflow.stream(None, config=config):
            if "__interrupt__" in event:
                break

        # Get final state
        final_state = workflow.get_state(config)
        state_values = final_state.values if final_state else {}

        return {
            "score": state_values.get("score", 0),
            "strengths": state_values.get("strengths", ""),
            "weakness": state_values.get("weakness", ""),
            "final_response": state_values.get("final_response", ""),
            "next_question": state_values.get("interview_question", ""),
            "status": state_values.get("interview_status", "continue")
        }

    except Exception as e:
        raise Exception(f"Service Error (submit answer): {str(e)}")