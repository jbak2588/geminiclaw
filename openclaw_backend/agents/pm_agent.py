"""
PM Agent: Analyzes CTO instructions and routes sub-tasks to team members.
"""
import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from core.config import settings

# ── 에이전트별 이모지 매핑 ──
AGENT_EMOJI = {
    "pm": "👔",
    "developer": "💻",
    "reviewer": "✅",
    "legal": "⚖️",
    "marketer": "📢",
    "accountant": "💰",
    "admin": "🏛️",
    "cs": "🎧",
    "hr": "👤",
}


def _build_kanban_tasks(sub_tasks: dict, agent_order: list) -> list:
    """PM이 분배한 sub_tasks를 기반으로 칸반 태스크 리스트 생성 (초기 상태: todo)."""
    tasks = []
    for i, agent_name in enumerate(agent_order):
        task_desc = sub_tasks.get(agent_name, "태스크 실행")
        tasks.append({
            "id": f"{agent_name}_{i}",
            "agent": agent_name,
            "task": task_desc,
            "status": "todo",
            "emoji": AGENT_EMOJI.get(agent_name, "📋"),
        })
    return tasks


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
        default_tasks = {"developer": current_task}
        default_order = ["developer"]
        return {
            "messages": [AIMessage(content="[PM]: No team members configured. Passing task directly.")],
            "sub_tasks": default_tasks,
            "agent_order": default_order,
            "current_agent_index": 0,
            "status": "pm_routed",
            "reviewer_feedback": "",
            "pending_command": "",
            "kanban_tasks": _build_kanban_tasks(default_tasks, default_order),
        }

    system_prompt = (
        "You are a PM Agent. Your job is to analyze the CTO's instruction "
        "and assign sub-tasks to available team members.\n"
        "RULES:\n"
        "1. Output ONLY a valid JSON object mapping agent names to their tasks.\n"
        "2. Only assign to agents in the available list.\n"
        "3. Each task should be a clear, actionable instruction.\n"
        "4. If only one agent fits, assign the full task to that agent.\n\n"
        'Example output: {"developer": "Create hello.txt with current date", "legal": "Draft privacy policy"}\n'
    )
    user_prompt = (
        f"Available team members: {', '.join(team_members)}\n\n"
        f"CTO's instruction: {current_task}\n"
    )

    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing.")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY,
            max_output_tokens=512,
        )
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
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

        agent_order = list(valid_tasks.keys())
        summary = "\n".join([f"  → {name}: {task}" for name, task in valid_tasks.items()])

        return {
            "messages": [AIMessage(content=f"[PM]: 태스크 분배 완료:\n{summary}")],
            "sub_tasks": valid_tasks,
            "agent_order": agent_order,
            "current_agent_index": 0,
            "status": "pm_routed",
            "reviewer_feedback": "",
            "pending_command": "",
            "kanban_tasks": _build_kanban_tasks(valid_tasks, agent_order),
        }

    except json.JSONDecodeError:
        # If JSON parsing fails, assign everything to first team member
        fallback_tasks = {team_members[0]: current_task}
        fallback_order = [team_members[0]]
        return {
            "messages": [AIMessage(content=f"[PM]: JSON 파싱 실패. {team_members[0]}에게 전체 태스크 할당.\nRaw: {content}")],
            "sub_tasks": fallback_tasks,
            "agent_order": fallback_order,
            "current_agent_index": 0,
            "status": "pm_routed",
            "reviewer_feedback": "",
            "pending_command": "",
            "kanban_tasks": _build_kanban_tasks(fallback_tasks, fallback_order),
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"[PM]: Error - {str(e)}")],
            "status": "error",
            "reviewer_feedback": "",
            "pending_command": "",
        }
