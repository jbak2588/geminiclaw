import json
import os
import copy
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from agents.graph import create_dynamic_graph
from agents.company_setup import generate_org_chart
from tools.shell_tools import force_execute_command
from core.memory import memory_store
from agents.pi_agent import pi_agent_instance

router = APIRouter()

# Ensure logs directory exists
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

manager = ConnectionManager()

# Track the last log file per client for HITL logging
_client_log_files: Dict[str, str] = {}

# ────────────────────────────────────────────────────
# Kanban helpers
# ────────────────────────────────────────────────────

_REVIEWER_NODES = {"reviewer"}
_PM_NODES = {"pm"}


def _update_kanban_status(
    kanban_tasks: List[Dict], node_name: str, new_status: str
) -> List[Dict]:
    """kanban_tasks 리스트에서 node_name에 해당하는 태스크의 status를 업데이트."""
    updated = copy.deepcopy(kanban_tasks)
    for task in updated:
        if task.get("agent") == node_name:
            task["status"] = new_status
            break
    return updated


def _derive_kanban_update(
    kanban_tasks: List[Dict], node_name: str, agent_status: str
) -> List[Dict]:
    """
    에이전트 이벤트를 기반으로 kanban_tasks 상태를 결정합니다.
    - pm 완료 → 모두 todo 유지 (초기 상태 그대로 전송)
    - reviewer 진입 → 직전 에이전트 status: review
    - dispatcher → 변경 없음 (skip)
    - 일반 에이전트 → in_progress
    - 완료(approved/done/completed) → done
    """
    if node_name == "dispatcher":
        return kanban_tasks  # dispatcher는 UI에 영향 없음

    if node_name in _PM_NODES:
        return kanban_tasks  # PM 완료 → 초기 todo 상태 전송

    if node_name in _REVIEWER_NODES:
        # 직전 in_progress 에이전트를 review 상태로
        updated = copy.deepcopy(kanban_tasks)
        for task in updated:
            if task.get("status") == "in_progress":
                task["status"] = "review"
        return updated

    # 일반 에이전트
    status_lower = agent_status.lower() if agent_status else ""
    if any(kw in status_lower for kw in ("approved", "done", "completed", "finished")):
        return _update_kanban_status(kanban_tasks, node_name, "done")
    else:
        return _update_kanban_status(kanban_tasks, node_name, "in_progress")


