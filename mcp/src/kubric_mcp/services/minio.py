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

# class MinIOService:
#     """
#     Minio service for managing file storage operations.
#     Singleton pattern - one client instance for the entire app
#     """

#     def __init__(self, setting: Settings):
#         """Initialize Minio client"""
#         self.setting = setting
#         self.client = Minio(
#             endpoint=setting.MINIO_ENDPOINT,
#             access_key=setting.MINIO_ACCESS_KEY,
#             secret_key=setting.MINIO_SECRET_KEY,
#             secure=False
#         )
#         self.bucket_name = setting.MINIO_BUCKET_NAME

#     def _ensure_bucket_exists(self):
#         """create bucket if it doesn't exists"""
#         try:
#             if not self.client.bucket_exists(self.bucket_name):
#                 self.client.make_bucket(self.bucket_name)
#                 logger.info(f"Created Bucket : {self.bucket_name}")
#             else:
#                 logger.info(f"Bucket already exists: {self.bucket_name}")
#         except S3Error as e:
#             logger.error(f"Error creating bucket : {e}")
#             raise

#     def upload_file(self, file_data: BinaryIO, object_name: str, content_type: str = "video/mp4", metadata: Optional[dict] = None) -> str:
#         """
#         Upload file to MinIo
#         Args:
#             file_data: File-like object or bytes
#             object_name: Object name in MinIO(path/filename)
#             content_type: MIME type of the file
#             metadata: Additional metadata as key-value pairs

#         Return:
#             str: Object name(path) in MinIO
#         """
#         try:
#             file_data.seek(0, 2)
#             file_size = file_data.tell()
#             file_data.seek(0)

#             self.client.put_object(
#                 bucket_name=self.bucket_name,
#                 object_name=object_name,
#                 data=file_data,
#                 length=file_size,
#                 content_type=content_type,
#                 metadata=metadata or {}
#             )
#             logger.info(f"Successfully Uploaded: {object_name}")
#             return object_name
#         except S3Error as e:
#             logger.error(f"Error uploading file: {e}")
#             raise

#     def get_file(self, file_path: str):
#         try:
#             video_object = self.client.get_object(
#                 self.bucket_name, file_path).read()
#             with open()
#         except S3Error as e:
#             logger.error(f"Error in fetching object:{e}")
#             raise


# _minio_service:  None = None  # <-- define it globally


# def get_minio_service(settings: Settings) -> MinIOService:
#     global _minio_service

#     if _minio_service is None:
#         _minio_service = MinIOService(settings)
#     return _minio_service
