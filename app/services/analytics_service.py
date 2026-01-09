"""Analytics service for calculating real statistics"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.memory import Memory
from app.models.task import Task, TaskStatus


class AnalyticsService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete analytics dashboard data"""
        now = datetime.now()
        
        # Calculate all metrics in parallel
        total_memories = await self._get_total_memories()
        total_tasks_completed = await self._get_total_tasks_completed()
        total_time_tracked = await self._get_total_time_tracked()
        
        this_week_stats = await self._get_this_week_stats(now)
        streaks = await self._get_streaks(now)
        current_month_data = await self._get_current_month_data(now)
        productivity_trends = await self._get_productivity_trends(now)
        
        return {
            "total_memories": total_memories,
            "total_tasks_completed": total_tasks_completed,
            "total_time_tracked": total_time_tracked,
            "total_stories": 0,  # TODO: implement stories
            "this_week_memories": this_week_stats["memories"],
            "this_week_tasks": this_week_stats["tasks"],
            "this_week_time": this_week_stats["time"],
            "current_streak": streaks["current"],
            "longest_streak": streaks["longest"],
            "current_month": current_month_data,
            "productivity_trends": productivity_trends,
            "category_stats": []  # TODO: implement category stats
        }

    async def _get_total_memories(self) -> int:
        """Get total number of memories"""
        result = await self.db.execute(
            select(func.count(Memory.id)).where(Memory.user_id == self.user_id)
        )
        return result.scalar() or 0

    async def _get_total_tasks_completed(self) -> int:
        """Get total number of completed tasks"""
        result = await self.db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.user_id == self.user_id,
                    Task.status == TaskStatus.completed
                )
            )
        )
        return result.scalar() or 0

    async def _get_total_time_tracked(self) -> int:
        """Get total time tracked in minutes"""
        # TODO: Implement time tracking model
        return 0

    async def _get_this_week_stats(self, now: datetime) -> Dict[str, int]:
        """Get statistics for the current week"""
        # Start of week (Monday)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        # Memories this week
        memories_result = await self.db.execute(
            select(func.count(Memory.id)).where(
                and_(
                    Memory.user_id == self.user_id,
                    Memory.created_at >= start_of_week
                )
            )
        )
        memories_count = memories_result.scalar() or 0

        # Tasks completed this week
        tasks_result = await self.db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.user_id == self.user_id,
                    Task.status == TaskStatus.completed,
                    Task.completed_at >= start_of_week
                )
            )
        )
        tasks_count = tasks_result.scalar() or 0

        # Time tracked this week
        # TODO: Implement time tracking model
        time_count = 0

        return {
            "memories": memories_count,
            "tasks": tasks_count,
            "time": time_count
        }

    async def _get_streaks(self, now: datetime) -> Dict[str, int]:
        """Calculate current and longest streaks"""
        # Get all days with activity (memories or completed tasks)
        # Start from 90 days ago for longest streak calculation
        start_date = now - timedelta(days=90)
        
        # Get dates with memories
        memory_dates_result = await self.db.execute(
            select(func.date(Memory.created_at).label('activity_date')).where(
                and_(
                    Memory.user_id == self.user_id,
                    Memory.created_at >= start_date
                )
            ).distinct()
        )
        memory_dates = {row.activity_date for row in memory_dates_result}

        # Get dates with completed tasks
        task_dates_result = await self.db.execute(
            select(func.date(Task.completed_at).label('activity_date')).where(
                and_(
                    Task.user_id == self.user_id,
                    Task.status == TaskStatus.completed,
                    Task.completed_at >= start_date
                )
            ).distinct()
        )
        task_dates = {row.activity_date for row in task_dates_result}

        # Combine all activity dates
        all_activity_dates = sorted(memory_dates | task_dates)

        if not all_activity_dates:
            return {"current": 0, "longest": 0}

        # Calculate current streak
        current_streak = 0
        check_date = now.date()
        
        while check_date in all_activity_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        # Calculate longest streak
        longest_streak = 0
        temp_streak = 0
        prev_date = None

        for activity_date in all_activity_dates:
            if prev_date is None:
                temp_streak = 1
            elif (activity_date - prev_date).days == 1:
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
            
            prev_date = activity_date

        longest_streak = max(longest_streak, temp_streak)

        return {
            "current": current_streak,
            "longest": longest_streak
        }

    async def _get_current_month_data(self, now: datetime) -> Dict[str, Any]:
        """Get current month statistics"""
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Total memories this month
        memories_result = await self.db.execute(
            select(func.count(Memory.id)).where(
                and_(
                    Memory.user_id == self.user_id,
                    Memory.created_at >= start_of_month
                )
            )
        )
        memories_count = memories_result.scalar() or 0

        # Total tasks completed this month
        tasks_result = await self.db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.user_id == self.user_id,
                    Task.status == TaskStatus.completed,
                    Task.completed_at >= start_of_month
                )
            )
        )
        tasks_count = tasks_result.scalar() or 0

        # Total time tracked this month
        # TODO: Implement time tracking model
        time_count = 0

        # Daily activities for heatmap
        daily_activities = await self._get_daily_activities(start_of_month, now)

        return {
            "month": now.month,
            "year": now.year,
            "total_memories": memories_count,
            "total_tasks_completed": tasks_count,
            "total_time_tracked": time_count,
            "total_stories": 0,
            "daily_activities": daily_activities
        }

    async def _get_daily_activities(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get daily activity counts for heatmap"""
        # Get daily memory counts
        memory_result = await self.db.execute(
            select(
                func.date(Memory.created_at).label('date'),
                func.count(Memory.id).label('count')
            ).where(
                and_(
                    Memory.user_id == self.user_id,
                    Memory.created_at >= start_date,
                    Memory.created_at <= end_date
                )
            ).group_by(func.date(Memory.created_at))
        )
        memory_by_date = {row.date: row.count for row in memory_result}

        # Get daily task completion counts
        task_result = await self.db.execute(
            select(
                func.date(Task.completed_at).label('date'),
                func.count(Task.id).label('count')
            ).where(
                and_(
                    Task.user_id == self.user_id,
                    Task.status == TaskStatus.completed,
                    Task.completed_at >= start_date,
                    Task.completed_at <= end_date
                )
            ).group_by(func.date(Task.completed_at))
        )
        task_by_date = {row.date: row.count for row in task_result}

        # Get daily time tracked
        # TODO: Implement time tracking model
        time_by_date = {}

        # Combine into daily activities
        daily_activities = []
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            memories = memory_by_date.get(current_date, 0)
            tasks = task_by_date.get(current_date, 0)
            time_tracked = time_by_date.get(current_date, 0)
            total = memories + tasks

            if total > 0:
                daily_activities.append({
                    "date": current_date.isoformat(),
                    "memories_count": memories,
                    "tasks_completed": tasks,
                    "time_tracked": time_tracked,
                    "stories_created": 0
                })

            current_date += timedelta(days=1)

        return daily_activities

    async def _get_productivity_trends(self, now: datetime) -> List[Dict[str, Any]]:
        """Get productivity trends for the last 6 months"""
        trends = []
        
        # Month names in Russian
        month_names = [
            "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
            "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"
        ]
        
        for i in range(5, -1, -1):
            # Calculate month boundaries
            target_date = now - timedelta(days=30 * i)
            start_of_month = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Calculate end of month
            if start_of_month.month == 12:
                end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
            else:
                end_of_month = start_of_month.replace(month=start_of_month.month + 1)

            # Get tasks completed in this month
            tasks_result = await self.db.execute(
                select(func.count(Task.id)).where(
                    and_(
                        Task.user_id == self.user_id,
                        Task.status == TaskStatus.completed,
                        Task.completed_at >= start_of_month,
                        Task.completed_at < end_of_month
                    )
                )
            )
            tasks_count = tasks_result.scalar() or 0

            # Get memories created in this month
            memories_result = await self.db.execute(
                select(func.count(Memory.id)).where(
                    and_(
                        Memory.user_id == self.user_id,
                        Memory.created_at >= start_of_month,
                        Memory.created_at < end_of_month
                    )
                )
            )
            memories_count = memories_result.scalar() or 0

            # Get time tracked in this month
            # TODO: Implement time tracking model
            time_tracked = 0

            # Format period as "Month Year"
            period = f"{month_names[start_of_month.month - 1]} {start_of_month.year}"

            trends.append({
                "period": period,
                "tasks_completed": tasks_count,
                "time_tracked": time_tracked,
                "memories_created": memories_count
            })

        return trends
