import io
import shutil
import sys
from contextlib import asynccontextmanager
from uuid import uuid4
from pathlib import Path
from enum import Enum

import click
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# from loguru import logger
import logging
from kubric_api.models import VideoUploadResponse
from kubric_api.models import ProcessVideoRequest
from fastmcp.client import Client
from kubric_api.config import get_settings
from kubric_api.dependencies import MinIOClient
import uuid

# Get the directory where this file is located
BASE_DIR = Path(__file__).parent
SHARED_MEDIA_DIR = BASE_DIR / "shared_media"
LOGS_DIR = BASE_DIR / "logs"

settings = get_settings()

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)

# Configure loguru logger
# logger.remove()  # Remove default handler
logger = logging.getLogger("uvicorn")


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_FOUND = "not_found"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bg_task_status = dict()
    yield
    # app.state.agent.reset_memory()

app = FastAPI(
    title="Kubric API",
    description="An AI-Powered sports Assistance API using openAI",
    docs_url="/docs",
    lifespan=lifespan
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Read and log the request body
    body = await request.body()

    # Create a new receive function that returns the body
    async def receive():
        return {"type": "http.request", "body": body}

    # Replace the request's receive with our custom one
    request._receive = receive

    # Log the request details
    try:
        body_str = body.decode('utf-8')
        logger.info(
            f"📥 {request.method} {request.url.path} | Body: {body_str}")
    except Exception as e:
        logger.info(
            f"📥 {request.method} {request.url.path} | Body: <binary data>")

    # Process the request
    response = await call_next(request)
    logger.info(
        f"📤 {request.method} {request.url.path} | Status: {response.status_code}")

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

app.mount("/media", StaticFiles(directory=str(SHARED_MEDIA_DIR)), name="media")


@app.get("/")
async def root():
    """
    Root endpoints that redirect to API documentation
    """
    return {"message": "Welcome to Kubrics API"}


@app.post("/upload-video", response_model=str)
async def upload_video(file: UploadFile = File(...), minio: MinIOClient = None):
    """
    Upload a video and return the path
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="no file upload")
    video_id = uuid.uuid4()
    file_ext = Path(file.filename).suffix.lower()
    object_name = f"videos/{video_id}/{file_ext}"
    content = await file.read()
    logger.info("uploading ")
    try:
        object_name = minio.upload_file(
            file_data=io.BytesIO(content),
            object_name=object_name,
            content_type=file.content_type,
            metadata={
                "original_filename": file.filename,
                "video_id": str(video_id)
            }
        )

        # return VideoUploadResponse(message="Video uploaded successfully", video_path=str(object_name))
        return str(object_name)
    except Exception as e:
        logger.error("Error uploading videos : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-video")
async def process_video(request: ProcessVideoRequest, bg_tasks: BackgroundTasks, fastapi_request: Request):
    """
    Process a video and return the results
    """
    task_id = str(uuid4())
    bg_task_status = fastapi_request.app.state.bg_task_status

    # Log comprehensive request details
    logger.info(f"Received process_video request: {request.model_dump()}")

    async def background_process_video(video_path: str, task_id: str):
        """
        Background task to process the video
        """
        bg_task_status[task_id] = TaskStatus.IN_PROGRESS

        if not Path(video_path).exists():
            bg_task_status[task_id] = TaskStatus.FAILED
            raise HTTPException(status_code=404, detail="Video file not found")

        try:
            mcp_client = Client(settings.MCP_SERVER)
            async with mcp_client:
                _ = await mcp_client.call_tool("process_video", {video_path: request.video_path})
        except Exception as e:
            logger.error(f"Error processing video {video_path}: {e}")
            bg_task_status[task_id] = TaskStatus.FAILED
            raise HTTPException(status_code=500, detail=str(e))
        bg_task_status[task_id] = TaskStatus.COMPLETED
    logger.error(f"Path to video, {request.video_path}")
    bg_tasks.add_task(background_process_video, request.video_path, task_id)
    # return ProcessVideoResponse(message="Task completed Successfully", task_id=task_id)
    return True


@click.command
@click.option("--port", default=8080, help="FastAPI server port")
@click.option("--host", default="localhost", help="FastApi server host")
def run_api(port, host):
    import uvicorn
    log_config_path = BASE_DIR / "utils" / "log_conf.yml"
    uvicorn.run("kubric_api.api:app", host=host, port=port,
                loop="asyncio", reload=True, log_config=str(log_config_path))


if __name__ == "__main__":
    run_api()
