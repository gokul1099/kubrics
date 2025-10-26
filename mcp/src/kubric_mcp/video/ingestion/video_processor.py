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

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
print(DEVICE, "device")


class VideoProcessor():
    def __init__(self, minio_client: Minio, video_path: str):
        self.minio_client = minio_client
        self.video_path = video_path
        self.temp_video_path = None
        self.temp_audio_path = None
        self.settings = get_settings()
        self.bucket_name = self.settings.MINIO_BUCKET_NAME
        self.frames = None
        self._load_video()
        self.openai_client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.groq_client = Groq(api_key=self.settings.GROQ_API_KEY)
        self.audio_transcripts = []
        self.background_task = set()

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
        return

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
        print(f"Extracted frames : {len(frames)}")
        print("Starting to audi processing in background")
        # self._generate_embedding_for_frames()

        audio_task = asyncio.create_task(self._process_audio())
        self.background_task.add(audio_task)
        audio_task.add_done_callback(self.background_task.discard)
        return

    async def _process_audio(self):
        """
        Extract the audio from the video and start audio processing
        """
        video_clip = VideoFileClip(self.temp_video_path)
        temp_audio = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        self.temp_audio_path = temp_audio.name
        video_clip.audio.write_audiofile(self.temp_audio_path)
        split_info = self._split_audio(video_clip.audio)
        tasks = [
            self._transcribe_audio(video_clip.audio, chunk["start"], chunk["end"], chunk["index"]) for chunk in split_info
        ]
        print(split_info, "infor")
        # results = await asyncio.gather(*tasks)
        # print(f"Audio Processing completed: {results}")
        video_clip.close()

    async def _transcribe_audio(self, audio, start, end, index):
        subclip = audio.subclipped(start, end)
        audio_array = subclip.to_soundarray(fps=16000)

        if len(audio_array.shape) > 1:
            audio_array = audio_array.mean(axis=1)

        audio_array = np.int16(audio_array*32767)
        buffer = io.BytesIO()
        wavfile.write(buffer, 16000, audio_array)
        buffer.seek(0)
        buffer.name = f"chunk_{index}.wav"
        response = self.groq_client.audio.transcriptions.create(
            model=self.settings.AUDIO_TRANSCRIPT_MODEL,
            file=buffer,
            # timestamp_granularities=["word"]
        )
        print(response, "audio")

    def _split_audio(self, audio):
        duration = audio.duration
        chunks_info = []
        current_start = 0
        # created start and end time for splitting audio with overlap
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
