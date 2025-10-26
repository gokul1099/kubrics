import fastapi
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import TEXT, Column, BIGINT, VECTOR
import uuid
from pgvector.sqlalchemy import Vector
from typing import List


class FrameIndex(SQLModel, table=True):
    __tablename__ = "frame_index"

    frame_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True)),
        primary_key=True,
        index=True,
        nullable=False
    )
    video_id: uuid.UUID = Field(
        foreign_key="video_registry.video_id",
        nullable=False,
        index=True
    )
    frame_timestamp_ms: BIGINT
    resized_frame_ref: TEXT
    image_embedding: List[float] = Field(
        sa_column=Column(Vector(1536))
    )
    caption_text: TEXT
    caption_embedding: List[float] = Field(
        sa_column=Column(Vector(1536))
    )
