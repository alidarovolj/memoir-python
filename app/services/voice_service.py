"""Voice/Audio service with Gemini transcription"""
import asyncio
import os
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import uuid

from google import genai
from google.genai import types
from app.core.config import settings


class VoiceService:
    """Service for handling voice notes and transcription using Gemini"""

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.upload_dir = Path("/app/uploads/audio")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_audio_file(
        self,
        file: UploadFile,
        user_id: str,
    ) -> str:
        file_ext = Path(file.filename).suffix if file.filename else ".m4a"
        filename = f"{user_id}_{uuid.uuid4()}{file_ext}"
        filepath = self.upload_dir / filename

        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        return f"/uploads/audio/{filename}"

    async def transcribe_audio(
        self,
        audio_path: str,
    ) -> Optional[str]:
        """Transcribe audio using Gemini multimodal capabilities."""
        try:
            loop = asyncio.get_event_loop()

            ext = Path(audio_path).suffix.lower()
            mime_map = {
                ".mp3": "audio/mpeg",
                ".m4a": "audio/mp4",
                ".wav": "audio/wav",
                ".ogg": "audio/ogg",
                ".flac": "audio/flac",
                ".aac": "audio/aac",
                ".webm": "audio/webm",
            }
            mime_type = mime_map.get(ext, "audio/mpeg")

            uploaded_file = await loop.run_in_executor(
                None,
                lambda: self.client.files.upload(
                    file=audio_path,
                    config=types.UploadFileConfig(mime_type=mime_type),
                ),
            )

            response = await self.client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    types.Part(
                        file_data=types.FileData(
                            file_uri=uploaded_file.uri,
                            mime_type=mime_type,
                        )
                    ),
                    "Transcribe this audio recording in Russian. "
                    "Return only the transcribed text without any additional commentary.",
                ],
            )

            await loop.run_in_executor(
                None,
                lambda: self.client.files.delete(name=uploaded_file.name),
            )

            return response.text.strip()

        except Exception as e:
            print(f"❌ Gemini transcription failed: {e}")
            return None

    async def process_voice_note(
        self,
        file: UploadFile,
        user_id: str,
    ) -> dict:
        audio_url = await self.save_audio_file(file, user_id)
        full_path = f"/app{audio_url}"
        transcript = await self.transcribe_audio(full_path)

        return {
            "audio_url": audio_url,
            "transcript": transcript,
        }
