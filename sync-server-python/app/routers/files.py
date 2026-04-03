from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import os
import aiofiles
from datetime import datetime
from app.database import get_db
from app.models import File, User
from app.utils.security import decode_access_token
from app.config import get_settings
from pydantic import BaseModel

router = APIRouter(prefix="/api/files", tags=["files"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
settings = get_settings()


# Pydantic models
class FileCreate(BaseModel):
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
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    success: bool
    data: List[FileResponse]
    pagination: dict
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


@router.post("/upload")
async def upload_file(
    file_data: FileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload file metadata"""
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
        # Update existing file
        existing_file.size = file_data.size
        existing_file.file_hash = file_data.file_hash
        existing_file.last_modified = file_data.last_modified
        existing_file.is_directory = file_data.is_directory
        await db.commit()
        await db.refresh(existing_file)
        
        return {
            "success": True,
            "data": existing_file,
            "message": "File updated successfully"
        }
    else:
        # Create new file
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
        await db.commit()
        await db.refresh(new_file)
        
        return {
            "success": True,
            "data": new_file,
            "message": "File uploaded successfully"
        }


@router.post("/upload-content/{file_id}")
async def upload_file_content(
    file_id: int,
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload actual file content"""
    # Check if file exists and belongs to user
    result = await db.execute(
        select(File).where(
            and_(File.id == file_id, File.user_id == current_user.id)
        )
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Save file to disk
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{db_file.id}_{db_file.filename}")
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    return {
        "success": True,
        "message": "File content uploaded successfully"
    }


@router.get("/list", response_model=FileListResponse)
async def list_files(
    path: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List files for current user"""
    # Build query
    query = select(File).where(File.user_id == current_user.id)
    
    if path:
        query = query.where(File.path == path)
    
    # Get total count
    count_query = select(File).where(File.user_id == current_user.id)
    if path:
        count_query = count_query.where(File.path == path)
    
    result = await db.execute(count_query)
    total = len(result.scalars().all())
    
    # Get files with pagination
    query = query.offset(offset).limit(limit).order_by(File.last_modified.desc())
    result = await db.execute(query)
    files = result.scalars().all()
    
    return FileListResponse(
        success=True,
        data=files,
        pagination={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(files) < total
        },
        message="Files listed successfully"
    )


@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download file"""
    from fastapi.responses import FileResponse
    
    # Check if file exists and belongs to user
    result = await db.execute(
        select(File).where(
            and_(File.id == file_id, File.user_id == current_user.id)
        )
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Build file path
    file_path = os.path.join(settings.UPLOAD_DIR, f"{db_file.id}_{db_file.filename}")
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        file_path,
        filename=db_file.filename,
        media_type='application/octet-stream'
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete file"""
    # Check if file exists and belongs to user
    result = await db.execute(
        select(File).where(
            and_(File.id == file_id, File.user_id == current_user.id)
        )
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Delete file from disk
    file_path = os.path.join(settings.UPLOAD_DIR, f"{db_file.id}_{db_file.filename}")
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    await db.delete(db_file)
    await db.commit()
    
    return {
        "success": True,
        "message": "File deleted successfully"
    }
