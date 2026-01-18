"""Notification-related Celery tasks"""
import asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.services.notification_service import NotificationService

# Import models - все модели нужны для правильной инициализации relationships
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.pet import Pet
from app.models.time_capsule import TimeCapsule
# Импортируем все модели, которые используются в relationships User
try:
    from app.models.challenge import ChallengeParticipant
except ImportError:
    pass  # Модель может не существовать
try:
    from app.models.achievement import UserAchievement
except ImportError:
    pass  # Модель может не существовать

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
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
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
            # Only send if task hasn't been updated in the last 55 minutes
            # This prevents duplicate notifications if the task stays in the window for an hour
            min_update_time = now - timedelta(minutes=55)
            tasks = db.query(Task).filter(
                and_(
                    Task.user_id == user.id,
                    Task.status == TaskStatus.pending,  # Only pending tasks
                    Task.due_date.isnot(None),
                    Task.due_date >= window_start,
                    Task.due_date <= window_end,
                    # Only send if task wasn't updated in the last 55 minutes
                    # This ensures we send reminder once per hour max
                    Task.updated_at < min_update_time,
                )
            ).all()
            
            # Send reminders
            for task in tasks:
                try:
                    # Ensure due_date is timezone-aware
                    task_due = task.due_date
                    if task_due.tzinfo is None:
                        # If timezone-naive, assume UTC
                        task_due = task_due.replace(tzinfo=timezone.utc)
                    
                    # Calculate hours until due
                    time_diff = task_due - now
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
                        # Update task to mark that reminder was sent (prevent duplicates)
                        task.updated_at = now
                        db.commit()
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
            # Only send alert if task hasn't been updated in the last 23 hours
            # This prevents sending duplicate alerts every 4 hours
            min_update_time = now - timedelta(hours=23)
            overdue_tasks = db.query(Task).filter(
                and_(
                    Task.user_id == user.id,
                    Task.status == TaskStatus.pending,
                    Task.due_date.isnot(None),
                    Task.due_date < now,
                    # Only send if task was last updated more than 23 hours ago
                    # This ensures we send alert once per day max
                    Task.updated_at < min_update_time,
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
                        # Update task to mark that alert was sent (prevent duplicates)
                        task.updated_at = now
                        db.commit()
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


@celery_app.task(name="check_pet_health")
def check_pet_health():
    """
    Check all pets' health and send notifications if they need attention
    
    Should be scheduled to run twice per day:
    ```python
    app.conf.beat_schedule = {
        'check-pet-health': {
            'task': 'check_pet_health',
            'schedule': crontab(hour='9,21', minute=0),  # 9:00 AM and 9:00 PM
        },
    }
    ```
    """
    db = SyncSessionLocal()
    try:
        now = datetime.utcnow()
        
        # Get all users with pets and FCM tokens
        users_with_pets = db.query(User).join(Pet).filter(
            User.fcm_token.isnot(None)
        ).all()
        
        notifications_sent = 0
        
        for user in users_with_pets:
            try:
                pet = user.pet
                if not pet:
                    continue
                
                # Calculate hours since last activities
                hours_since_fed = (now - pet.last_fed).total_seconds() / 3600
                hours_since_played = (now - pet.last_played).total_seconds() / 3600
                
                # Update pet stats if needed
                if hours_since_fed > 24 or hours_since_played > 24:
                    max_hours = max(hours_since_fed, hours_since_played)
                    pet.decay_stats(int(max_hours))
                    db.commit()
                
                # Send notification if pet needs attention
                # Criteria: no activity for 48+ hours OR happiness/health < 30
                needs_notification = (
                    (hours_since_fed > 48 and hours_since_played > 48) or
                    pet.happiness < 30 or
                    pet.health < 30
                )
                
                if needs_notification:
                    # Determine notification type
                    if hours_since_fed > 48:
                        message = f"{pet.name} скучает! Покормите питомца, создав воспоминание 🍔"
                    elif hours_since_played > 48:
                        message = f"{pet.name} хочет играть! Выполните задачу 🎾"
                    elif pet.happiness < 30:
                        happiness_emoji = "😢" if pet.happiness < 20 else "😞"
                        message = f"{pet.name} грустит {happiness_emoji}. Создайте воспоминание!"
                    elif pet.health < 30:
                        health_emoji = "💔" if pet.health < 20 else "❤️"
                        message = f"{pet.name} чувствует себя плохо {health_emoji}. Выполните задачу!"
                    else:
                        message = f"{pet.name} нуждается в вашем внимании!"
                    
                    # Send notification
                    # TODO: Add send_pet_reminder method to NotificationService
                    print(f"🐾 Would send: {message} to user {user.phone_number}")
                    notifications_sent += 1
                        
            except Exception as e:
                print(f"❌ Error checking pet for user {user.id}: {e}")
                continue
        
        print(f"🐾 Pet health check complete: {notifications_sent} reminders sent to {len(users_with_pets)} users")
        
        return {
            "success": True,
            "users_checked": len(users_with_pets),
            "notifications_sent": notifications_sent,
        }
        
    except Exception as e:
        print(f"❌ Error in check_pet_health: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()


@celery_app.task(name="send_throwback_notifications")
def send_throwback_notifications():
    """
    Send "On this day X years ago" notifications to users
    
    This task should be scheduled to run every morning at 9:00 AM:
    ```python
    app.conf.beat_schedule = {
        'send-throwback-notifications': {
            'task': 'send_throwback_notifications',
            'schedule': crontab(hour=9, minute=0),  # Every day at 9:00 AM
        },
    }
    ```
    """
    db = SyncSessionLocal()
    try:
        from app.models.memory import Memory
        from sqlalchemy import extract
        
        now = datetime.utcnow()
        
        # Get all users with FCM tokens
        users = db.query(User).filter(
            User.fcm_token.isnot(None)
        ).all()
        
        notifications_sent = 0
        
        for user in users:
            # Check for memories from 1, 2, 3, 5, or 10 years ago (same day and month)
            years_to_check = [1, 2, 3, 5, 10]
            
            for years_ago in years_to_check:
                target_year = now.year - years_ago
                
                # Find memory from this exact day N years ago
                memory = db.query(Memory).filter(
                    and_(
                        Memory.user_id == user.id,
                        extract('month', Memory.created_at) == now.month,
                        extract('day', Memory.created_at) == now.day,
                        extract('year', Memory.created_at) == target_year,
                    )
                ).order_by(Memory.created_at.desc()).first()
                
                if memory:
                    # Found a memory! Send notification
                    title = f"🕰️ {years_ago} {_get_years_text(years_ago)} назад"
                    
                    # Truncate memory content to 100 chars
                    preview = memory.content[:100]
                    if len(memory.content) > 100:
                        preview += "..."
                    
                    body = preview
                    
                    try:
                        # Send notification
                        run_async(
                            NotificationService().send_notification(
                                token=user.fcm_token,
                                title=title,
                                body=body,
                                data={
                                    "type": "throwback",
                                    "memory_id": str(memory.id),
                                    "years_ago": str(years_ago),
                                },
                            )
                        )
                        notifications_sent += 1
                        print(f"✅ Sent throwback notification to user {user.id} ({years_ago} years ago)")
                        
                        # Only send one notification per user (first match)
                        break
                        
                    except Exception as e:
                        print(f"❌ Failed to send throwback notification to user {user.id}: {e}")
                        continue
        
        print(f"🕰️ Throwback notifications complete: {notifications_sent} sent to {len(users)} users checked")
        
        return {
            "success": True,
            "users_checked": len(users),
            "notifications_sent": notifications_sent,
        }
        
    except Exception as e:
        print(f"❌ Error in send_throwback_notifications: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()


def _get_years_text(years: int) -> str:
    """Get Russian text for years (год/года/лет)"""
    if years == 1:
        return "год"
    elif years in [2, 3, 4]:
        return "года"
    else:
        return "лет"
