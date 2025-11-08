from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, CheckConstraint, UniqueConstraint, Enum as PGEnum
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum
import uuid
from .base import Base


class AudioStatus(str,Enum):
    PENDING_TRANSCRIPTION = "pending_transcription"
    PENDING_EMBEDDING = "pedning_embedding"
    COMPLETE = "complete"

class AudioIndex(Base):
    __tablename__ = "audio_index"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("video_index.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    transcript_embedding = Column(VECTOR(1536))
    transcription_text = Column(String(255))
    status = Column(PGEnum(AudioStatus), nullable=False, default="pending_transcription")
    create_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc),nullable=False)

    ## relationships
    video = relationship("VideoIndex", back_populates="audio_chunks")

    # contraints
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="valid_time_range"),
        UniqueConstraint("video_id", "chunk_index", name="unique_chunk"),
    )
