from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
import json
from app.database import get_db
from app.models import Sync, File, User
from app.utils.security import decode_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/sync", tags=["sync"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Pydantic models
class FileSyncData(BaseModel):
    path: str
    filename: str
    size: int
    file_hash: str
    last_modified: datetime
    is_directory: bool = False


class SyncInitRequest(BaseModel):
    files: List[FileSyncData]


class ConflictResolutionRequest(BaseModel):
    sync_id: int
    file: FileSyncData
    resolution: str  # keep_local, keep_remote, keep_both


class SyncResponse(BaseModel):
    success: bool
    data: dict
    message: str


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from token"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/init", response_model=SyncResponse)
async def init_sync(
    request: SyncInitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize sync operation"""
    # Create sync record
    sync_record = Sync(
        user_id=current_user.id,
        sync_type="init",
        status="pending",
        metadata=json.dumps({"files": len(request.files)})
    )
    db.add(sync_record)
    await db.commit()
    await db.refresh(sync_record)
    
    # Process files
    conflicts = []
    synced_files = []
    
    for file_data in request.files:
        # Check if file exists
        result = await db.execute(
            select(File).where(
                and_(
                    File.user_id == current_user.id,
                    File.path == file_data.path,
                    File.filename == file_data.filename
                )
            )
        )
        existing_file = result.scalar_one_or_none()
        
        if existing_file:
            # Check for conflicts
            if existing_file.file_hash != file_data.file_hash:
                conflicts.append({
                    "file": file_data.dict(),
                    "existing_file": {
                        "id": existing_file.id,
                        "path": existing_file.path,
                        "filename": existing_file.filename,
                        "size": existing_file.size,
                        "file_hash": existing_file.file_hash,
                        "last_modified": existing_file.last_modified.isoformat()
                    }
                })
            else:
                synced_files.append(existing_file)
        else:
            # Create new file record
            new_file = File(
                user_id=current_user.id,
                path=file_data.path,
                filename=file_data.filename,
                size=file_data.size,
                file_hash=file_data.file_hash,
                last_modified=file_data.last_modified,
                is_directory=file_data.is_directory
            )
            db.add(new_file)
            synced_files.append(new_file)
    
    # Update sync record
    sync_record.status = "conflict" if conflicts else "completed"
    sync_record.metadata = json.dumps({
        "files": len(request.files),
        "synced": len(synced_files),
        "conflicts": len(conflicts)
    })
    await db.commit()
    
    return SyncResponse(
        success=True,
        data={
            "sync_id": sync_record.id,
            "synced_files": [{
                "id": f.id,
                "path": f.path,
                "filename": f.filename,
                "size": f.size,
                "file_hash": f.file_hash,
                "last_modified": f.last_modified.isoformat()
            } for f in synced_files],
            "conflicts": conflicts
        },
        message="Sync completed with conflicts" if conflicts else "Sync completed successfully"
    )


@router.post("/conflict", response_model=SyncResponse)
async def resolve_conflict(
    request: ConflictResolutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve sync conflict"""
    # Get sync record
    result = await db.execute(
        select(Sync).where(
            and_(Sync.id == request.sync_id, Sync.user_id == current_user.id)
        )
    )
    sync_record = result.scalar_one_or_none()
    
    if not sync_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync record not found"
        )
    
    # Get existing file
    result = await db.execute(
        select(File).where(
            and_(
                File.user_id == current_user.id,
                File.path == request.file.path,
                File.filename == request.file.filename
            )
        )
    )
    existing_file = result.scalar_one_or_none()
    
    if request.resolution == "keep_remote":
        # Keep remote file (do nothing)
        pass
    elif request.resolution == "keep_local":
        # Update with local file data
        if existing_file:
            existing_file.size = request.file.size
            existing_file.file_hash = request.file.file_hash
            existing_file.last_modified = request.file.last_modified
            existing_file.is_directory = request.file.is_directory
        else:
            # Create new file
            new_file = File(
                user_id=current_user.id,
                path=request.file.path,
                filename=request.file.filename,
                size=request.file.size,
                file_hash=request.file.file_hash,
                last_modified=request.file.last_modified,
                is_directory=request.file.is_directory
            )
            db.add(new_file)
    elif request.resolution == "keep_both":
        # Create conflict copy
        new_filename = f"{request.file.filename}.conflict.{int(datetime.now().timestamp())}"
        conflict_file = File(
            user_id=current_user.id,
            path=request.file.path,
            filename=new_filename,
            size=request.file.size,
            file_hash=request.file.file_hash,
            last_modified=request.file.last_modified,
            is_directory=request.file.is_directory
        )
        db.add(conflict_file)
    
    # Update sync record
    sync_record.status = "completed"
    sync_record.conflict_type = "file_conflict"
    sync_record.resolution = request.resolution
    sync_record.file_path = f"{request.file.path}/{request.file.filename}"
    await db.commit()
    
    return SyncResponse(
        success=True,
        data={},
        message="Conflict resolved successfully"
    )


@router.get("/status")
async def get_sync_status(
    sync_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sync status"""
    if sync_id:
        # Get specific sync record
        result = await db.execute(
            select(Sync).where(
                and_(Sync.id == sync_id, Sync.user_id == current_user.id)
            )
        )
        sync_record = result.scalar_one_or_none()
        
        if not sync_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync record not found"
            )
        
        return {
            "success": True,
            "data": {
                "id": sync_record.id,
                "sync_type": sync_record.sync_type,
                "status": sync_record.status,
                "file_path": sync_record.file_path,
                "conflict_type": sync_record.conflict_type,
                "resolution": sync_record.resolution,
                "metadata": json.loads(sync_record.metadata) if sync_record.metadata else None,
                "created_at": sync_record.created_at.isoformat() if sync_record.created_at else None,
                "updated_at": sync_record.updated_at.isoformat() if sync_record.updated_at else None
            },
            "message": "Sync status retrieved successfully"
        }
    else:
        # Get recent sync records
        result = await db.execute(
            select(Sync)
            .where(Sync.user_id == current_user.id)
            .order_by(Sync.created_at.desc())
            .limit(10)
        )
        sync_records = result.scalars().all()
        
        return {
            "success": True,
            "data": [{
                "id": s.id,
                "sync_type": s.sync_type,
                "status": s.status,
                "file_path": s.file_path,
                "conflict_type": s.conflict_type,
                "resolution": s.resolution,
                "created_at": s.created_at.isoformat() if s.created_at else None
            } for s in sync_records],
            "message": "Sync statuses retrieved successfully"
        }
