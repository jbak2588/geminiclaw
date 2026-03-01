from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from core.config import settings

def reviewer_node(state: AgentState) -> Dict[str, Any]:
    """
    Reviewer Agent Node: Evaluates the worker's work and decides whether to approve or reject.
    """
    current_task = state.get("current_task", "")
    
    # Get the last message, assuming it's from the worker
    if state.get("messages") and len(state.get("messages", [])) > 0:
        last_worker_msg = state["messages"][-1].content
    else:
        last_worker_msg = "No work found."
    
    prompt = (
        f"You are a QA/Reviewer Agent. Be LENIENT and BRIEF.\n"
        f"Task: {current_task}\n"
        f"Worker's submission:\n{last_worker_msg}\n\n"
        f"If the work reasonably addresses the task, reply ONLY with 'APPROVED'.\n"
        f"Only reject if there are critical errors. If rejecting, give ONE sentence of feedback.\n"
    )
    try:
        if not settings.GEMINI_API_KEY:
             raise ValueError("GEMINI_API_KEY is missing or empty. Please check your .env file.")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY,
            max_output_tokens=256,  # Reviewer needs very short responses
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
    except Exception as e:
        # Return error status so the graph stops instead of looping
        return {
            "messages": [AIMessage(content=f"[Reviewer]: Error during review: {str(e)}")],
            "status": "error",
            "reviewer_feedback": ""
        }
    
    is_approved = content.upper().startswith("APPROVED")
    
    if is_approved:
        return {
            "messages": [AIMessage(content="[Reviewer]: work approved. Moving forward.")],
            "status": "approved",
            "reviewer_feedback": ""
        }
    else:
        return {
            "messages": [AIMessage(content=f"[Reviewer]: work rejected. Feedback: {content}")],
            "status": "rejected",
            "reviewer_feedback": content
        }
