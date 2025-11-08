from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
from datetime import datetime
import logging

from pathlib import Path
from kubric_mcp.config import Settings

logger = logging.getLogger("uvicorn")


def get_minio_service(setting: Settings):
    return Minio(
        endpoint=setting.MINIO_ENDPOINT,
        access_key=setting.MINIO_ACCESS_KEY,
        secret_key=setting.MINIO_SECRET_KEY,
        secure=False
    )
