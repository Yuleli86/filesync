import os
import asyncio
from typing import Optional, List
from app.client import SyncClient
from app.websocket import SyncWebSocketClient
from app.watcher import FileWatcher
from app.utils import create_file_data, walk_directory, ensure_directory
from app.models import FileData
from app.config import get_settings


class SyncManager:
    def __init__(self):
        self.settings = get_settings()
        self.client = SyncClient()
        self.ws_client: Optional[SyncWebSocketClient] = None
        self.watcher: Optional[FileWatcher] = None
        self.sync_dir = self.settings.SYNC_DIR
        self.running = False
    
    async def initialize(self):
        ensure_directory(self.sync_dir)
        print(f"Sync directory: {self.sync_dir}")
    
    async def login(self, username: str, password: str) -> bool:
        try:
            result = await self.client.login(username, password)
            if result.get("success"):
                print(f"Login successful: {result['data']['user']['username']}")
                return True
            return False
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    async def register(self, username: str, email: str, password: str) -> bool:
        try:
            from app.models import UserCreate
            
            user_data = UserCreate(
                username=username,
                email=email,
                password=password
            )
            
            result = await self.client.register(user_data)
            if result.get("success"):
                print(f"Registration successful: {result['data']['user']['username']}")
                self.client.token = result["data"]["token"]
                return True
            return False
        except Exception as e:
            print(f"Registration failed: {e}")
            return False
    
    async def start_sync(self):
        self.running = True
        
        await self.connect_websocket()
        await self.start_file_watcher()
        
        await self.initial_sync()
        
        print("Sync started")
    
    async def stop_sync(self):
        self.running = False
        
        if self.watcher:
            await self.watcher.stop()
        
        if self.ws_client:
            await self.ws_client.disconnect()
        
        print("Sync stopped")
    
    async def connect_websocket(self):
        self.ws_client = SyncWebSocketClient(self.client.token)
        
        self.ws_client.register_handler("CONNECTED", self._on_connected)
        self.ws_client.register_handler("PONG", self._on_pong)
        self.ws_client.register_handler("SYNC_RESPONSE", self._on_sync_response)
        self.ws_client.register_handler("SYNC_PROGRESS", self._on_sync_progress)
        self.ws_client.register_handler("SYNC_COMPLETED", self._on_sync_completed)
        self.ws_client.register_handler("FILE_CHANGED_NOTIFICATION", self._on_file_changed_notification)
        
        await self.ws_client.start()
    
    async def start_file_watcher(self):
        self.watcher = FileWatcher(self.sync_dir, self._on_file_change)
        await self.watcher.start()
    
    async def initial_sync(self):
        print("Starting initial sync...")
        
        files = walk_directory(self.sync_dir)
        file_data_list = []
        
        for file_path in files:
            try:
                file_data = create_file_data(file_path, self.sync_dir)
                file_data_list.append(file_data)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
        
        if file_data_list:
            result = await self.client.init_sync(file_data_list)
            
            if result.get("success"):
                data = result["data"]
                synced_files = data.get("synced_files", [])
                conflicts = data.get("conflicts", [])
                
                print(f"Sync completed: {len(synced_files)} files synced")
                
                if conflicts:
                    print(f"Found {len(conflicts)} conflicts:")
                    for conflict in conflicts:
                        print(f"  - {conflict['file']['path']}/{conflict['file']['filename']}")
                    await self._handle_conflicts(result["data"]["sync_id"], conflicts)
            else:
                print(f"Sync failed: {result.get('message')}")
    
    async def _handle_conflicts(self, sync_id: int, conflicts: List):
        for conflict in conflicts:
            file_data = conflict["file"]
            existing_file = conflict["existing_file"]
            
            print(f"\nConflict detected: {file_data['path']}/{file_data['filename']}")
            print(f"  Local: size={file_data['size']}, hash={file_data['file_hash']}")
            print(f"  Remote: size={existing_file['size']}, hash={existing_file['file_hash']}")
            
            resolution = input("Choose resolution (keep_local/keep_remote/keep_both): ").strip()
            
            if resolution in ["keep_local", "keep_remote", "keep_both"]:
                file_obj = FileData(**file_data)
                await self.client.resolve_conflict(sync_id, file_obj, resolution)
                print(f"Conflict resolved: {resolution}")
            else:
                print("Invalid resolution, skipping")
    
    async def _on_file_change(self, event_type: str, file_path: str):
        print(f"File {event_type}: {file_path}")
        
        if self.ws_client:
            rel_path = os.path.relpath(file_path, self.sync_dir)
            await self.ws_client.send_file_changed(rel_path)
    
    async def _on_connected(self, message: dict):
        print(f"WebSocket connected: {message.get('message')}")
    
    async def _on_pong(self, message: dict):
        pass
    
    async def _on_sync_response(self, message: dict):
        print(f"Sync response: {message.get('message')}")
    
    async def _on_sync_progress(self, message: dict):
        progress = message.get("progress", 0)
        print(f"Sync progress: {progress}%")
    
    async def _on_sync_completed(self, message: dict):
        data = message.get("data", {})
        synced_files = data.get("synced_files", 0)
        conflicts = data.get("conflicts", 0)
        print(f"Sync completed: {synced_files} files synced, {conflicts} conflicts")
    
    async def _on_file_changed_notification(self, message: dict):
        file_path = message.get("file_path")
        print(f"Remote file changed: {file_path}")
        await self._sync_remote_file(file_path)
    
    async def _sync_remote_file(self, file_path: str):
        try:
            result = await self.client.list_files()
            
            if result.get("success"):
                files = result.get("data", [])
                
                for file in files:
                    remote_path = f"{file['path']}/{file['filename']}" if file['path'] else file['filename']
                    
                    if remote_path == file_path or remote_path.startswith(file_path):
                        local_path = os.path.join(self.sync_dir, remote_path)
                        
                        if file['is_directory']:
                            ensure_directory(local_path)
                        else:
                            ensure_directory(os.path.dirname(local_path))
                            await self.client.download_file(file['id'], local_path)
                            print(f"Downloaded: {remote_path}")
        except Exception as e:
            print(f"Error syncing remote file: {e}")
    
    async def close(self):
        await self.stop_sync()
        await self.client.close()
