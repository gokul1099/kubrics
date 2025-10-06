from typing import Dict
from uuid import uuid4
from loguru import logger
import os

from kubric_mcp.video.ingestion.tools import extract_video_clip

logger = logger.bind(name="MCPVideoTools")


def process_video(video_path: str) -> str:
    """
    Process a video file and prepare it for searching

    Args:
        video_path(str): Path to the video file to process

    Returns:
        str: success message indicating the video was processed

    Raises:
        ValueError: If the video file cannot be found or processed
    """
    exists = os.path.exists(
        video_path)  # need to changes this to video-processor

    if exists:
        logger.info(f"Video index for `{video_path}` already exists ")
        return False
    extraced = extract_video_clip(
        video_path=video_path, start_time='0.49', end_time='2.10', output_path="./data/output.mp4")
    return True
