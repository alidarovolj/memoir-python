"""Notification Service for Firebase Cloud Messaging"""
import logging
from typing import Optional
from firebase_admin import messaging, initialize_app, credentials
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
# Note: You need to set FIREBASE_CREDENTIALS_PATH in .env
try:
    if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and settings.FIREBASE_CREDENTIALS_PATH:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized")
    else:
        logger.warning("⚠️ FIREBASE_CREDENTIALS_PATH not set, push notifications disabled")
except Exception as e:
    logger.error(f"❌ Failed to initialize Firebase: {e}")


class NotificationService:
    """Service for sending push notifications via FCM"""
    
    @staticmethod
    async def send_task_reminder(
        fcm_token: str,
        task_title: str,
        task_id: str,
        hours_until_due: int
    ) -> bool:
        """
        Send a task reminder notification
        
        Args:
            fcm_token: User's Firebase Cloud Messaging token
            task_title: Title of the task
            task_id: ID of the task
            hours_until_due: Hours until task is due
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            if hours_until_due <= 1:
                time_text = "менее чем через час"
            elif hours_until_due < 24:
                time_text = f"через {hours_until_due} ч"
            else:
                days = hours_until_due // 24
                time_text = f"через {days} д"
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"⏰ Напоминание о задаче",
                    body=f"{task_title} - {time_text}",
                ),
                data={
                    'type': 'task_reminder',
                    'task_id': task_id,
                    'task_title': task_title,
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='notification_icon',
                        color='#6366F1',  # Primary color
                        sound='default',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Task reminder sent: {task_title} → {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send task reminder: {e}")
            return False
    
    @staticmethod
    async def send_task_due_soon(
        fcm_token: str,
        task_title: str,
        task_id: str
    ) -> bool:
        """
        Send notification that task is due soon
        
        Args:
            fcm_token: User's Firebase Cloud Messaging token
            task_title: Title of the task
            task_id: ID of the task
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"🔥 Задача скоро истекает!",
                    body=f"{task_title}",
                ),
                data={
                    'type': 'task_due_soon',
                    'task_id': task_id,
                    'task_title': task_title,
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='notification_icon',
                        color='#EF4444',  # Red color for urgency
                        sound='default',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Task due soon notification sent: {task_title} → {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send task due soon notification: {e}")
            return False
    
    @staticmethod
    async def send_daily_summary(
        fcm_token: str,
        tasks_count: int,
        completed_count: int
    ) -> bool:
        """
        Send daily tasks summary notification
        
        Args:
            fcm_token: User's Firebase Cloud Messaging token
            tasks_count: Total tasks for today
            completed_count: Completed tasks count
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            remaining = tasks_count - completed_count
            
            if remaining == 0:
                title = "🎉 Все задачи выполнены!"
                body = f"Отлично! Вы завершили все {tasks_count} задачи на сегодня."
            else:
                title = f"📋 У вас {remaining} задач на сегодня"
                body = f"Выполнено: {completed_count}/{tasks_count}. Продолжайте в том же духе!"
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    'type': 'daily_summary',
                    'tasks_count': str(tasks_count),
                    'completed_count': str(completed_count),
                },
                token=fcm_token,
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Daily summary sent → {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send daily summary: {e}")
            return False
    
    @staticmethod
    async def test_notification(fcm_token: str) -> bool:
        """
        Send test notification to verify FCM token
        
        Args:
            fcm_token: User's Firebase Cloud Messaging token
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="✅ Уведомления работают!",
                    body="Memoir готов отправлять вам напоминания о задачах.",
                ),
                data={
                    'type': 'test',
                },
                token=fcm_token,
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Test notification sent → {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send test notification: {e}")
            return False
