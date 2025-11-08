from sqlalchemy import Column, String, Float, BigInteger, DateTime, Enum as PGEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from enum import Enum
from .base import Base


class VideoStatus(str,Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoIndex(Base):
    __tablename__ = "video_index"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename= Column(String(255))
    minio_bucket= Column(String(255),  default="video")
    minio_path= Column(String(500),  unique=True)
    mime_type = Column(String(50))
    duration_seconds= Column(Float)
    file_size_bytes = Column(BigInteger)
    status = Column(PGEnum(VideoStatus),  default="uploaded")
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    audio_processing_completed = Column(Boolean, unique=False, default=False)
    frame_processing_completed = Column(Boolean, unique=False, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    ##Relationships
    audio_chunks = relationship("AudioIndex", back_populates="video", cascade="all, delete-orphan")
    frames = relationship("FrameIndex", back_populates="video", cascade="all, delete-orphan")