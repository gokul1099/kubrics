from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from kubric_mcp.models import VideoIndex
from kubric_mcp.models.video import VideoStatus
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid


class VideoService:
    """DB services for video"""
    def __init__(self, session: Session):
        self.session = session
    
    
    def _check_video_exists(self, minio_path:str):
        """
        Check the video exisits
        """
        existing = self.session.query(VideoIndex).filter(
            VideoIndex.minio_path == minio_path
        )
        if existing:
            """If video exists need to check whethere the processing is already done. 
                dont need to do the processing the retrival can be done else need to schedule the processing
            """
            return True
        return False
    
    def _make_entry(self, minio_path:str, filename:str, minio_bucket:str ="video") -> VideoIndex:
        """
            Create video record and mark as processing
            This run before retrieving from minio to ensure path is saved
        """
        try:
            video = VideoIndex(
                filename = filename,
                minio_bucket = minio_bucket,
                minio_path = minio_path,
                status = VideoStatus.PROCESSING,
                processing_started_at = datetime.now(timezone.utc)
            )

            self.session.add(video)
            self.session.commit()
            self.session.refresh(video)

            print(f"✅ [Video Service] Video Entry Sucessfull. {video.id}: {video.minio_path}")
            return video
        except Exception as e:
            self.session.rollback()
            print(f"❌ [Video Service] error while making video entry: {e}")
            raise
    def _update_video_metadata(self, video_id:uuid.UUID, file_size_bytes: int, duration_seconds: float, mime_type: str) -> VideoIndex:
                """
                the video metadata will be stored after the video is retrieved from the minio bucket.
                """
                video = self.session.query(VideoIndex).filter(
                     VideoIndex.id == id
                ).first()

                if not video:
                     raise ValueError(f"❌ [Video Service] video not found. Error while storing metadata")
                try:
                     video.file_size_bytes = file_size_bytes
                     video.duration_seconds = duration_seconds
                     video.mime_type = mime_type
                     video.updated_at = datetime.now(timezone.utc)
                     
                     self.session.commit()
                     self.session.refresh(video)

                     print(f"✅ [Video Service]  metadata updated for video {video.id} ")
                     return video

                except Exception as e:
                     self.session.rollback()
                     print(f"❌ [Video Service] error in updating metadata: {e}")
                     raise

    def _complete_processing(self, video_id: uuid.UUID, status: VideoStatus =VideoStatus.COMPLETED) -> VideoIndex:
         """
         Mark the video processing as completed 
         """       
         video = self.session.query(VideoIndex).filter(
              VideoIndex.id == id
         ).first()

         if not video:
            raise ValueError(f"❌ [Video Service] video not found. Error while storing metadata")

         try:
              video.status = status
              video.processing_completed_at = datetime.now(timezone.utc)
              video.updated_at = datetime.now(timezone.utc)

              self.session.commit()
              self.session.refresh(video)

              print(f"✅ [Video Service] Completed processing video {video.id} with status: {status}")
              return video
         except Exception as e:
              self.session.rollback()
              print(f"❌ [Video Service] error in completing processing {e}") 
              raise
    
    def _mark_as_failed(self, video_id: uuid.UUID, error_message: Optional[str]= None):
         """
         Mark video as failed
         """
         return self._complete_processing(video_id=video_id, status=VideoStatus.FAILED)
