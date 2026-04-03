from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./sync_server.db"
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload Configuration
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 104857600  # 100MB
    
    # Sync Configuration
    CHUNK_SIZE: int = 8192  # 8KB
    SYNC_INTERVAL: int = 5  # seconds
    
    # Security
    ENCRYPTION_KEY: str = "your-encryption-key-here"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
