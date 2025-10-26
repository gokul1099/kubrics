from typing import Annotated
from fastapi import Depends
from kubric_mcp.config import get_settings, Settings

from kubric_mcp.services.minio import MinIOService, get_minio_service


def get_minio_client(
        settings: Annotated[Settings, Depends(get_settings)]
) -> MinIOService:
    return get_minio_service(settings)


MinIOClient = Annotated[MinIOService, Depends(get_minio_client)]
