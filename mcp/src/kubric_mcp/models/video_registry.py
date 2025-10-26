from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import TEXT, Column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime
import uuid


class VideoRegistry(SQLModel, table=True):
    __tablename__ = "video_registry"

    video_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
        primary_key=True,
        index=True,
        nullable=False
    )
    video_name: str = Field(max_length=255, index=True)
    video_path: str = Field(sa_column=Column(TEXT))
    processing_status: str = Field(max_length=255)
