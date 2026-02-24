from typing import Annotated, Sequence, TypedDict
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The state of the entire agentic team workflow.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_task: str
    reviewer_feedback: str
    status: str # "in_progress", "needs_review", "approved", "rejected"
