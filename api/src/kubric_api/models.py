from pydantic import BaseModel, Field


class VideoUploadResponse(BaseModel):
    message: str
    video_path: str | None = None
    task_id: str | None = None


class ProcessVideoRequest(BaseModel):
    video_path: str


class ProcessVideoResponse(BaseModel):
    message: str
    task_id: str
