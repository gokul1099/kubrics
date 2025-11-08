from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from kubric_mcp.models import VideoIndex, AudioIndex
from datetime import datetime, timezone
from kubric_mcp.models.audio import AudioStatus

import uuid


class AudioService:
    """
    DB services for audio
    """
    def __init__(self, session: Session):
        self.session = session

    def _create_entry(self, video_id: uuid.UUID, audio_chunks_info, ) -> AudioIndex:
        """
        Create a bulk entry for audio chunks in database for ongoing vidoe processing
        """
        try:
            bulk_data = []
            for audio_info in audio_chunks_info:
                chunk = AudioIndex(
                    video_id = video_id,
                    chunk_index = audio_info["chunk_index"],
                    start_time = audio_info["start_time"],
                    end_time = audio_info["end_time"],
                    status = AudioStatus.PENDING_TRANSCRIPTION,
                )
                bulk_data.append(chunk)
            
            
            self.session.add_all(bulk_data)
            self.session.commit()

            for chunk in bulk_data:
                self.session.refresh(chunk)
            
            print(f"✅  [Audio Service] audio chunk inserted : {len(bulk_data)}")
            return bulk_data
        except Exception as e:
            self.session.rollback()
            print(f"❌  [Audio Service] audio chunk insertion failed: {e}")
            raise
    
    def _update_transcription(self,video_id: uuid.UUID, transcriptions):

        audio_chunks = self.session.query(AudioIndex).filter(
            AudioIndex.video_id == video_id
        ).all()
        
        chunk_id_map = {chunk.chunk_index : chunk.id for chunk in audio_chunks}

        updates = []
        try:
            for transcription in transcriptions:
                chunk_id = chunk_id_map.get(transcription["chunk_index"])
                if chunk_id:
                    updates.append({
                        "id":chunk_id,
                        "transcription" : transcription,
                        "status": AudioStatus.PENDING_EMBEDDING,
                        "updated_at": datetime.now(timezone.utc)
                    })
            
            self.session.bulk_update_mappings(AudioIndex, updates)
            self.session.commit()
            print(f"✅  [Audio Service] Transcriptions updated successfully")
        
        except Exception as e:
            self.session.rollback()
            print(f"❌  [Audio Service] audio transcription insertion failed: {e}")
            raise


            

