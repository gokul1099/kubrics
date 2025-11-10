from sqlalchemy import Column, Float, DateTime, Text, ForeignKey, UniqueConstraint, Enum as PGEnum
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from .base import Base
from enum import Enum

class FrameStatus(str,Enum):
    PENDING_IMAGE_EMBEDDING = "pending_image_embedding"
    PENDING_CAPTION_EMBEDDING = "pending_caption_embedding"
    PENDING_CAPTON = "pending_caption"
    COMPLETE = "complete"


class FrameIndex(Base):
    __tablename__ = "frames_index"

    id= Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id= Column(UUID(as_uuid=True), ForeignKey("video_index.id", ondelete="CASCADE"), nullable=False)
    timestamp_seconds = Column(Float, nullable=False)
    caption= Column(Text, nullable=False)
    caption_embedding = Column(VECTOR(1536), nullable=False)
    frame_embedding = Column(VECTOR(512), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc),onupdate=datetime.now(timezone.utc), nullable=False)
    status = Column(PGEnum(FrameStatus), nullable=False, default="pending_image_embedding")

    
    ## relationships 
    video = relationship("VideoIndex", back_populates="frames")

    ## constraints
    __table_args__ = (
        UniqueConstraint("video_id", "timestamp_seconds", name="unique_frame_timestamp"),
    )