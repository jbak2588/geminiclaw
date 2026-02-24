import json
import os
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from agents.graph import team_graph
from tools.shell_tools import force_execute_command

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
            # Normal task flow
            # ─────────────────────────────────────────────
            task_instruction = payload.get("task", "")
            if not task_instruction:
                await manager.send_personal_message(json.dumps({"error": "No task provided."}), client_id)
                continue
            
            # Create a log file for this session
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(LOGS_DIR, f"session_{timestamp}_{client_id[:8]}.txt")
            _client_log_files[client_id] = log_file  # Track for HITL logging
            _write_log(log_file, f"=== Session Log ===")
            _write_log(log_file, f"Time: {datetime.now().isoformat()}")
            _write_log(log_file, f"Task: {task_instruction}")
            _write_log(log_file, f"{'='*50}\n")
            
            # Initialize state
            initial_state = {
                "messages": [],
                "current_task": task_instruction,
                "reviewer_feedback": "",
                "status": "in_progress",
                "pending_command": ""
            }
            
            # Start streaming
            await manager.send_personal_message(json.dumps({
                "type": "info",
                "message": "Agentic Team started working..."
            }), client_id)
            _write_log(log_file, "[INFO] Agentic Team started working...\n")
            
            for event in team_graph.stream(initial_state):
                for node_name, state_value in event.items():
                    msg_content = ""
                    if "messages" in state_value and state_value["messages"]:
                        msg_content = state_value["messages"][-1].content
                    
                    status = state_value.get("status", "unknown")
                    
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
            print(f"📝 Session log saved: {log_file}")
            
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
