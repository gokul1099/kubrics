from moviepy import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


def extract_video_clip(video_path: str, start_time: float, end_time: float, output_path: str = None) -> VideoFileClip:
    if start_time >= end_time:
        raise ValueError("start_time must be less than end_time")
    try:
        extracted_clip = ffmpeg_extract_subclip(
            video_path, start_time, end_time, output_path)
        return extracted_clip

    except e:
        raise IOError(f"Failed to extract subclip: {str(e)}")
