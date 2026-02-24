"""
Dynamic Graph Builder: Creates LangGraph workflow based on team configuration.

Flow: PM → Agent1 → Reviewer → Agent2 → Reviewer → ... → END
"""
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.pm_agent import pm_node
from agents.agent_config import AgentConfig, AVAILABLE_ROLES
from agents.agent_factory import create_agent_node


def create_dynamic_graph(team_config: list):
    """
    Creates a LangGraph workflow dynamically based on team configuration.
    Supports sequential execution: PM assigns tasks, then agents execute
    one-by-one with reviewer between each.
    
    Flow: PM → worker → reviewer → (approved → next worker | rejected → same worker) → ... → END
    
    Args:
        team_config: List of dicts, e.g.:
            [{"name": "developer", "knowledge_dir": ""}, {"name": "legal"}]
    """
    workflow = StateGraph(AgentState)
    
    # ─────────────────────────────────────────────
    # 1. Always add PM node
    # ─────────────────────────────────────────────
    workflow.add_node("pm", pm_node)
    workflow.set_entry_point("pm")
    
    # ─────────────────────────────────────────────
    # 2. Build agent nodes from team config
    # ─────────────────────────────────────────────
    agent_names = []
    for member in team_config:
        name = member.get("name", "")
        if name in ("pm", "reviewer") or name not in AVAILABLE_ROLES:
            continue
        
        # Create config from template, applying custom knowledge_dir
        base_config = AVAILABLE_ROLES[name]
        config = AgentConfig(
            name=base_config.name,
            role=base_config.role,
            system_prompt=base_config.system_prompt,
            tools=base_config.tools,
            knowledge_dir=member.get("knowledge_dir", ""),
        )
        
        node_fn = create_agent_node(config)
        workflow.add_node(name, node_fn)
        agent_names.append(name)
    
    # If no agents, add default developer
    if not agent_names:
        default_config = AVAILABLE_ROLES["developer"]
        workflow.add_node("developer", create_agent_node(default_config))
        agent_names = ["developer"]
    
    # ─────────────────────────────────────────────
    # 3. Add reviewer node
    # ─────────────────────────────────────────────
    reviewer_config = AVAILABLE_ROLES["reviewer"]
    workflow.add_node("reviewer", create_agent_node(reviewer_config))
    
    # ─────────────────────────────────────────────
    # 4. Add dispatcher node (routes to next agent)
    # ─────────────────────────────────────────────
    def dispatcher_node(state: AgentState):
        """Advances current_agent_index and routes to next agent."""
        idx = state.get("current_agent_index", 0)
        return {
            "current_agent_index": idx + 1,
            "status": "dispatching",
        }
    
    workflow.add_node("dispatcher", dispatcher_node)
    
    # ─────────────────────────────────────────────
    # 5. Wire edges
    # ─────────────────────────────────────────────
    
    # PM → dispatcher (to start sequential execution)
    def check_pm_status(state: AgentState) -> str:
        status = state.get("status", "")
        if status == "error":
            return "error"
        return "continue"
    
    workflow.add_conditional_edges(
        "pm",
        check_pm_status,
        {"error": END, "continue": "dispatcher"}
    )
    
    # Dispatcher → correct agent based on current_agent_index
    def route_to_agent(state: AgentState) -> str:
        agent_order = state.get("agent_order", agent_names)
        idx = state.get("current_agent_index", 0)
        if idx < len(agent_order):
            target = agent_order[idx]
            # Only route to agents that actually exist in this graph
            if target in agent_names:
                return target
        return "__done__"
    
    dispatch_routes = {name: name for name in agent_names}
    dispatch_routes["__done__"] = END
    
    workflow.add_conditional_edges(
        "dispatcher",
        route_to_agent,
        dispatch_routes
    )
    
    # Each agent → reviewer (with error/HITL checks)
    for agent_name in agent_names:
        def make_check(name):
            def check_agent_status(state: AgentState) -> str:
                status = state.get("status", "")
                if status == "error":
                    return "error"
                if status == "awaiting_approval":
                    return "awaiting_approval"
                return "continue"
            return check_agent_status
        
        workflow.add_conditional_edges(
            agent_name,
            make_check(agent_name),
            {"error": END, "awaiting_approval": END, "continue": "reviewer"}
        )
    
    # Reviewer → dispatcher (approved → next agent) or back to current agent (rejected)
    MAX_RETRIES = 2  # Max times reviewer can reject before forcing next
    
    def check_review_status(state: AgentState) -> str:
        status = state.get("status", "")
        if status == "approved":
            return "approved"
        elif status == "error":
            return "error"
        else:
            # Rejected — go back to current agent (but with feedback)
            return "rejected"
    
    def get_reject_target(state: AgentState) -> str:
        """Get the agent to send back to on rejection."""
        agent_order = state.get("agent_order", agent_names)
        idx = state.get("current_agent_index", 0)
        if idx < len(agent_order):
            target = agent_order[idx]
            if target in agent_names:
                return target
        return agent_names[0]
    
    # Build rejection routes
    reject_routes = {name: name for name in agent_names}
    
    # For reviewer: approved → dispatcher (next agent), rejected → current agent
    # We need conditional edges that can determine the reject target dynamically
    def review_router(state: AgentState) -> str:
        status = state.get("status", "")
        if status == "approved":
            return "dispatcher"
        elif status == "error":
            return "__end__"
        else:
            # Rejected: route back to current agent
            agent_order = state.get("agent_order", agent_names)
            idx = state.get("current_agent_index", 0)
            if idx < len(agent_order):
                target = agent_order[idx]
                if target in agent_names:
                    return target
            # Fallback: just move to next
            return "dispatcher"
    
    review_routes = {"dispatcher": "dispatcher", "__end__": END}
    review_routes.update({name: name for name in agent_names})
    
    workflow.add_conditional_edges(
        "reviewer",
        review_router,
        review_routes
    )
    
    # ─────────────────────────────────────────────
    # 6. Compile
    # ─────────────────────────────────────────────
    return workflow.compile()


# Default graph for backward compatibility (2-agent team)
team_graph = create_dynamic_graph([{"name": "developer"}])
