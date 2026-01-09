"""Seed initial achievements"""
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
import json


SEED_ACHIEVEMENTS = [
    # Memories
    {"code": "first_memory", "title": "Первое воспоминание", "description": "Создайте своё первое воспоминание", "emoji": "✨", "type": "MEMORIES", "criteria": 1, "xp": 10},
    {"code": "memories_10", "title": "Летописец", "description": "Создайте 10 воспоминаний", "emoji": "📝", "type": "MEMORIES", "criteria": 10, "xp": 50},
    {"code": "memories_50", "title": "Хранитель историй", "description": "Создайте 50 воспоминаний", "emoji": "📚", "type": "MEMORIES", "criteria": 50, "xp": 100},
    {"code": "memories_100", "title": "Мастер памяти", "description": "Создайте 100 воспоминаний", "emoji": "🏆", "type": "MEMORIES", "criteria": 100, "xp": 200},
    
    # Tasks
    {"code": "first_task", "title": "Первый шаг", "description": "Создайте первую задачу", "emoji": "✅", "type": "TASKS", "criteria": 1, "xp": 10},
    {"code": "tasks_20", "title": "Организатор", "description": "Завершите 20 задач", "emoji": "📋", "type": "TASKS", "criteria": 20, "xp": 50},
    {"code": "tasks_50", "title": "Продуктивность", "description": "Завершите 50 задач", "emoji": "⚡", "type": "TASKS", "criteria": 50, "xp": 100},
    
    # Streaks
    {"code": "streak_3", "title": "Три дня подряд", "description": "Ведите дневник 3 дня подряд", "emoji": "🔥", "type": "STREAKS", "criteria": 3, "xp": 30},
    {"code": "streak_7", "title": "Неделя силы", "description": "Ведите дневник 7 дней подряд", "emoji": "💪", "type": "STREAKS", "criteria": 7, "xp": 70},
    {"code": "streak_30", "title": "Месяц дисциплины", "description": "Ведите дневник 30 дней подряд", "emoji": "🌟", "type": "STREAKS", "criteria": 30, "xp": 200},
    
    # Social
    {"code": "first_challenge", "title": "Челленджер", "description": "Присоединитесь к первому челленджу", "emoji": "🎯", "type": "SOCIAL", "criteria": 1, "xp": 25},
    {"code": "challenge_complete", "title": "Победитель", "description": "Завершите челлендж", "emoji": "🏅", "type": "SOCIAL", "criteria": 1, "xp": 100},
    
    # Pet
    {"code": "pet_level_5", "title": "Опытный тренер", "description": "Прокачайте питомца до 5 уровня", "emoji": "🐣", "type": "PET", "criteria": 5, "xp": 50},
    {"code": "pet_level_10", "title": "Мастер питомцев", "description": "Прокачайте питомца до 10 уровня", "emoji": "🦋", "type": "PET", "criteria": 10, "xp": 150},
]


async def seed_achievements():
    """Seed achievements into database"""
    async with AsyncSessionLocal() as db:
        try:
            check_query = text("SELECT COUNT(*) FROM achievements")
            result = await db.execute(check_query)
            count = result.scalar()
            
            if count > 0:
                print(f"✅ Achievements already seeded ({count} found)")
                return
            
            print("🌱 Seeding achievements...")
            
            for ach in SEED_ACHIEVEMENTS:
                insert_query = text("""
                    INSERT INTO achievements 
                    (id, code, title, description, emoji, achievement_type, criteria_count, xp_reward, is_active, created_at)
                    VALUES 
                    (gen_random_uuid(), :code, :title, :description, :emoji, :type, :criteria, :xp, true, NOW())
                """)
                
                await db.execute(insert_query, {
                    "code": ach["code"],
                    "title": ach["title"],
                    "description": ach["description"],
                    "emoji": ach["emoji"],
                    "type": ach["type"],
                    "criteria": ach["criteria"],
                    "xp": ach["xp"],
                })
            
            await db.commit()
            print(f"✅ Successfully seeded {len(SEED_ACHIEVEMENTS)} achievements")
            
        except Exception as e:
            print(f"❌ Error seeding achievements: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_achievements())
