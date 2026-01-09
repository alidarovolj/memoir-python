"""User settings and notification endpoints"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import shutil
from pathlib import Path
import uuid

from app.db.session import get_db
from app.models.user import User
from app.models.memory import Memory
from app.models.task import Task
from app.models.story import Story
from app.api.deps import get_current_user
from app.services.notification_service import NotificationService

router = APIRouter()


# Schemas
class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    phone_number: Optional[str]
    username: Optional[str]
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    firebase_uid: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """User profile update request"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class FCMTokenRequest(BaseModel):
    """Request to save FCM token"""
    fcm_token: str


class NotificationSettings(BaseModel):
    """Notification settings"""
    task_reminders_enabled: bool
    reminder_hours_before: int


class NotificationSettingsResponse(BaseModel):
    """Notification settings response"""
    task_reminders_enabled: bool
    reminder_hours_before: int
    fcm_token: Optional[str]


class UserStatsResponse(BaseModel):
    """User statistics response"""
    memories_count: int
    tasks_total: int
    tasks_completed: int
    tasks_in_progress: int
    stories_count: int
    total_time_tracked: int


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get current user's profile information"""
    return UserProfileResponse(
        id=str(current_user.id),
        phone_number=current_user.phone_number,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        avatar_url=current_user.avatar_url,
        firebase_uid=current_user.firebase_uid,
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat(),
    )


@router.put("/me")
async def update_current_user_profile(
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile"""
    try:
        # Update text fields
        if first_name is not None:
            current_user.first_name = first_name
        if last_name is not None:
            current_user.last_name = last_name
        if email is not None:
            current_user.email = email
        
        # Handle avatar upload
        if avatar:
            # Create uploads directory if it doesn't exist
            upload_dir = Path("uploads/avatars")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            file_extension = Path(avatar.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename
            
            # Save file
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(avatar.file, buffer)
            
            # Update user's avatar_url
            current_user.avatar_url = f"/uploads/avatars/{unique_filename}"
        
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": UserProfileResponse(
                id=str(current_user.id),
                phone_number=current_user.phone_number,
                username=current_user.username,
                email=current_user.email,
                first_name=current_user.first_name,
                last_name=current_user.last_name,
                avatar_url=current_user.avatar_url,
                firebase_uid=current_user.firebase_uid,
                created_at=current_user.created_at.isoformat(),
                updated_at=current_user.updated_at.isoformat(),
            )
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's statistics
    
    Returns counts of memories, tasks, stories and total time tracked.
    """
    try:
        # Count memories
        memories_count_query = select(func.count(Memory.id)).where(
            Memory.user_id == current_user.id
        )
        memories_count = await db.scalar(memories_count_query) or 0
        
        # Count all tasks
        tasks_total_query = select(func.count(Task.id)).where(
            Task.user_id == current_user.id
        )
        tasks_total = await db.scalar(tasks_total_query) or 0
        
        # Count completed tasks
        tasks_completed_query = select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status == "completed"
        )
        tasks_completed = await db.scalar(tasks_completed_query) or 0
        
        # Count in-progress tasks
        tasks_in_progress_query = select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status == "in_progress"
        )
        tasks_in_progress = await db.scalar(tasks_in_progress_query) or 0
        
        # Count stories
        stories_count_query = select(func.count(Story.id)).where(
            Story.user_id == current_user.id
        )
        stories_count = await db.scalar(stories_count_query) or 0
        
        # Calculate total time tracked (sum of task durations in seconds)
        # For now, we'll use a simple estimation based on completed tasks
        # TODO: Implement actual time tracking when that feature is added
        total_time_tracked = tasks_completed * 1800  # Estimate 30 min per task
        
        return UserStatsResponse(
            memories_count=memories_count,
            tasks_total=tasks_total,
            tasks_completed=tasks_completed,
            tasks_in_progress=tasks_in_progress,
            stories_count=stories_count,
            total_time_tracked=total_time_tracked,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load user stats: {str(e)}"
        )


@router.post("/fcm-token")
async def save_fcm_token(
    request: FCMTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save user's Firebase Cloud Messaging token
    
    This token is used to send push notifications to the user's device.
    Should be called when user logs in or when FCM token is refreshed.
    """
    try:
        # Update user's FCM token
        current_user.fcm_token = request.fcm_token
        await db.commit()
        await db.refresh(current_user)
        
        # Send test notification to verify token
        await NotificationService.test_notification(request.fcm_token)
        
        return {
            "success": True,
            "message": "FCM token saved successfully",
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save FCM token: {str(e)}")


@router.delete("/fcm-token")
async def delete_fcm_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete user's FCM token (e.g. on logout)
    """
    try:
        current_user.fcm_token = None
        await db.commit()
        
        return {
            "success": True,
            "message": "FCM token deleted successfully",
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete FCM token: {str(e)}")


@router.get("/notification-settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
):
    """Get user's notification settings"""
    return NotificationSettingsResponse(
        task_reminders_enabled=current_user.task_reminders_enabled,
        reminder_hours_before=current_user.reminder_hours_before,
        fcm_token=current_user.fcm_token,
    )


@router.put("/notification-settings")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user's notification settings"""
    try:
        # Validate reminder_hours_before
        if settings.reminder_hours_before < 0 or settings.reminder_hours_before > 168:  # Max 1 week
            raise HTTPException(
                status_code=400,
                detail="reminder_hours_before must be between 0 and 168 hours (1 week)"
            )
        
        # Update settings
        current_user.task_reminders_enabled = settings.task_reminders_enabled
        current_user.reminder_hours_before = settings.reminder_hours_before
        
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "success": True,
            "message": "Notification settings updated successfully",
            "settings": {
                "task_reminders_enabled": current_user.task_reminders_enabled,
                "reminder_hours_before": current_user.reminder_hours_before,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update notification settings: {str(e)}"
        )


@router.post("/test-notification")
async def send_test_notification(
    current_user: User = Depends(get_current_user),
):
    """Send a test notification to verify that push notifications work"""
    if not current_user.fcm_token:
        raise HTTPException(
            status_code=400,
            detail="No FCM token found. Please save FCM token first."
        )
    
    success = await NotificationService.test_notification(current_user.fcm_token)
    
    if success:
        return {
            "success": True,
            "message": "Test notification sent successfully",
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send test notification"
        )
