"""
PM Agent: Analyzes CTO instructions and routes sub-tasks to team members.
"""
import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from core.config import settings


def pm_node(state: AgentState) -> Dict[str, Any]:
    """
    PM Agent: Takes CTO's instruction, analyzes it, and creates sub-tasks
    for the available team members.
    """
    current_task = state.get("current_task", "")
    team_config = state.get("team_config", [])
    
    # Get team member names (exclude pm and reviewer)
    team_members = [m["name"] for m in team_config if m["name"] not in ("pm", "reviewer")]
    
    if not team_members:
        # No team members, just pass task through to default worker
        return {
            "messages": [AIMessage(content="[PM]: No team members configured. Passing task directly.")],
            "sub_tasks": {"developer": current_task},
            "agent_order": ["developer"],
            "current_agent_index": 0,
            "status": "pm_routed",
            "reviewer_feedback": "",
            "pending_command": "",
        }
    
    prompt = (
        f"You are a PM Agent. Analyze the following task and assign sub-tasks to available team members.\n\n"
        f"Available team members: {', '.join(team_members)}\n\n"
        f"CTO's instruction: {current_task}\n\n"
        f"RULES:\n"
        f"1. Output ONLY a valid JSON object mapping agent names to their tasks.\n"
        f"2. Only assign to agents in the available list above.\n"
        f"3. Each task should be a clear, actionable instruction.\n"
        f"4. If only one agent fits, assign the full task to that agent.\n\n"
        f'Example output: {{"developer": "Create hello.txt with current date", "legal": "Draft privacy policy"}}\n'
    )
    
    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing.")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY,
            max_output_tokens=512,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # Parse JSON from response (handle markdown code blocks)
        json_str = content
        if "```" in json_str:
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            json_str = json_str.strip()
        
        sub_tasks = json.loads(json_str)
        
        # Validate: only keep tasks for existing team members
        valid_tasks = {k: v for k, v in sub_tasks.items() if k in team_members}
        
        if not valid_tasks:
            # Fallback: assign to first team member
            valid_tasks = {team_members[0]: current_task}
        
        summary = "\n".join([f"  → {name}: {task}" for name, task in valid_tasks.items()])
        
        return {
            "messages": [AIMessage(content=f"[PM]: 태스크 분배 완료:\n{summary}")],
            "sub_tasks": valid_tasks,
            "agent_order": list(valid_tasks.keys()),
            "current_agent_index": 0,
            "status": "pm_routed",
            "reviewer_feedback": "",
            "pending_command": "",
        }
        
    except json.JSONDecodeError:
        # If JSON parsing fails, assign everything to first team member
        return {
            "messages": [AIMessage(content=f"[PM]: JSON 파싱 실패. {team_members[0]}에게 전체 태스크 할당.\nRaw: {content}")],
            "sub_tasks": {team_members[0]: current_task},
            "agent_order": [team_members[0]],
            "current_agent_index": 0,
            "status": "pm_routed",
            "reviewer_feedback": "",
            "pending_command": "",
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"[PM]: Error - {str(e)}")],
            "status": "error",
            "reviewer_feedback": "",
            "pending_command": "",
        }
