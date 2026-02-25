from typing import Annotated, Sequence, TypedDict, Dict, List
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The state of the entire agentic team workflow.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_task: str           # The original CTO instruction
    status: str                 # Current workflow status
    reviewer_feedback: str      # Feedback from the reviewer (if rejected)
    pending_command: str        # Command awaiting CTO approval (HITL)
    team_config: List[Dict]     # List of agent configs from frontend
    sub_tasks: Dict[str, str]   # PM-assigned tasks: {"agent_name": "task"}
    agent_order: List[str]      # Ordered list of agents to execute sequentially
    current_agent_index: int    # Index into agent_order for sequential execution
    kanban_tasks: List[Dict]    # Kanban board state: [{id, agent, task, status, emoji}]
    project_id: str             # Project ID for dynamic skill manual resolution
