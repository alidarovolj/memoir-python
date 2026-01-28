"""File upload endpoints"""
from pathlib import Path
import uuid
import shutil
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload image file
    
    Accepts: image files (jpg, png, gif, webp, etc.)
    Returns: image_url path
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if not file.content_type or file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File must be an image format. Allowed types: {', '.join(allowed_types)}",
        )
    
    # Validate file size (max 10MB)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image file too large (max {max_size // 1024 // 1024}MB)",
        )
    
    try:
        # Create uploads/images directory if it doesn't exist
        upload_dir = Path("uploads/images")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix or ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return image URL path (relative to /uploads)
        image_url = f"/uploads/images/{unique_filename}"
        
        print(f"📸 [UPLOAD] Image uploaded: {image_url} (size: {file_size} bytes)")
        
        return {
            "success": True,
            "image_url": image_url,
            "message": "Image uploaded successfully",
        }
    
    except Exception as e:
        print(f"❌ [UPLOAD] Error uploading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}",
        )