def _write_log(log_file: str, text: str):
    """Append a line to the session log file."""
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(text + "\n")

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            # Wait for message from client
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            msg_type = payload.get("type", "task")
            
            # ─────────────────────────────────────────────
            # HITL: Handle approval response from CTO
            # ─────────────────────────────────────────────
            if msg_type == "approval_response":
                approved = payload.get("approved", False)
                command = payload.get("command", "")
                log_file = _client_log_files.get(client_id)
                
                if approved and command:
                    # CTO approved: execute the command (bypass safety)
                    result = force_execute_command(command)
                    msg = f"[CTO 승인] 명령어 실행 완료:\n$ {command}\n\n결과:\n{result}"
                    await manager.send_personal_message(json.dumps({
                        "type": "agent_event",
                        "node": "system",
                        "status": "approved",
                        "message": msg
                    }), client_id)
                    if log_file:
                        _write_log(log_file, f"\n[HITL] CTO 승인 - 명령어 실행됨: {command}")
                        _write_log(log_file, f"실행 결과: {result}")
                else:
                    # CTO rejected
                    msg = f"[CTO 거절] 위험 명령어가 차단되었습니다: {command}"
                    await manager.send_personal_message(json.dumps({
                        "type": "agent_event",
                        "node": "system",
                        "status": "rejected",
                        "message": msg
                    }), client_id)
                    if log_file:
                        _write_log(log_file, f"\n[HITL] CTO 거절 - 명령어 차단됨: {command}")
                
                if log_file:
                    _write_log(log_file, "\n[INFO] HITL Workflow Completed.")
                
                await manager.send_personal_message(json.dumps({
                    "type": "info",
                    "message": "Workflow Completed."
                }), client_id)
                continue
            
            # ─────────────────────────────────────────────
            # Org Chart: Generate AI org chart for company
            # ─────────────────────────────────────────────
            if msg_type == "org_chart_request":
                # Fallback to old profile if description isn't provided, but prioritize description.
                company_desc = payload.get("company_description", "")
                project_id = payload.get("project_id", client_id)
                whitepaper_dir = payload.get("whitepaper_dir", "")
                
                if not company_desc:
                    profile_id = payload.get("profile_id", "pt_humantric")
                    # Quick mock for backward compatibility
                    company_desc = f"Company ID: {profile_id}. Type: {payload.get('company_type', 'Tech')}"
                
                await manager.send_personal_message(json.dumps({
                    "type": "info",
                    "message": "AI가 조직도와 직무 기술서(Skills)를 생성하고 있습니다..."
                }), client_id)
                
                org_chart = await generate_org_chart(company_desc, project_id, whitepaper_dir)
                
                await manager.send_personal_message(json.dumps({
                    "type": "org_chart_response",
                    "data": org_chart
                }), client_id)
                continue

            # ─────────────────────────────────────────────
            # Base Assistant (Pi) 1:1 Chat Flow (Streaming + /compact)
            # ─────────────────────────────────────────────
            if msg_type == "pi_chat":
                session_id = client_id
                user_message = payload.get("message", "")
                project_id = payload.get("project_id", "default")
                if not user_message:
                    continue
                
                # ── Handle /compact command ──
                if user_message.strip().lower() == "/compact":
                    history = memory_store.get_session_history(session_id)
                    msg_count = memory_store.get_message_count(session_id)
                    
                    if msg_count <= 2:
                        await manager.send_personal_message(json.dumps({
                            "type": "pi_compact",
                            "summary": "세션이 이미 충분히 짧습니다.",
                            "saved_messages": 0
                        }), client_id)
                        continue
                    
                    await manager.send_personal_message(json.dumps({
                        "type": "info",
                        "message": f"📦 {msg_count}개 메시지를 요약 중..."
                    }), client_id)
                    
                    summary = pi_agent_instance.compact_history(history)
                    saved = memory_store.compact_session(session_id, summary)
                    
                    await manager.send_personal_message(json.dumps({
                        "type": "pi_compact",
                        "summary": summary,
                        "saved_messages": saved
                    }), client_id)
                    continue
                
                # ── Streaming response flow ──
                history = memory_store.get_session_history(session_id)
                memory_store.add_message(session_id, "user", user_message)
                
                await manager.send_personal_message(json.dumps({
                    "type": "info",
                    "message": "Pi is thinking..."
                }), client_id)
                
                full_text = ""
                async for event in pi_agent_instance.chat_stream(user_message, history, project_id=project_id):
                    event_type = event.get("type", "")
                    
                    if event_type == "chunk":
                        await manager.send_personal_message(json.dumps({
                            "type": "pi_stream",
                            "chunk": event["content"]
                        }), client_id)
                        full_text += event["content"]
                    
                    elif event_type == "tool_call":
                        await manager.send_personal_message(json.dumps({
                            "type": "pi_tool_call",
                            "tool": event["tool"],
                            "args": event["args"]
                        }), client_id)
                    
                    elif event_type == "tool_result":
                        await manager.send_personal_message(json.dumps({
                            "type": "pi_tool_result",
                            "tool": event["tool"],
                            "result": event["result"][:500]  # Truncate large results
                        }), client_id)
                    
                    elif event_type == "approval":
                        await manager.send_personal_message(json.dumps({
                            "type": "approval_request",
                            "command": event["pending_command"],
                            "message": event["text"]
                        }), client_id)
                        # Don't save — awaiting approval
                        full_text = ""
                        break
                    
                    elif event_type == "done":
                        full_text = event.get("full_text", full_text)
                    
                    elif event_type == "error":
                        await manager.send_personal_message(json.dumps({
                            "type": "agent_event",
                            "node": "pi",
                            "status": "error",
                            "message": event["message"]
                        }), client_id)
                        full_text = ""
                        break
                
                # Save and send final event
                if full_text:
                    memory_store.add_message(session_id, "assistant", full_text)
                    await manager.send_personal_message(json.dumps({
                        "type": "pi_stream_end",
                        "full_text": full_text
                    }), client_id)
                
                continue
            
            # ─────────────────────────────────────────────
            # Normal task flow (Multi-Agent Team)
            # ─────────────────────────────────────────────
            task_instruction = payload.get("task", "")
            if not task_instruction:
                await manager.send_personal_message(json.dumps({"error": "No task provided."}), client_id)
                continue
            
            # Get team configuration from frontend (default: developer only)
            team_config = payload.get("team", [{"name": "developer"}])
            
            # Inject knowledge directory for all agents
            knowledge_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "doc")
            for member in team_config:
                if "knowledge_dir" not in member or not member["knowledge_dir"]:
                    member["knowledge_dir"] = knowledge_dir
            
            # Create a log file for this session
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(LOGS_DIR, f"session_{timestamp}_{client_id[:8]}.txt")
            _client_log_files[client_id] = log_file  # Track for HITL logging
            _write_log(log_file, f"=== Session Log ===")
            _write_log(log_file, f"Time: {datetime.now().isoformat()}")
            _write_log(log_file, f"Task: {task_instruction}")
            team_names = [m.get("name", "?") for m in team_config]
            _write_log(log_file, f"Team: {', '.join(team_names)}")
            _write_log(log_file, f"{'='*50}\n")
            
            # Build dynamic graph from team config
            dynamic_graph = create_dynamic_graph(team_config)
            
            thread_id = payload.get("thread_id", client_id)
            
            # Initialize state
            initial_state = {
                "messages": [],
                "current_task": task_instruction,
                "reviewer_feedback": "",
                "status": "in_progress",
                "pending_command": "",
                "team_config": team_config,
                "sub_tasks": {},
                "agent_order": [],
                "current_agent_index": 0,
                "project_id": thread_id,
            }
            
            # Start streaming
            await manager.send_personal_message(json.dumps({
                "type": "info",
                "message": f"Agentic Team started working... (Team: {', '.join(team_names)})"
            }), client_id)
            _write_log(log_file, "[INFO] Agentic Team started working...\n")
            
            # 칸반 상태 추적용 (세션 내 유지)
            current_kanban_tasks: List[Dict] = []
            # 노드 그래프 추적용
            node_states: Dict[str, str] = {}  # {node_name: status}
            async for event in dynamic_graph.astream(initial_state, config={"configurable": {"thread_id": thread_id}}):
                for node_name, state_value in event.items():
                    msg_content = ""
                    if "messages" in state_value and state_value["messages"]:
                        msg_content = state_value["messages"][-1].content
                    
                    status = state_value.get("status", "unknown")

                    # ─────────────────────────────────────────────
                    # Kanban: PM 완료 시 초기 칸반 상태 세팅
                    # ─────────────────────────────────────────────
                    if node_name == "pm" and "kanban_tasks" in state_value:
                        current_kanban_tasks = state_value["kanban_tasks"]

                    # ─────────────────────────────────────────────
                    # Kanban: 에이전트 이벤트마다 상태 업데이트
                    # ─────────────────────────────────────────────
                    if current_kanban_tasks and node_name not in ("pm",):
                        current_kanban_tasks = _derive_kanban_update(
                            current_kanban_tasks, node_name, status
                        )

                    # ─────────────────────────────────────────────
                    # Kanban update 이벤트 전송
                    # ─────────────────────────────────────────────
                    if current_kanban_tasks:
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "kanban_update",
                                "tasks": current_kanban_tasks,
                            }),
                            client_id,
                        )

                    # ─────────────────────────────────────────────
                    # Node Graph update 이벤트 전송 (Google Opal 스타일)
                    # ─────────────────────────────────────────────
                    _SKIP_NODES = {"dispatcher", "retry_manager", "__end__"}
                    if node_name not in _SKIP_NODES:
                        # 노드별 상태 매핑
                        _node_status_map = {
                            "pm_routed": "completed", "approved": "completed",
                            "done": "completed", "completed": "completed",
                            "needs_review": "running", "in_progress": "running",
                            "error": "error", "awaiting_approval": "pending",
                        }
                        graph_node_status = _node_status_map.get(status, "running")
                        node_states[node_name] = graph_node_status

                        # 팀 순서에서 엣지(연결선) 생성
                        team_order = [m.get("name") for m in team_config if m.get("name") not in ("pm", "reviewer")]
                        graph_nodes = []
                        graph_edges = []

                        # PM 노드
                        graph_nodes.append({"id": "pm", "label": "CTO", "role": "pm",
                                            "status": node_states.get("pm", "pending")})
                        # 에이전트 노드들
                        for i, agent in enumerate(team_order):
                            graph_nodes.append({"id": agent, "label": agent.capitalize(),
                                                "role": agent, "status": node_states.get(agent, "pending")})
                            if i == 0:
                                graph_edges.append({"from": "pm", "to": agent})
                            else:
                                graph_edges.append({"from": "reviewer", "to": agent})
                            graph_edges.append({"from": agent, "to": "reviewer"})

                        # Reviewer 노드
                        graph_nodes.append({"id": "reviewer", "label": "Reviewer", "role": "reviewer",
                                            "status": node_states.get("reviewer", "pending")})

                        await manager.send_personal_message(
                            json.dumps({
                                "type": "node_update",
                                "nodes": graph_nodes,
                                "edges": graph_edges,
                                "active_node": node_name,
                            }),
                            client_id,
                        )


                    event_payload = {
                        "type": "agent_event",
                        "node": node_name,
                        "status": status,
                        "message": msg_content
                    }
                    
                    # ─────────────────────────────────────────────
                    # HITL: Send approval request to frontend
                    # ─────────────────────────────────────────────
                    if status == "awaiting_approval":
                        pending_cmd = state_value.get("pending_command", "")
                        event_payload["type"] = "approval_request"
                        event_payload["command"] = pending_cmd
                    
                    await manager.send_personal_message(json.dumps(event_payload), client_id)
                    
                    # Write to log
                    _write_log(log_file, f"[{node_name}] -> Status: {status}")
                    _write_log(log_file, msg_content)
                    _write_log(log_file, "")
            
            await manager.send_personal_message(json.dumps({
                "type": "info",
                "message": "Workflow Completed."
            }), client_id)
            _write_log(log_file, f"\n[INFO] Workflow Completed.")
            _write_log(log_file, f"Log saved to: {log_file}")
            logging.info(f"Session log saved: {log_file}")
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        error_msg = {
            "type": "agent_event",
            "node": "system",
            "status": "error",
            "message": f"Server Error: {str(e)}"
        }
        await manager.send_personal_message(json.dumps(error_msg), client_id)
        manager.disconnect(client_id)
