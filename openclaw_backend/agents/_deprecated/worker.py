from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState
from core.config import settings
from tools.file_tools import read_file, write_file
from tools.shell_tools import execute_shell_command

# Register all available tools
TOOLS = [read_file, write_file, execute_shell_command]

def worker_node(state: AgentState) -> Dict[str, Any]:
    """
    Worker Agent Node: Processes tasks using LLM + Tool execution.
    The LLM decides which tools to call, and we execute them.
    """
    current_task = state.get("current_task", "")
    reviewer_feedback = state.get("reviewer_feedback", "")
    
    system_prompt = (
        "You are a concise Software Engineering Worker Agent with access to real tools.\n"
        "IMPORTANT RULES:\n"
        "1. Use the provided tools to ACTUALLY perform tasks (create files, run commands).\n"
        "2. Be BRIEF. No tutorials or lengthy explanations.\n"
        "3. If the task requires creating a file, USE the write_file tool.\n"
        "4. If the task requires running a command, USE the execute_shell_command tool.\n"
        "5. After using tools, briefly summarize what you did.\n"
    )
    
    user_prompt = f"Task: {current_task}\n"
    if reviewer_feedback:
        user_prompt += f"\nReviewer feedback (fix these issues):\n{reviewer_feedback}\n"
        
    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing or empty. Please check your .env file.")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY,
            max_output_tokens=1024,
        )
        
        # Bind tools to the LLM
        llm_with_tools = llm.bind_tools(TOOLS)
        
        # Build message list
        messages = [
            HumanMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        # Call LLM - it may request tool calls
        response = llm_with_tools.invoke(messages)
        
        # Check if the LLM wants to call tools
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute each tool call
            tool_results = []
            pending_cmd = ""
            messages.append(response)  # Add AI message with tool calls
            
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Find and execute the tool
                tool_result = _execute_tool(tool_name, tool_args)
                
                # Check for HITL: dangerous command detected
                if "APPROVAL_REQUIRED" in tool_result:
                    # Extract the command from tool_args
                    pending_cmd = tool_args.get("command", str(tool_args))
                    return {
                        "messages": [AIMessage(content=f"[Worker]:\n⚠️ HITL: 위험 명령 감지됨 - CTO 승인 대기 중\n명령어: {pending_cmd}\n사유: {tool_result}")],
                        "status": "awaiting_approval",
                        "reviewer_feedback": "",
                        "pending_command": pending_cmd
                    }
                
                tool_results.append(f"[{tool_name}]: {tool_result}")
                
                # Add tool result to conversation
                messages.append(ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call["id"],
                ))
            
            # Get final summary from LLM after tool execution
            final_response = llm_with_tools.invoke(messages)
            content = final_response.content or ""
            
            # Prepend tool execution results
            tool_summary = "\n".join(tool_results)
            content = f"Tool Execution Results:\n{tool_summary}\n\nSummary: {content}"
        else:
            # No tool calls, just text response
            content = response.content or ""
        
    except Exception as e:
        content = f"Error calling LLM: {str(e)}"
        return {
            "messages": [AIMessage(content=f"[Worker]:\n{content}")],
            "status": "error",
            "reviewer_feedback": "",
            "pending_command": ""
        }
    
    return {
        "messages": [AIMessage(content=f"[Worker]:\n{content}")],
        "status": "needs_review",
        "reviewer_feedback": "",
        "pending_command": ""
    }


def _execute_tool(tool_name: str, tool_args: dict) -> str:
    """Execute a tool by name with given arguments."""
    tool_map = {t.name: t for t in TOOLS}
    
    if tool_name not in tool_map:
        return f"Error: Unknown tool '{tool_name}'"
    
    try:
        result = tool_map[tool_name].invoke(tool_args)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
