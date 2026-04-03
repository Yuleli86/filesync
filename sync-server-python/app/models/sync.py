from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Sync(Base):
    __tablename__ = "syncs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sync_type = Column(String, nullable=False)  # init, incremental, full
    status = Column(String, nullable=False)  # pending, completed, conflict, failed
    file_path = Column(String, nullable=True)
    conflict_type = Column(String, nullable=True)
    resolution = Column(String, nullable=True)
    sync_metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="syncs")
