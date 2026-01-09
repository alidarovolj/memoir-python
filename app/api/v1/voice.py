"""Voice/Audio API endpoints"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.services.voice_service import VoiceService

router = APIRouter()


class VoiceProcessResponse(BaseModel):
    """Response for voice processing"""
    audio_url: str
    transcript: str | None


@router.post("/upload", response_model=VoiceProcessResponse)
async def upload_voice_note(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and transcribe voice note
    
    Accepts: audio files (m4a, mp3, wav, etc.)
    Returns: audio_url and Whisper transcript
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be audio format",
        )
    
    # Validate file size (max 25MB for Whisper)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if file_size > 25 * 1024 * 1024:  # 25MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file too large (max 25MB)",
        )
    
    try:
        service = VoiceService()
        result = await service.process_voice_note(
            file=file,
            user_id=str(current_user.id),
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice processing failed: {str(e)}",
        )
