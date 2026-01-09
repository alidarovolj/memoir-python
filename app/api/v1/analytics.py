"""Analytics API endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard")
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics dashboard data with real statistics"""
    analytics_service = AnalyticsService(db=db, user_id=current_user.id)
    dashboard_data = await analytics_service.get_dashboard_data()
    return dashboard_data
