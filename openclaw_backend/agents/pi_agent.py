from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings
from tools.file_tools import read_file, write_file
from tools.shell_tools import execute_shell_command
from tools.system_langchain import send_notification, read_clipboard, write_clipboard
from tools.skill_tools import update_skill_manual
import json

# The Pi Agent uses a wider set of tools compared to the regular Worker
PI_TOOLS = [
    read_file, 
    write_file, 
    execute_shell_command,
    send_notification,
    read_clipboard,
    write_clipboard,
    update_skill_manual
]

class PiAgent:
    """
    A standalone, 1:1 Base Personal Assistant.
    Bypasses the multi-agent graph, responds directly to the user,
    and has full access to local system tools.
    """
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing or empty.")
            
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY,
            max_output_tokens=2048,
        )
        self.llm_with_tools = self.llm.bind_tools(PI_TOOLS)
        
        self.system_prompt = (
            "You are Pi, a highly capable Local Personal Assistant.\n"
            "You are running directly on the user's local machine (macOS).\n"
            "IMPORTANT RULES:\n"
            "1. You have tools to write files, run shell commands, send macOS notifications, and read/write the clipboard.\n"
            "2. Execute commands and tools proactively when asked to do things like 'build this', 'copy to my clipboard', or 'remind me'.\n"
            "3. Be friendly, concise, and helpful. You are talking 1:1 with the CTO.\n"
            "4. You have access to the 'update_skill_manual' tool. If the CTO asks you to modify how a certain team member works, use this tool to dynamically evolve their Skill Manual.\n"
        )
        
        self.tool_map = {t.name: t for t in PI_TOOLS}

    def chat(self, user_message: str, history: Optional[List[Dict[str, str]]] = None, project_id: str = "default") -> Dict[str, Any]:
        """
        Process a user message directly, including potential tool executions.
        Returns a dictionary with the final text, any pending HITL commands, and the raw messages.
        """
        # Inject dynamic PM skill if available
        import os
        dynamic_skill_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "storage", "skills", project_id, "pm_manual.md"
        )
        sys_prompt = self.system_prompt
        if os.path.exists(dynamic_skill_path):
            try:
                with open(dynamic_skill_path, "r", encoding="utf-8") as f:
                    sys_prompt += "\n\n[Project Overview & PM Operating Manual]\n" + f.read().strip()
            except Exception:
                pass
                
        # Inject dynamic project knowledge
        from agents.agent_factory import _load_knowledge
        knowledge_context = _load_knowledge(project_id)
        if knowledge_context:
            sys_prompt += knowledge_context

        messages = [SystemMessage(content=sys_prompt)]
        
        # Load history
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=user_message))
        
        try:
            # First pass: see if LLM wants to use tools
            response = self.llm_with_tools.invoke(messages)
            
            pending_cmd = ""
            tool_outputs = []
            
            if hasattr(response, 'tool_calls') and response.tool_calls:
                messages.append(response)
                
                for tool_call in response.tool_calls:
                    t_name = tool_call["name"]
                    t_args = tool_call["args"]
                    
                    # Execute
                    if t_name in self.tool_map:
                        try:
                            # Direct invocation. If it's a shell command, the tool handles HITL string.
                            result = str(self.tool_map[t_name].invoke(t_args))
                            
                            # HITL Check
                            if "APPROVAL_REQUIRED" in result:
                                pending_cmd = t_args.get("command", str(t_args))
                                return {
                                    "text": f"⚠️ HITL: 위험 명령 감지됨 - CTO 승인 대기 중\n명령어: {pending_cmd}\n사유: {result}",
                                    "status": "awaiting_approval",
                                    "pending_command": pending_cmd
                                }
                                
                        except Exception as e:
                            result = f"Error executing {t_name}: {str(e)}"
                    else:
                        result = f"Unknown tool: {t_name}"
                        
                    tool_outputs.append((t_name, result))
                    messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))
                
                # Second LLM pass to summarize tool results
                final_response = self.llm_with_tools.invoke(messages)
                final_text = final_response.content or ""
            else:
                final_text = response.content or ""
                
            return {
                "text": final_text,
                "status": "done",
                "pending_command": ""
            }
            
        except Exception as e:
            return {
                "text": f"Error in Pi Agent: {str(e)}",
                "status": "error",
                "pending_command": ""
            }

pi_agent_instance = PiAgent()
