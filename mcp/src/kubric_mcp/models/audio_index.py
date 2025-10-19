from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import TEXT, Column, BIGINT, VECTOR, NUMERIC
from datetime import datetime
import uuid
from pgvector.sqlalchemy import Vector
from typing import List


class AudioIndex(SQLModel, table=True):
    chunk_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True)),
        primary_key=True,
        index=True,
        nullable=False,
    )
    video_id: uuid.UUID = Field(
        foreign_key="video_registry.video_id",
        nullable=False,
        index=True,
    )
    start_time_sec: NUMERIC
    end_time_sec: NUMERIC
    chunk_text: TEXT
    audio_embedding: List[float] = Field(
        sa_column=Column(Vector(1536), nullable=False)
    )
