import logging
import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings

log = logging.getLogger("uvicorn")


class Settings(BaseSettings):

    OPIK_API_KEY: str
    OPIK_WORKSPACE: str
    OPIK_PROJECT: str

    # OPENAI Config
    OPENAI_API_KEY: str
    AUDIO_TRANSCRIPT_MODEL: str = "gpt-4o-mini-transcribe"
    IMAGE_CAPTION_MODEL: str = "gpt-4o-mini"

    # Video Ingestion Config
    SPLIT_FRAMES_COUNT: int = 45
    AUDIO_CHUNK_LENGTH: int = 10
    AUDIO_OVERLAP_SECONDS: int = 1
    AUDIO_MIN_CHUNK_DURATION_SECONDS: int = 1

    # Transcription Config
    TRANSCRIPT_SIMILARITY_EMDB_MODEL: str = "text-embedding-3-small"

    # Image EMBD Config
    IMAGE_EMDB_MODEL: str = "openai/clip-vit-base-patch32"

    # Image Captioning CONFIG
    IMAGE_RESIZE_WIDTH: int = 1024
    IMAGE_RESIZE_HEIGHT: int = 768
    CAPTION_SIMILARITY_EMBD_MODEL: str = "text-embedding-3-small"

    CAPTION_MODEL_PROMPT: str = "Describe what is happening in the image"
    DELTA_SECONDS_FRAME_INTERVAL: float = 5.0

    # Video Search Engine config
    VIDEO_CLIP_SPEECH_SEARCH_TOP_K: int = 1
    VIDEO_CLIP_CAPTION_SEARCH_TOP_K: int = 1
    VIDEO_CLIP_IMAGE_SEARCH_TOP_K: int = 1
    QUESTION_ANSWER_TOP_K: int = 3


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get the application settings

    Returns:
        Settings: The application Settings
    """
    return Settings()
