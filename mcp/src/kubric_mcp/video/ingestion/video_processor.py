import asyncio
from minio import Minio
from moviepy import VideoFileClip
import cv2
from pathlib import Path
import sys
import subprocess
from groq import Groq
import json
from openai import OpenAI
import pybase64
import tempfile
import numpy as np
from kubric_mcp.config import get_settings
from transformers import CLIPProcessor, CLIPModel
import torch
import io
from PIL import Image
from tqdm import tqdm
from scipy.io import wavfile
from minio.error import S3Error
from pydub import AudioSegment
from kubric_mcp.models import VideoIndex, AudioIndex, FrameIndex, AudioStatus, VideoStatus
from kubric_mcp.services import AudioService, VideoService
from kubric_mcp.db import get_session
from tqdm.asyncio import tqdm
from enum import Enum
from sqlalchemy import select

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
print(DEVICE, "device")

class VideoPorcessorStatus(str, Enum):
    PENDING_EMBEDDING = "pending_embedding"
    PENDING_TRANSCRIPTION = "peding_transcription"
    PROCESSING_DONE = "done"
    PENDING = "pending"
    
class VideoProcessor():
    def __init__(self, minio_client: Minio, video_path: str):
        self.minio_client = minio_client
        self.video_path = video_path
        self.temp_video_path = None
        self.temp_audio_path = None
        self.settings = get_settings()
        self.bucket_name = self.settings.MINIO_BUCKET_NAME
        self.frames = None
        self.openai_client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.groq_client = Groq(api_key=self.settings.GROQ_API_KEY)
        self.audio_transcripts = []
        self.background_task = set()
        self.db_session = next(get_session())
        self.audio_service = AudioService(session=self.db_session)
        self.video_service = VideoService(session=self.db_session)
        self.video_id = None
        self._load_video()


    def _load_video(self):
        suffix = Path(self.video_path).suffix
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        self.temp_video_path = temp_file.name
        temp_file.close()
        self.minio_client.fget_object(
            self.bucket_name,
            self.video_path,
            self.temp_video_path
        )
        metadata = self.minio_client.stat_object(
        bucket_name=self.settings.MINIO_BUCKET_NAME, object_name=self.video_path)
        is_video_exists = self.db_session.query(VideoIndex).filter(VideoIndex.minio_path == self.video_path).first()
        if(not is_video_exists):
            video_entry = self.video_service._make_entry(minio_path=self.video_path, filename=metadata.object_name)
            self.video_id = video_entry.id
            print("✅  [Video Processor]: Video entry made in databaase")

        else:
            print("✅  [Video Processor]: Video already exists in databaase")

            self.video_id = is_video_exists.id

        return
    
    def _check_status(self):
        video = self.db_session.query(VideoIndex).filter(VideoIndex.id == self.video_id).first()
        if(video.status == VideoStatus.PROCESSING):
            audio = self.db_session.query(AudioIndex).filter(AudioIndex.video_id == self.video_id).all()
            if any(item.status == AudioStatus.PENDING_EMBEDDING for item in audio):
                print("[Video Processor]: Audio transcription done. start trnascription emebedding")
                return VideoPorcessorStatus.PENDING_EMBEDDING
            if any(item.status == AudioStatus.PENDING_TRANSCRIPTION for item in audio):
                print("[Video Processor]: start trnascription")
                return VideoPorcessorStatus.PENDING_TRANSCRIPTION
        elif(video.status == VideoStatus.FAILED or video.status == VideoStatus.UPLOADED):
            print("[Video Processing]: start video proecssing")
            return VideoPorcessorStatus.PENDING


    def _extract_frames(self):
        if not self.temp_video_path:
            raise ValueError("Video path not found")

        cap = cv2.VideoCapture(self.temp_video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # compute frame indices to extract uniformly

        frame_indices = np.linspace(
            0, total_frames - 1, 2, dtype=int)

        frames = []
        for i, frame_idx in enumerate(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
            else:
                raise ValueError(
                    f"VideoProcessor: _extract_frames: could not read frame {frame_idx}")
        cap.release()
        self.frames = frame
        print(f"✅ [Video Processor] Extracted frames : {len(frames)}")
        print("[Video Processor] Starting to audio processing in background")
        # self._generate_embedding_for_frames()
        self.__start_audio_processsing()

    def _start_audio_processsing(self):
        audio_task = asyncio.create_task(self._process_audio())
        self.background_task.add(audio_task)
        audio_task.add_done_callback(self.background_task.discard)
        return 

    async def _process_audio(self):
        """
        Extract the audio from the video and start audio processing
        """
        audio = AudioSegment.from_file(self.temp_video_path)
        total_duration_ms = len(audio)
        chunk_duration_ms = self.settings.AUDIO_CHUNK_LENGTH * 1000
        audio_chunks_info =[]
        for i, start_ms in enumerate(range(0, total_duration_ms, chunk_duration_ms)):
            end_ms = min(start_ms + chunk_duration_ms, total_duration_ms)
            audio_chunks_info.append({"start_time": start_ms, "end_time": end_ms, "chunk_index":i})
        coroutines = [
            self._transcribe_audio(audio, chunk['start_time'], chunk['end_time'], chunk['chunk_index']) 
            for chunk in audio_chunks_info
        ]
        print("✅ [Video Processor] Audio Chunk Info prepared", audio_chunks_info)
        self.audio_service._create_entry(self.video_id, audio_chunks_info=audio_chunks_info)
        print(f"[Video Processor] Processing {len(coroutines)} chunks...")
        results=[]
        with tqdm(total= len(coroutines), desc="[Video Processor]: transcribing audio chunks") as pbar:
            for coro in asyncio.as_completed(coroutines):
                result = await coro
                results.append(result)
                pbar.update(1)
        self.audio_service._update_transcription(self.video_id, transcriptions=results)
        return True


    def _store_audio_to_minio(self,buffer, index):
        try:
            if not self.minio_client.bucket_exists("audio"):
                self.minio_client.make_bucket("audio")
                print(f"Bucket created")
        except S3Error as e:
            print(f"Error {e}")
        bucket_name= "audio"
        try:
            self.minio_client.put_object(
                bucket_name=bucket_name,
                object_name= index,
                content_type="audio/wav",
                data=buffer,
                length =buffer.getbuffer().nbytes
            )
            print(f"audio {index} stored")
        except S3Error as e:
            print(f"Error in storing {e}")

    async def _transcribe_audio(self, audio, start_ms, end_ms, index):
        chunk = audio[start_ms: end_ms]
        chunk = chunk.set_channels(1)
        chunk = chunk.set_frame_rate(16000)

        buffer = io.BytesIO()
        chunk.export(buffer, format="wav")
        buffer.seek(0)
        buffer.name = f"chunk_{index}.wav"
        try:
            transcription = self.groq_client.audio.transcriptions.create(
                model=self.settings.AUDIO_TRANSCRIPT_MODEL,
                file=buffer,
                response_format="json"
            )
            return {
                'chunk_index': index,
                'transcription': transcription.text
            }
        except Exception as e:
            print(f"Error transcribing chunk {index}: {e}")
            return None
        finally:
            buffer.close()

    def _generate_embedding_for_transription(self):
        audio_transcriptions = self.db_session.execute(select(AudioIndex.transcription_text, AudioIndex.id)
                                                       .where(AudioIndex.video_id == self.video_id)
                                                       .where(AudioIndex.status == AudioStatus.PENDING_EMBEDDING)).all()
        transcription_list = [item[0] for item in audio_transcriptions]
        transcription_ids = [item[1] for item in audio_transcriptions]

        results= []
        
        try:
            for index in tqdm(range(0, len(transcription_list)), desc="Generating embedding for transcriptions"):
                embedding_response = self.openai_client.embeddings.create(
                    model=self.settings.TRANSCRIPT_SIMILARITY_EMDB_MODEL,
                    input= transcription_list[index]
                )
                results.append({"id":transcription_ids[index], "embedding": embedding_response.data[0].embedding})

            self.audio_service._update_transcription_embedding(embdeddings_info=results)
            print("✅ [Video Processor] embedding generated for transcription")
        except Exception as e:
            print('❌ [Video Processor] embedding generation failed',e)


    def _split_audio(self, audio):
        duration = audio.duration
        chunks_info = []
        current_start = 0

        while current_start < duration:
            chunk_end = min(
                current_start + self.settings.AUDIO_CHUNK_LENGTH, duration)
            chunks_info.append({
                "start": current_start,
                "end": chunk_end,
                "index": len(chunks_info)
            })
            current_start += (self.settings.AUDIO_CHUNK_LENGTH -
                              self.settings.AUDIO_OVERLAP_SECONDS)
        print(f"created {len(chunks_info)} overlapping chunks")
        return chunks_info

    def _encode_image(self, frame):
        """
        Encoding image for passing the image as argument into openai model for generating image embedding
        """
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            raise ValueError(
                "VideoProcessor: _encode_image -> Error in encoding image using cv2")
        encoded_bytes = pybase64.b64encode(buffer)
        return encoded_bytes.decode("utf-8")

    def _generate_embedding_for_frames(self):
        pil_frames = [Image.fromarray(cv2.cvtColor(
            f, cv2.COLOR_BGR2RGB)) for f in self.frames]

        model = CLIPModel.from_pretrained(
            self.settings.IMAGE_EMDB_MODEL).to(DEVICE)
        processor = CLIPProcessor.from_pretrained(
            self.settings.IMAGE_EMDB_MODEL)

        batch_szie = 16
        image_embeddings = []
        for i in tqdm(range(0, len(pil_frames), batch_szie), desc="Embedding frames"):
            batch = pil_frames[i: i+batch_szie]
            inputs = processor(images=batch, return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                features = model.get_image_features(**inputs)
                features = features / features.norm(p=2, dim=1, keepdim=True)
                image_embeddings.append(features)
        image_embeddings = torch.cat(image_embeddings, dim=0)

        return
