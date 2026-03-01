from typing import Dict, Any, List, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings
from tools.file_tools import read_file, write_file
from tools.shell_tools import execute_shell_command
from tools.system_langchain import send_notification, read_clipboard, write_clipboard
from tools.skill_tools import update_skill_manual
import os
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

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
    Supports streaming responses and session compression.
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
            "You are running directly on the user's local machine.\n"
            "IMPORTANT RULES:\n"
            "1. You have tools to write files, run shell commands, send notifications, and read/write the clipboard.\n"
            "2. Execute commands and tools proactively when asked to do things like 'build this', 'copy to my clipboard', or 'remind me'.\n"
            "3. Be friendly, concise, and helpful. You are talking 1:1 with the CTO.\n"
            "4. You have access to the 'update_skill_manual' tool. If the CTO asks you to modify how a certain team member works, use this tool to dynamically evolve their Skill Manual.\n"
        )
        
        self.tool_map = {t.name: t for t in PI_TOOLS}

    def _build_messages(self, user_message: str, history: Optional[List[Dict[str, str]]], project_id: str) -> List:
        """Build the message list with system prompt, knowledge injection, and history."""
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
                
        from agents.agent_factory import _load_knowledge
        knowledge_context = _load_knowledge(project_id)
        if knowledge_context:
            sys_prompt += knowledge_context

        messages = [SystemMessage(content=sys_prompt)]
        
        if history:
            for msg in history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                elif role == "system":
                    # Compact summary injected as context
                    messages.append(SystemMessage(content=f"[Previous conversation summary]\n{content}"))
        
        messages.append(HumanMessage(content=user_message))
        return messages

    def _execute_tool_calls(self, response, messages) -> Optional[Dict[str, Any]]:
        """Execute tool calls from LLM response. Returns HITL dict if approval needed, else None."""
        if not (hasattr(response, 'tool_calls') and response.tool_calls):
            return None
            
        messages.append(response)
        tool_outputs = []
        
        for tool_call in response.tool_calls:
            t_name = tool_call["name"]
            t_args = tool_call["args"]
            
            if t_name in self.tool_map:
                try:
                    result = str(self.tool_map[t_name].invoke(t_args))
                    
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
        
        return None  # No HITL needed, tool results appended to messages

    # ─────────────────────────────────────────────
    # Synchronous chat (backward compatible)
    # ─────────────────────────────────────────────
    def chat(self, user_message: str, history: Optional[List[Dict[str, str]]] = None, project_id: str = "default") -> Dict[str, Any]:
        """
        Process a user message directly, including potential tool executions.
        Returns a dictionary with the final text, any pending HITL commands, and the raw messages.
        """
        messages = self._build_messages(user_message, history, project_id)
        
        try:
            response = self.llm_with_tools.invoke(messages)
            
            hitl = self._execute_tool_calls(response, messages)
            if hitl:
                return hitl
            
            if hasattr(response, 'tool_calls') and response.tool_calls:
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

    # ─────────────────────────────────────────────
    # Streaming chat (async generator)
    # ─────────────────────────────────────────────
    async def chat_stream(self, user_message: str, history: Optional[List[Dict[str, str]]] = None, project_id: str = "default") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator that yields streaming chunks from Pi Agent.
        
        Yields:
            {"type": "chunk", "content": "..."} — text token
            {"type": "tool_call", "tool": "...", "args": {...}} — tool invocation event
            {"type": "tool_result", "tool": "...", "result": "..."} — tool result
            {"type": "approval", ...} — HITL approval request
            {"type": "done", "full_text": "..."} — final signal
            {"type": "error", "message": "..."} — error
        """
        messages = self._build_messages(user_message, history, project_id)
        
        try:
            # 1st pass: check for tool calls (non-streaming to detect tools)
            response = await asyncio.to_thread(self.llm_with_tools.invoke, messages)
            
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Signal tool calls to client
                messages.append(response)
                
                for tool_call in response.tool_calls:
                    t_name = tool_call["name"]
                    t_args = tool_call["args"]
                    
                    yield {"type": "tool_call", "tool": t_name, "args": t_args}
                    
                    if t_name in self.tool_map:
                        try:
                            result = await asyncio.to_thread(
                                lambda: str(self.tool_map[t_name].invoke(t_args))
                            )
                            
                            if "APPROVAL_REQUIRED" in result:
                                pending_cmd = t_args.get("command", str(t_args))
                                yield {
                                    "type": "approval",
                                    "text": f"⚠️ HITL: 위험 명령 감지됨 - CTO 승인 대기 중\n명령어: {pending_cmd}\n사유: {result}",
                                    "pending_command": pending_cmd
                                }
                                return
                                
                        except Exception as e:
                            result = f"Error executing {t_name}: {str(e)}"
                    else:
                        result = f"Unknown tool: {t_name}"
                    
                    yield {"type": "tool_result", "tool": t_name, "result": result}
                    messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))
                
                # 2nd pass (streaming): summarize tool results
                full_text = ""
                for chunk in self.llm_with_tools.stream(messages):
                    token = chunk.content or ""
                    if token:
                        full_text += token
                        yield {"type": "chunk", "content": token}
                
                yield {"type": "done", "full_text": full_text}
            else:
                # No tool calls — stream the response directly
                full_text = ""
                for chunk in self.llm_with_tools.stream(messages):
                    token = chunk.content or ""
                    if token:
                        full_text += token
                        yield {"type": "chunk", "content": token}
                
                yield {"type": "done", "full_text": full_text}
                
        except Exception as e:
            logger.error(f"Pi Agent stream error: {e}")
            yield {"type": "error", "message": str(e)}

    # ─────────────────────────────────────────────
    # Session compression (/compact)
    # ─────────────────────────────────────────────
    def compact_history(self, history: List[Dict[str, str]]) -> str:
        """
        Summarize conversation history into a concise 3-5 sentence summary.
        Used when session grows too large (token saving).
        """
        if not history:
            return "No conversation history to compact."
        
        conversation_text = "\n".join(
            f"{msg['role'].upper()}: {msg['content'][:500]}" 
            for msg in history[-30:]  # Summarize last 30 messages max
        )
        
        compact_prompt = (
            "Summarize the following conversation between a user (CTO) and an AI assistant (Pi) "
            "in 3-5 sentences. Capture the key topics, decisions, and any pending items.\n\n"
            f"CONVERSATION:\n{conversation_text}\n\n"
            "SUMMARY:"
        )
        
        try:
            response = self.llm.invoke([HumanMessage(content=compact_prompt)])
            return response.content or "Summary generation failed."
        except Exception as e:
            logger.warning(f"Compact history failed: {e}")
            return f"Failed to compact history: {str(e)}"

pi_agent_instance = PiAgent()
