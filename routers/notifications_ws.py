from fastapi import WebSocket, APIRouter, WebSocketDisconnect, status
from typing import Dict
from utils.auth import decode_access_token
import json

router = APIRouter(tags=["Notification"])

# In-memory user connections
connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_access_token(token)
    if not payload or payload.get("user_id") != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    connections[user_id] = websocket

    try:
        while True:
            await websocket.receive_text()  # Keep the connection alive
    except WebSocketDisconnect:
        connections.pop(user_id, None)
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        connections.pop(user_id, None)

#  Call this from other files to notify a user in real-time
async def send_notification(user_id: str, data: dict):
    websocket = connections.get(user_id)
    if websocket:
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            print(f"Failed to send notification to {user_id}: {e}")
            connections.pop(user_id, None)
