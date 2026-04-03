from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class AuthResponse(BaseModel):
    success: bool
    data: dict
    message: str


class FileData(BaseModel):
    path: str
    filename: str
    size: int
    file_hash: str
    last_modified: datetime
    is_directory: bool = False


class FileResponse(BaseModel):
    id: int
    path: str
    filename: str
    size: int
    file_hash: str
    last_modified: datetime
    is_directory: bool
    created_at: datetime


class FileListResponse(BaseModel):
    success: bool
    data: list
    pagination: dict
    message: str


class SyncInitRequest(BaseModel):
    files: List[FileData]


class SyncResponse(BaseModel):
    success: bool
    data: dict
    message: str


class ConflictResolutionRequest(BaseModel):
    sync_id: int
    file: FileData
    resolution: str


class WebSocketMessage(BaseModel):
    type: str
    data: Optional[dict] = None
    message: Optional[str] = None
