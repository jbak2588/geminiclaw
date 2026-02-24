from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.worker import worker_node
from agents.reviewer import reviewer_node

def create_team_graph():
    """
    Creates and compiles the LangGraph workflow for the agentic team.
    """
    # 1. Initialize the graph with our state schema
    workflow = StateGraph(AgentState)
    
    # 2. Add nodes (the agents)
    workflow.add_node("worker", worker_node)
    workflow.add_node("reviewer", reviewer_node)
    
    # 3. Define the edges (the flow)
    # Start -> Worker
    workflow.set_entry_point("worker")
    
    # Worker -> Conditional Edge: if error or awaiting_approval, go to END; otherwise, go to reviewer
    def check_worker_status(state: AgentState) -> str:
        status = state.get("status", "")
        if status == "error":
            return "error"
        if status == "awaiting_approval":
            return "awaiting_approval"
        return "continue"
    
    workflow.add_conditional_edges(
        "worker",
        check_worker_status,
        {
            "error": END,
            "awaiting_approval": END,
            "continue": "reviewer"
        }
    )
    
    # Reviewer -> Conditional Edge based on status
    def check_review_status(state: AgentState) -> str:
        status = state.get("status", "")
        if status == "approved":
            return "approved"
        elif status == "error":
            return "error"
        else:
            return "rejected"
            
    workflow.add_conditional_edges(
        "reviewer",
        check_review_status,
        {
            "approved": END,
            "error": END,
            "rejected": "worker" # Send back to worker with feedback
        }
    )
    
    # 4. Compile the graph
    app = workflow.compile()
    
    return app

# Expose a compiled instance
team_graph = create_team_graph()
