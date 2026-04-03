import httpx
from typing import Optional, List
from app.models import UserCreate, AuthResponse, FileData, FileListResponse, SyncInitRequest, SyncResponse
from app.config import get_settings


class SyncClient:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.SERVER_URL
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def register(self, user_data: UserCreate) -> dict:
        response = await self.client.post(
            f"{self.base_url}/api/auth/register",
            json=user_data.dict(),
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def login(self, username: str, password: str) -> dict:
        from httpx import FormData
        
        form_data = FormData({
            "username": username,
            "password": password
        })
        
        response = await self.client.post(
            f"{self.base_url}/api/auth/login",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        
        result = response.json()
        if result.get("success"):
            self.token = result["data"]["token"]
        
        return result
    
    async def upload_file_metadata(self, file_data: FileData) -> dict:
        response = await self.client.post(
            f"{self.base_url}/api/files/upload",
            json=file_data.dict(),
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def upload_file_content(self, file_id: int, file_path: str) -> dict:
        import os
        
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
            response = await self.client.post(
                f"{self.base_url}/api/files/upload-content/{file_id}",
                files=files,
                headers={"Authorization": f"Bearer {self.token}"}
            )
        
        response.raise_for_status()
        return response.json()
    
    async def list_files(self, path: Optional[str] = None, limit: int = 50, offset: int = 0) -> dict:
        params = {"limit": limit, "offset": offset}
        if path:
            params["path"] = path
        
        response = await self.client.get(
            f"{self.base_url}/api/files/list",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def download_file(self, file_id: int, save_path: str) -> None:
        response = await self.client.get(
            f"{self.base_url}/api/files/download/{file_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        import os
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, "wb") as f:
            f.write(response.content)
    
    async def delete_file(self, file_id: int) -> dict:
        response = await self.client.delete(
            f"{self.base_url}/api/files/{file_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def init_sync(self, files: List[FileData]) -> dict:
        request = SyncInitRequest(files=files)
        response = await self.client.post(
            f"{self.base_url}/api/sync/init",
            json=request.dict(),
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def resolve_conflict(self, sync_id: int, file_data: FileData, resolution: str) -> dict:
        from app.models import ConflictResolutionRequest
        
        request = ConflictResolutionRequest(
            sync_id=sync_id,
            file=file_data,
            resolution=resolution
        )
        
        response = await self.client.post(
            f"{self.base_url}/api/sync/conflict",
            json=request.dict(),
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def get_sync_status(self, sync_id: Optional[int] = None) -> dict:
        params = {}
        if sync_id:
            params["sync_id"] = sync_id
        
        response = await self.client.get(
            f"{self.base_url}/api/sync/status",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
