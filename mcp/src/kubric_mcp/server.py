from fastmcp import FastMCP
import click

mcp = FastMCP("VideoProcessor")


@mcp.tool()
def process_video(video_path: str) -> str:
    """
    Process a video file and prepare it for searching

    Args:
        video_path: Path to the video file to process

    Returns:
        Success message indicating the video was processed
    """
    from kubric_mcp.tools import process_video as _process_video
    return _process_video(video_path)


@click.command()
@click.option("--host", default="0.0.0.0", help="Enter the host number you want to run the MCP")
@click.option("--port", default=8081, help="Enter the port number you want MCP to run")
@click.option("--transport", default="streamable-http")
def run_mcp(port, host, transport):
    """
    Run FastMcp server with provided port, host and transport
    """
    mcp.run(host=host, port=port, transport=transport)


if __name__ == "__main__":
    run_mcp()
