from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from core.config import settings

def worker_node(state: AgentState) -> Dict[str, Any]:
    """
    Worker Agent Node: Processes the task and makes code changes.
    """
    current_task = state.get("current_task", "")
    reviewer_feedback = state.get("reviewer_feedback", "")
    
    prompt = f"You are a skilled Software Engineering Worker Agent.\nYour current task is: {current_task}\n"
    
    if reviewer_feedback:
        prompt += f"\nYour previous work was rejected. The Reviewer Agent provided this feedback:\n{reviewer_feedback}\n\nPlease fix the issues."
    else:
        prompt += "\nPlease provide the implementation details or the solution."
        
    try:
        # Requires a valid API key in .env or environment
        if not settings.GEMINI_API_KEY:
             raise ValueError("GEMINI_API_KEY is missing or empty. Please check your .env file.")
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", api_key=settings.GEMINI_API_KEY)
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
    except Exception as e:
        content = f"Error calling LLM: {str(e)}"
        # Return error status so the graph stops instead of looping
        return {
            "messages": [AIMessage(content=f"[Worker]:\n{content}")],
            "status": "error",
            "reviewer_feedback": ""
        }
    
    return {
        "messages": [AIMessage(content=f"[Worker]:\n{content}")],
        "status": "needs_review",
        "reviewer_feedback": "" # Clear feedback after attempting a fix
    }
