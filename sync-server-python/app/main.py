from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import init_db, get_db
from app.models import User
from app.utils.security import decode_access_token
from app.routers import auth, files, sync
from app.websocket.handler import handle_websocket

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("Starting up...")
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="File Sync Server",
    description="A file synchronization server with real-time sync capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(sync.router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user_ws(token: str, db: AsyncSession) -> User:
    """Get current user from WebSocket token"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    username = payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@app.websocket("/ws/sync")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time sync"""
    async with AsyncSessionLocal() as db:
        try:
            # Authenticate user
            user = await get_current_user_ws(token, db)
            # Handle WebSocket connection
            await handle_websocket(websocket, user.id)
        except HTTPException:
            await websocket.close(code=4001, reason="Authentication failed")
        except Exception as e:
            print(f"WebSocket error: {e}")
            await websocket.close(code=4000, reason="Internal server error")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "File Sync Server API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


from datetime import datetime
from app.database import AsyncSessionLocal

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )
