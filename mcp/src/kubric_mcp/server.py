from fastmcp import FastMCP
import click
import tempfile
import os
from kubric_mcp.tools import process_video
from kubric_mcp.config import get_settings
from kubric_mcp.services.minio import get_minio_service
from kubric_mcp.video.ingestion.video_processor import VideoProcessor
import asyncio
from kubric_mcp.db import init_db, get_session
from concurrent.futures import ThreadPoolExecutor
from kubric_mcp.services import VideoService

mcp = FastMCP("Kubric_MCP")

executer = ThreadPoolExecutor(max_workers=5)


@mcp.tool(name="processsss_video")
async def processss_video(video_path: str) -> str:
    settings = get_settings()
    minio_client = get_minio_service(settings)
    db_session = next(get_session())

    video_service = VideoService(session=db_session)

    # metadata = minio_client.stat_object(
    #     bucket_name=settings.MINIO_BUCKET_NAME, object_name=video_path)
    videoProcessor = VideoProcessor(
        minio_client=minio_client, video_path=video_path)
    # video_service._make_entry(minio_path=video_path, filename=metadata.object_name)

    video_processor_task = asyncio.create_task(
        videoProcessor._extract_frames())
    videoProcessor.background_task.add(video_processor_task)
    video_processor_task.add_done_callback(
        videoProcessor.background_task.discard)
    return f"Video Processing started for {metadata.object_name}"


@click.command()
@click.option("--host", default="0.0.0.0", help="Enter the host number you want to run the MCP")
@click.option("--port", default=8081, help="Enter the port number you want MCP to run")
@click.option("--transport", default="streamable-http")
def run_mcp(port, host, transport):
    """
    Run FastMcp server with provided port, host and transport
    """
    print("initializing database")
    init_db()
    session = next(get_session())
    print(session,"session initiated")
    session.close()
    print("Database connection established")
    mcp.run(host=host, port=port, transport=transport)


if __name__ == "__main__":
    run_mcp()
