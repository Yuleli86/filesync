from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    size = Column(BigInteger, default=0)
    file_hash = Column(String, nullable=False)
    last_modified = Column(DateTime(timezone=True), nullable=False)
    is_directory = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="files")
