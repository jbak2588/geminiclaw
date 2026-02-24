import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from agents.graph import team_graph

router = APIRouter()

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

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            # Wait for task instruction from client
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            task_instruction = payload.get("task", "")
            if not task_instruction:
                await manager.send_personal_message(json.dumps({"error": "No task provided."}), client_id)
                continue
                
            # Initialize state
            initial_state = {
                "messages": [],
                "current_task": task_instruction,
                "reviewer_feedback": "",
                "status": "in_progress"
            }
            
            # Start streaming the agent events
            await manager.send_personal_message(json.dumps({"type": "info", "message": "Agentic Team started working..."}), client_id)
            
            # Note: LangGraph's stream is synchronous by default unless using astream
            # For PoC, we iterate over stream and yield back via websocket.
            for event in team_graph.stream(initial_state):
                for node_name, state_value in event.items():
                    # Extract the latest message
                    msg_content = ""
                    if "messages" in state_value and state_value["messages"]:
                        msg_content = state_value["messages"][-1].content
                        
                    event_payload = {
                        "type": "agent_event",
                        "node": node_name,
                        "status": state_value.get("status", "unknown"),
                        "message": msg_content
                    }
                    await manager.send_personal_message(json.dumps(event_payload), client_id)
                    
            await manager.send_personal_message(json.dumps({"type": "info", "message": "Workflow Completed."}), client_id)
            
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
