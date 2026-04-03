from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast_to_user(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)


manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, user_id: int):
    """Handle WebSocket connection"""
    await manager.connect(websocket, user_id)
    
    try:
        # Send connection success message
        await manager.send_personal_message({
            "type": "CONNECTED",
            "message": "WebSocket connection established",
            "user_id": user_id
        }, websocket)
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            await handle_message(websocket, user_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


async def handle_message(websocket: WebSocket, user_id: int, message: dict):
    """Handle incoming WebSocket message"""
    msg_type = message.get("type")
    
    if msg_type == "PING":
        await manager.send_personal_message({
            "type": "PONG",
            "timestamp": asyncio.get_event_loop().time()
        }, websocket)
    
    elif msg_type == "SYNC_REQUEST":
        await handle_sync_request(websocket, user_id, message)
    
    elif msg_type == "FILE_CHANGED":
        await handle_file_changed(websocket, user_id, message)
    
    elif msg_type == "CONFLICT_RESOLUTION":
        await handle_conflict_resolution(websocket, user_id, message)
    
    else:
        await manager.send_personal_message({
            "type": "ERROR",
            "message": f"Unknown message type: {msg_type}"
        }, websocket)


async def handle_sync_request(websocket: WebSocket, user_id: int, message: dict):
    """Handle sync request"""
    await manager.send_personal_message({
        "type": "SYNC_RESPONSE",
        "status": "pending",
        "message": "Sync request received"
    }, websocket)
    
    # Simulate sync process
    await asyncio.sleep(1)
    
    await manager.send_personal_message({
        "type": "SYNC_PROGRESS",
        "progress": 50,
        "message": "Syncing files..."
    }, websocket)
    
    await asyncio.sleep(1)
    
    await manager.send_personal_message({
        "type": "SYNC_COMPLETED",
        "progress": 100,
        "message": "Sync completed successfully",
        "data": {
            "synced_files": 5,
            "conflicts": 0
        }
    }, websocket)


async def handle_file_changed(websocket: WebSocket, user_id: int, message: dict):
    """Handle file change notification"""
    file_path = message.get("file_path")
    print(f"File changed: {file_path} (User: {user_id})")
    
    await manager.send_personal_message({
        "type": "FILE_CHANGED_ACK",
        "file_path": file_path,
        "message": "File change received"
    }, websocket)
    
    # Broadcast to other connections of the same user
    await manager.broadcast_to_user({
        "type": "FILE_CHANGED_NOTIFICATION",
        "file_path": file_path,
        "message": "File has been changed"
    }, user_id)


async def handle_conflict_resolution(websocket: WebSocket, user_id: int, message: dict):
    """Handle conflict resolution"""
    resolution = message.get("resolution")
    file_path = message.get("file_path")
    
    print(f"Conflict resolution: {resolution} for {file_path} (User: {user_id})")
    
    await manager.send_personal_message({
        "type": "CONFLICT_RESOLUTION_ACK",
        "resolution": resolution,
        "file_path": file_path,
        "message": "Conflict resolution received"
    }, websocket)
