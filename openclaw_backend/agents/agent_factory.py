"""
Agent Factory: Dynamically creates LangGraph node functions from AgentConfig.
"""
import os
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from agents.agent_config import AgentConfig, COMPANY_CONTEXT, AGENTS_CONTEXT
from core.config import settings
from tools.file_tools import read_file, write_file
from tools.shell_tools import execute_shell_command

# Tool registry
TOOL_REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
    "execute_shell_command": execute_shell_command,
}


def _load_knowledge(project_id: str) -> str:
    """Load matching text/md files from the project's knowledge directory."""
    knowledge_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "knowledge", project_id)
    if not project_id or not os.path.isdir(knowledge_dir):
        return ""
    
    context_parts = []
    for filename in os.listdir(knowledge_dir):
        filepath = os.path.join(knowledge_dir, filename)
        if os.path.isfile(filepath) and filename.endswith(('.md', '.txt', '.json')):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()[:3000]  # Limit per file to save tokens
                context_parts.append(f"--- {filename} ---\n{content}")
            except Exception:
                pass
    
    if context_parts:
        return "\n\n[Reference Documents]\n" + "\n\n".join(context_parts[:5])  # Max 5 files
    return ""


def _execute_tool(tool_name: str, tool_args: dict, available_tools: list) -> str:
    """Execute a tool by name."""
    tool_map = {t.name: t for t in available_tools}
    if tool_name not in tool_map:
        return f"Error: Tool '{tool_name}' not available for this agent."
    try:
        result = tool_map[tool_name].invoke(tool_args)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"


def create_agent_node(config: AgentConfig):
    """
    Factory function: creates a LangGraph node function for a given AgentConfig.
    Returns a callable that takes AgentState and returns updated state.
    """
    # Resolve available tools for this agent
    agent_tools = [TOOL_REGISTRY[t] for t in config.tools if t in TOOL_REGISTRY]
    is_reviewer = config.name == "reviewer"
    
    def agent_node(state: AgentState) -> Dict[str, Any]:
        # Get the sub-task assigned to this agent (or the main task)
        sub_tasks = state.get("sub_tasks", {})
        current_task = sub_tasks.get(config.name, state.get("current_task", ""))
        reviewer_feedback = state.get("reviewer_feedback", "")
        
        # 1. Load dynamic project knowledge
        project_id = state.get("project_id", "default")
        knowledge_context = _load_knowledge(project_id)
        
        # 2. Load dynamic skill manual if available
        dynamic_skill_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "storage", "skills", project_id, f"{config.name}_manual.md"
        )
        system_prompt = config.system_prompt
        if os.path.exists(dynamic_skill_path):
            try:
                with open(dynamic_skill_path, "r", encoding="utf-8") as f:
                    system_prompt = f.read().strip()
            except Exception:
                pass

        if AGENTS_CONTEXT:
            system_prompt += "\n\n" + AGENTS_CONTEXT
        system_prompt += "\n\n" + COMPANY_CONTEXT
        if knowledge_context:
            system_prompt += f"\n\n{knowledge_context}\n"
        
        user_prompt = f"Task: {current_task}\n"
        if reviewer_feedback:
            user_prompt += f"\nReviewer feedback:\n{reviewer_feedback}\n"
        
        # For reviewer: include the last agent's response
        if is_reviewer:
            messages_list = state.get("messages", [])
            if messages_list:
                last_msg = messages_list[-1]
                last_content = getattr(last_msg, 'content', str(last_msg))
                user_prompt += f"\n--- Agent's work to review ---\n{last_content}\n"
        
        try:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is missing.")
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                api_key=settings.GEMINI_API_KEY,
                max_output_tokens=1024,
            )
            
            messages = [
                HumanMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            
            if agent_tools:
                llm_with_tools = llm.bind_tools(agent_tools)
                response = llm_with_tools.invoke(messages)
                
                # Handle tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    tool_results = []
                    messages.append(response)
                    
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        tool_result = _execute_tool(tool_name, tool_args, agent_tools)
                        
                        # HITL check
                        if "APPROVAL_REQUIRED" in tool_result:
                            pending_cmd = tool_args.get("command", str(tool_args))
                            return {
                                "messages": [AIMessage(content=f"[{config.role}]:\n⚠️ HITL: 위험 명령 감지됨 - CTO 승인 대기 중\n명령어: {pending_cmd}\n사유: {tool_result}")],
                                "status": "awaiting_approval",
                                "reviewer_feedback": "",
                                "pending_command": pending_cmd,
                            }
                        
                        tool_results.append(f"[{tool_name}]: {tool_result}")
                        messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call["id"]))
                    
                    final_response = llm_with_tools.invoke(messages)
                    content = final_response.content or ""
                    tool_summary = "\n".join(tool_results)
                    content = f"Tool Results:\n{tool_summary}\n\nSummary: {content}"
                else:
                    content = response.content or ""
            else:
                # No tools (e.g., reviewer)
                response = llm.invoke(messages)
                content = response.content or ""
                
        except Exception as e:
            content = f"Error: {str(e)}"
            return {
                "messages": [AIMessage(content=f"[{config.role}]:\n{content}")],
                "status": "error",
                "reviewer_feedback": "",
                "pending_command": "",
            }
        
        # ─────────────────────────────────────────────
        # REVIEWER: Parse response to determine approved/rejected
        # ─────────────────────────────────────────────
        if is_reviewer:
            content_upper = content.upper().strip()
            if "APPROVED" in content_upper:
                return {
                    "messages": [AIMessage(content=f"[{config.role}]:\n{content}")],
                    "status": "approved",
                    "reviewer_feedback": "",
                    "pending_command": "",
                }
            else:
                # Reviewer rejected — pass feedback back
                return {
                    "messages": [AIMessage(content=f"[{config.role}]:\n{content}")],
                    "status": "rejected",
                    "reviewer_feedback": content,
                    "pending_command": "",
                }
        
        # ─────────────────────────────────────────────
        # NORMAL AGENT: always needs_review
        # ─────────────────────────────────────────────
        return {
            "messages": [AIMessage(content=f"[{config.role}]:\n{content}")],
            "status": "needs_review",
            "reviewer_feedback": "",
            "pending_command": "",
        }
    
    return agent_node
