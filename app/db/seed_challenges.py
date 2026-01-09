"""Seed initial challenges"""
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


SEED_CHALLENGES = [
    {
        "title": "🌟 Месяц благодарности",
        "description": "Запишите 30 вещей, за которые вы благодарны. Практика благодарности улучшает настроение и помогает замечать хорошее в жизни.",
        "emoji": "🌟",
        "start_date": datetime.now(timezone.utc),
        "end_date": datetime.now(timezone.utc) + timedelta(days=30),
        "goal": {
            "type": "create_memories",
            "target": 30,
            "description": "Создать 30 воспоминаний о благодарности"
        }
    },
    {
        "title": "📝 30 дней ведения дневника",
        "description": "Создавайте хотя бы одно воспоминание каждый день в течение месяца. Формируйте привычку рефлексии и самопознания.",
        "emoji": "📝",
        "start_date": datetime.now(timezone.utc),
        "end_date": datetime.now(timezone.utc) + timedelta(days=30),
        "goal": {
            "type": "daily_streak",
            "target": 30,
            "description": "30-дневная серия записей"
        }
    },
    {
        "title": "🎯 Неделя продуктивности",
        "description": "Завершите 20 задач за неделю. Время для активных действий и достижений!",
        "emoji": "🎯",
        "start_date": datetime.now(timezone.utc),
        "end_date": datetime.now(timezone.utc) + timedelta(days=7),
        "goal": {
            "type": "complete_tasks",
            "target": 20,
            "description": "Завершить 20 задач"
        }
    },
    {
        "title": "🌱 Новогодние размышления",
        "description": "Подведите итоги года: запишите 10 самых ярких воспоминаний 2025 года. Отпразднуйте свой рост и достижения.",
        "emoji": "🌱",
        "start_date": datetime.now(timezone.utc),
        "end_date": datetime(2026, 1, 10, tzinfo=timezone.utc),
        "goal": {
            "type": "create_memories",
            "target": 10,
            "description": "Записать 10 ярких воспоминаний года"
        }
    },
    {
        "title": "💪 Челлендж личного роста",
        "description": "Фокус на саморазвитии: создайте 15 воспоминаний о том, чему вы научились или как выросли как личность.",
        "emoji": "💪",
        "start_date": datetime.now(timezone.utc),
        "end_date": datetime.now(timezone.utc) + timedelta(days=21),
        "goal": {
            "type": "create_memories",
            "target": 15,
            "description": "15 воспоминаний о личном росте"
        }
    },
]


async def seed_challenges():
    """Seed initial challenges into the database"""
    from sqlalchemy import bindparam
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if challenges already exist
            check_query = text("SELECT COUNT(*) FROM global_challenges")
            result = await db.execute(check_query)
            count = result.scalar()
            
            if count > 0:
                print(f"✅ Challenges already seeded ({count} found)")
                return
            
            print("🌱 Seeding challenges...")
            
            import json
            
            # Use direct SQL with proper parameter binding
            for challenge_data in SEED_CHALLENGES:
                insert_query = text("""
                    INSERT INTO global_challenges 
                    (id, title, description, emoji, start_date, end_date, goal, participants_count, is_active, created_at, updated_at)
                    VALUES 
                    (gen_random_uuid(), :title, :description, :emoji, :start_date, :end_date, CAST(:goal AS jsonb), 0, true, NOW(), NOW())
                """)
                
                await db.execute(insert_query, {
                    "title": challenge_data["title"],
                    "description": challenge_data["description"],
                    "emoji": challenge_data["emoji"],
                    "start_date": challenge_data["start_date"],
                    "end_date": challenge_data["end_date"],
                    "goal": json.dumps(challenge_data["goal"]),
                })
            
            await db.commit()
            print(f"✅ Successfully seeded {len(SEED_CHALLENGES)} challenges")
            
        except Exception as e:
            print(f"❌ Error seeding challenges: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_challenges())
