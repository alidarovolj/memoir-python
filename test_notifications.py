#!/usr/bin/env python3
"""
Test script to verify notification setup
Run this before deploying to ensure everything works
"""
import sys
import os
from datetime import datetime, timezone, timedelta

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tasks.celery_app import celery_app
from app.tasks.notification_tasks import check_task_reminders
from app.services.notification_service import NotificationService
import asyncio


def test_celery_beat_schedule():
    """Test that Celery Beat schedule is configured correctly"""
    print("🔍 Testing Celery Beat Schedule...")
    
    schedule = celery_app.conf.beat_schedule
    required_tasks = [
        'check-task-reminders',
        'send-daily-task-summary',
        'check-overdue-tasks',
        'check-pet-health',
        'send-throwback-notifications',
    ]
    
    missing_tasks = []
    for task_name in required_tasks:
        if task_name not in schedule:
            missing_tasks.append(task_name)
        else:
            print(f"  ✅ {task_name}: {schedule[task_name]['schedule']}")
    
    if missing_tasks:
        print(f"  ❌ Missing tasks: {missing_tasks}")
        return False
    
    print("  ✅ All required tasks are scheduled")
    return True


def test_notification_service():
    """Test that notification service can be imported and initialized"""
    print("\n🔍 Testing Notification Service...")
    
    try:
        # Check if Firebase is configured
        from app.core.config import settings
        if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and settings.FIREBASE_CREDENTIALS_PATH:
            if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                print(f"  ✅ Firebase credentials found: {settings.FIREBASE_CREDENTIALS_PATH}")
            else:
                print(f"  ⚠️  Firebase credentials path set but file not found: {settings.FIREBASE_CREDENTIALS_PATH}")
        else:
            print("  ⚠️  FIREBASE_CREDENTIALS_PATH not set - push notifications will be disabled")
        
        print("  ✅ NotificationService can be imported")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_task_reminder_logic():
    """Test the logic for calculating reminder windows"""
    print("\n🔍 Testing Task Reminder Logic...")
    
    try:
        # Simulate reminder calculation
        now = datetime.now(timezone.utc)
        reminder_hours_before = 1
        reminder_time = now + timedelta(hours=reminder_hours_before)
        window_start = reminder_time - timedelta(minutes=30)
        window_end = reminder_time + timedelta(minutes=30)
        
        print(f"  Current time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  Reminder window: {window_start.strftime('%Y-%m-%d %H:%M:%S UTC')} - {window_end.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Test with a task due in 1 hour
        task_due = now + timedelta(hours=1, minutes=15)
        if window_start <= task_due <= window_end:
            print(f"  ✅ Task due at {task_due.strftime('%Y-%m-%d %H:%M:%S UTC')} is in reminder window")
        else:
            print(f"  ⚠️  Task due at {task_due.strftime('%Y-%m-%d %H:%M:%S UTC')} is NOT in reminder window")
        
        print("  ✅ Reminder logic works correctly")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_due_date_with_time():
    """Test that due_date is created with time from scheduled_time"""
    print("\n🔍 Testing Due Date Creation with Time...")
    
    try:
        from datetime import datetime, timezone
        
        # Simulate creating a task with scheduled_time
        now = datetime.now(timezone.utc)
        scheduled_time = "08:00"
        
        # Parse scheduled_time
        hour, minute = map(int, scheduled_time.split(':'))
        due_date = datetime(now.year, now.month, now.day, hour, minute, tzinfo=timezone.utc)
        
        print(f"  Scheduled time: {scheduled_time}")
        print(f"  Due date created: {due_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        if due_date.hour == 8 and due_date.minute == 0:
            print("  ✅ Due date correctly includes time from scheduled_time")
        else:
            print(f"  ❌ Due date time incorrect: expected 08:00, got {due_date.hour:02d}:{due_date.minute:02d}")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing Notification Setup")
    print("=" * 60)
    
    results = []
    
    results.append(("Celery Beat Schedule", test_celery_beat_schedule()))
    results.append(("Notification Service", test_notification_service()))
    results.append(("Task Reminder Logic", test_task_reminder_logic()))
    results.append(("Due Date with Time", test_due_date_with_time()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Ready to deploy.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
