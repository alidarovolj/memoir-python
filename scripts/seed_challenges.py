"""Seed script — creates sample global challenges in the database.

Usage (inside the backend container or venv):
    python -m scripts.seed_challenges
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


CHALLENGES = [
    {
        "title": "7-Day Memory Streak",
        "description": (
            "Build a habit of capturing your life every day. "
            "Create at least one memory each day for 7 consecutive days "
            "and earn your place on the leaderboard."
        ),
        "emoji": "🔥",
        "days_from_now": 0,
        "duration_days": 14,
        "goal": {
            "type": "daily_streak",
            "target": 7,
            "description": "Create at least 1 memory every day for 7 days in a row",
        },
    },
    {
        "title": "Memory Collector",
        "description": (
            "Capture 30 meaningful moments this month — big or small. "
            "Every photo, note, or voice recording counts toward your total."
        ),
        "emoji": "📸",
        "days_from_now": 0,
        "duration_days": 30,
        "goal": {
            "type": "create_memories",
            "target": 30,
            "description": "Create 30 memories during the challenge period",
        },
    },
    {
        "title": "Task Master",
        "description": (
            "Prove your productivity! Complete 20 tasks before time runs out. "
            "Habits, one-time tasks, and goals all count."
        ),
        "emoji": "✅",
        "days_from_now": 0,
        "duration_days": 21,
        "goal": {
            "type": "complete_tasks",
            "target": 20,
            "description": "Complete 20 tasks of any type",
        },
    },
    {
        "title": "Storyteller",
        "description": (
            "Share your world through stories. Post 5 stories and inspire "
            "your friends. Each story is a window into your day."
        ),
        "emoji": "✨",
        "days_from_now": 0,
        "duration_days": 14,
        "goal": {
            "type": "create_stories",
            "target": 5,
            "description": "Create 5 stories and share them with friends",
        },
    },
    {
        "title": "Monthly Sprint",
        "description": (
            "The ultimate productivity challenge. Complete 50 tasks in one month — "
            "only the most dedicated reach the top of the leaderboard."
        ),
        "emoji": "🚀",
        "days_from_now": 0,
        "duration_days": 31,
        "goal": {
            "type": "complete_tasks",
            "target": 50,
            "description": "Complete 50 tasks within the month",
        },
    },
]


async def seed() -> None:
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        for data in CHALLENGES:
            # Skip if a challenge with the same title already exists
            result = await db.execute(
                text("SELECT id FROM global_challenges WHERE title = :title"),
                {"title": data["title"]},
            )
            if result.fetchone():
                print(f"  ⚠  Skipping '{data['title']}' — already exists")
                continue

            start = now + timedelta(days=data["days_from_now"])
            end = start + timedelta(days=data["duration_days"])
            cid = str(uuid.uuid4())

            await db.execute(
                text("""
                    INSERT INTO global_challenges
                        (id, title, description, emoji, start_date, end_date,
                         goal, participants_count, is_active, created_at, updated_at)
                    VALUES
                        (:id, :title, :description, :emoji, :start_date, :end_date,
                         :goal, 0, true, :now, :now)
                """),
                {
                    "id": cid,
                    "title": data["title"],
                    "description": data["description"],
                    "emoji": data["emoji"],
                    "start_date": start,
                    "end_date": end,
                    "goal": json.dumps(data["goal"]),
                    "now": now,
                },
            )
            print(f"  ✓  Created '{data['title']}' ({data['emoji']})")

        await db.commit()

    print("\nDone! Challenges seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
