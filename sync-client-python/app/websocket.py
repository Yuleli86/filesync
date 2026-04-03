import asyncio
import websockets
import json
from typing import Callable, Optional, List
from app.config import get_settings


class SyncWebSocketClient:
    def __init__(self, token: str):
        self.settings = get_settings()
        self.ws_url = f"{self.settings.WS_URL}?token={token}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.message_handlers: dict[str, Callable] = {}
        self.running = False
    
    def register_handler(self, message_type: str, handler: Callable):
        self.message_handlers[message_type] = handler
    
    async def connect(self):
        self.websocket = await websockets.connect(self.ws_url)
        self.running = True
        print(f"WebSocket connected to {self.ws_url}")
    
    async def disconnect(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("WebSocket disconnected")
    
    async def send_message(self, message: dict):
        if self.websocket:
            await self.websocket.send(json.dumps(message))
    
    async def send_ping(self):
        await self.send_message({"type": "PING"})
    
    async def send_sync_request(self, files: List):
        await self.send_message({
            "type": "SYNC_REQUEST",
            "data": {"files": files}
        })
    
    async def send_file_changed(self, file_path: str):
        await self.send_message({
            "type": "FILE_CHANGED",
            "data": {"file_path": file_path}
        })
    
    async def send_conflict_resolution(self, resolution: str, file_path: str):
        await self.send_message({
            "type": "CONFLICT_RESOLUTION",
            "data": {
                "resolution": resolution,
                "file_path": file_path
            }
        })
    
    async def listen(self):
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        try:
            while self.running:
                message = await self.websocket.recv()
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    async def handle_message(self, message: dict):
        message_type = message.get("type")
        handler = self.message_handlers.get(message_type)
        
        if handler:
            await handler(message)
        else:
            print(f"No handler for message type: {message_type}")
            print(f"Message: {message}")
    
    async def start(self):
        await self.connect()
        listen_task = asyncio.create_task(self.listen())
        return listen_task
