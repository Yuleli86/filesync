from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server Configuration
    SERVER_URL: str = "http://localhost:8000"
    WS_URL: str = "ws://localhost:8000/ws/sync"
    
    # Sync Configuration
    SYNC_DIR: str = "./sync"
    CHUNK_SIZE: int = 8192
    SYNC_INTERVAL: int = 5
    
    # File Watching
    WATCH_INTERVAL: float = 1.0
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
