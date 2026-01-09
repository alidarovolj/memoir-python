"""Voice/Audio service with Whisper transcription"""
import os
import openai
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import uuid

from app.core.config import settings


class VoiceService:
    """Service for handling voice notes and transcription"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.upload_dir = Path("/app/uploads/audio")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_audio_file(
        self,
        file: UploadFile,
        user_id: str,
    ) -> str:
        """
        Save uploaded audio file
        Returns: relative path to saved file
        """
        # Generate unique filename
        file_ext = Path(file.filename).suffix if file.filename else ".m4a"
        filename = f"{user_id}_{uuid.uuid4()}{file_ext}"
        filepath = self.upload_dir / filename
        
        # Save file
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        # Return relative path
        return f"/uploads/audio/{filename}"
    
    async def transcribe_audio(
        self,
        audio_path: str,
    ) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper
        
        Args:
            audio_path: Full path to audio file
        
        Returns:
            Transcribed text or None if failed
        """
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru",  # Russian language
                )
            
            return transcript.text
        
        except Exception as e:
            print(f"❌ Whisper transcription failed: {e}")
            return None
    
    async def process_voice_note(
        self,
        file: UploadFile,
        user_id: str,
    ) -> dict:
        """
        Process voice note: save + transcribe
        
        Returns:
            {
                "audio_url": str,
                "transcript": str or None,
            }
        """
        # Save audio
        audio_url = await self.save_audio_file(file, user_id)
        
        # Get full path for transcription
        full_path = f"/app{audio_url}"
        
        # Transcribe
        transcript = await self.transcribe_audio(full_path)
        
        return {
            "audio_url": audio_url,
            "transcript": transcript,
        }
