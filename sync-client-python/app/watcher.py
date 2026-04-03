import os
import asyncio
from typing import Callable, Optional, List
from app.utils import calculate_file_hash, create_file_data, walk_directory
from app.config import get_settings


class FileWatcher:
    def __init__(self, watch_dir: str, callback: Callable):
        self.watch_dir = watch_dir
        self.callback = callback
        self.settings = get_settings()
        self.file_hashes: dict[str, str] = {}
        self.running = False
        self.watch_task: Optional[asyncio.Task] = None
    
    async def start(self):
        self.running = True
        await self.scan_directory()
        self.watch_task = asyncio.create_task(self._watch_loop())
        print(f"FileWatcher started for {self.watch_dir}")
    
    async def stop(self):
        self.running = False
        if self.watch_task:
            self.watch_task.cancel()
            try:
                await self.watch_task
            except asyncio.CancelledError:
                pass
        print("FileWatcher stopped")
    
    async def scan_directory(self):
        if not os.path.exists(self.watch_dir):
            os.makedirs(self.watch_dir)
            return
        
        files = walk_directory(self.watch_dir)
        
        for file_path in files:
            current_hash = calculate_file_hash(file_path)
            
            if file_path not in self.file_hashes:
                self.file_hashes[file_path] = current_hash
                await self.callback("created", file_path)
            elif self.file_hashes[file_path] != current_hash:
                self.file_hashes[file_path] = current_hash
                await self.callback("modified", file_path)
        
        await self.check_deleted_files(files)
    
    async def check_deleted_files(self, current_files: List[str]):
        deleted_files = set(self.file_hashes.keys()) - set(current_files)
        
        for file_path in deleted_files:
            del self.file_hashes[file_path]
            await self.callback("deleted", file_path)
    
    async def _watch_loop(self):
        while self.running:
            try:
                await self.scan_directory()
                await asyncio.sleep(self.settings.WATCH_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"FileWatcher error: {e}")
                await asyncio.sleep(self.settings.WATCH_INTERVAL)
