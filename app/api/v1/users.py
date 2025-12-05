"""User settings and notification endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.notification_service import NotificationService

router = APIRouter()


# Schemas
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
