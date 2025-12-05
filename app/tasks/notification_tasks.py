"""Notification-related Celery tasks"""
import asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.services.notification_service import NotificationService

# Import models
from app.models.user import User
from app.models.task import Task, TaskStatus

# Sync engine for Celery tasks
sync_engine = create_engine(settings.DATABASE_URL_SYNC)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


def run_async(coro):
    """Helper to run async functions in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="check_task_reminders")
def check_task_reminders():
    """
    Check all tasks with upcoming due dates and send reminders
    
    This task should be scheduled to run every hour:
    - celery -A app.tasks.celery_app beat --loglevel=info
    
    Or configure in celerybeat-schedule.py:
    ```python
    app.conf.beat_schedule = {
        'check-task-reminders': {
            'task': 'check_task_reminders',
            'schedule': crontab(minute=0),  # Every hour
        },
    }
    ```
    """
    db = SyncSessionLocal()
    try:
        now = datetime.utcnow()
        
        # Get all users with reminders enabled and FCM token
        users = db.query(User).filter(
            and_(
                User.task_reminders_enabled == True,
                User.fcm_token.isnot(None),
            )
        ).all()
        
        reminders_sent = 0
        
        for user in users:
            # Calculate reminder time window
            reminder_time = now + timedelta(hours=user.reminder_hours_before)
            window_start = reminder_time - timedelta(minutes=30)  # 30 min before
            window_end = reminder_time + timedelta(minutes=30)    # 30 min after
            
            # Find tasks that need reminders
            tasks = db.query(Task).filter(
                and_(
                    Task.user_id == user.id,
                    Task.status == TaskStatus.pending,  # Only pending tasks
                    Task.due_date.isnot(None),
                    Task.due_date >= window_start,
                    Task.due_date <= window_end,
                )
            ).all()
            
            # Send reminders
            for task in tasks:
                try:
                    # Calculate hours until due
                    time_diff = task.due_date - now
                    hours_until_due = int(time_diff.total_seconds() / 3600)
                    
                    # Send notification
                    success = run_async(
                        NotificationService.send_task_reminder(
                            fcm_token=user.fcm_token,
                            task_title=task.title,
                            task_id=str(task.id),
                            hours_until_due=hours_until_due,
                        )
                    )
                    
                    if success:
                        reminders_sent += 1
                        print(f"✅ Sent reminder for task '{task.title}' to user {user.phone_number}")
                    else:
                        print(f"❌ Failed to send reminder for task '{task.title}'")
                        
                except Exception as e:
                    print(f"❌ Error sending reminder for task {task.id}: {e}")
                    continue
        
        print(f"📬 Reminders check complete: {reminders_sent} reminders sent to {len(users)} users")
        
        return {
            "success": True,
            "users_checked": len(users),
            "reminders_sent": reminders_sent,
        }
        
    except Exception as e:
        print(f"❌ Error in check_task_reminders: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()


@celery_app.task(name="send_daily_task_summary")
def send_daily_task_summary():
    """
    Send daily summary of tasks to all users
    
    Should be scheduled to run once per day (e.g., 8:00 AM):
    ```python
    app.conf.beat_schedule = {
        'send-daily-summary': {
            'task': 'send_daily_task_summary',
            'schedule': crontab(hour=8, minute=0),  # 8:00 AM daily
        },
    }
    ```
    """
    db = SyncSessionLocal()
    try:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        today_end = today_start + timedelta(days=1)
        
        # Get all users with reminders enabled and FCM token
        users = db.query(User).filter(
            and_(
                User.task_reminders_enabled == True,
                User.fcm_token.isnot(None),
            )
        ).all()
        
        summaries_sent = 0
        
        for user in users:
            try:
                # Count today's tasks
                today_tasks = db.query(Task).filter(
                    and_(
                        Task.user_id == user.id,
                        or_(
                            and_(
                                Task.due_date >= today_start,
                                Task.due_date < today_end,
                            ),
                            Task.due_date.is_(None),  # Include tasks without due date
                        ),
                        Task.status.in_([TaskStatus.pending, TaskStatus.inProgress]),
                    )
                ).all()
                
                # Count completed tasks
                completed_tasks = [t for t in today_tasks if t.status == TaskStatus.completed]
                
                tasks_count = len(today_tasks)
                completed_count = len(completed_tasks)
                
                if tasks_count == 0:
                    continue  # Skip users with no tasks
                
                # Send summary
                success = run_async(
                    NotificationService.send_daily_summary(
                        fcm_token=user.fcm_token,
                        tasks_count=tasks_count,
                        completed_count=completed_count,
                    )
                )
                
                if success:
                    summaries_sent += 1
                    print(f"✅ Sent daily summary to user {user.phone_number}")
                else:
                    print(f"❌ Failed to send summary to user {user.phone_number}")
                    
            except Exception as e:
                print(f"❌ Error sending summary to user {user.id}: {e}")
                continue
        
        print(f"📊 Daily summaries complete: {summaries_sent} summaries sent to {len(users)} users")
        
        return {
            "success": True,
            "users_checked": len(users),
            "summaries_sent": summaries_sent,
        }
        
    except Exception as e:
        print(f"❌ Error in send_daily_task_summary: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()


@celery_app.task(name="check_overdue_tasks")
def check_overdue_tasks():
    """
    Check for overdue tasks and send alerts
    
    Should be scheduled to run multiple times per day:
    ```python
    app.conf.beat_schedule = {
        'check-overdue-tasks': {
            'task': 'check_overdue_tasks',
            'schedule': crontab(hour='*/4'),  # Every 4 hours
        },
    }
    ```
    """
    db = SyncSessionLocal()
    try:
        now = datetime.utcnow()
        
        # Get all users with reminders enabled
        users = db.query(User).filter(
            and_(
                User.task_reminders_enabled == True,
                User.fcm_token.isnot(None),
            )
        ).all()
        
        alerts_sent = 0
        
        for user in users:
            # Find overdue tasks
            overdue_tasks = db.query(Task).filter(
                and_(
                    Task.user_id == user.id,
                    Task.status == TaskStatus.pending,
                    Task.due_date.isnot(None),
                    Task.due_date < now,
                )
            ).all()
            
            # Send alert for each overdue task
            for task in overdue_tasks:
                try:
                    success = run_async(
                        NotificationService.send_task_due_soon(
                            fcm_token=user.fcm_token,
                            task_title=task.title,
                            task_id=str(task.id),
                        )
                    )
                    
                    if success:
                        alerts_sent += 1
                        print(f"✅ Sent overdue alert for '{task.title}' to user {user.phone_number}")
                    
                except Exception as e:
                    print(f"❌ Error sending overdue alert for task {task.id}: {e}")
                    continue
        
        print(f"⏰ Overdue check complete: {alerts_sent} alerts sent")
        
        return {
            "success": True,
            "users_checked": len(users),
            "alerts_sent": alerts_sent,
        }
        
    except Exception as e:
        print(f"❌ Error in check_overdue_tasks: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()
