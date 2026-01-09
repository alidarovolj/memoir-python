"""Seed data for daily prompts"""
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.models.daily_prompt import PromptCategory, PromptType


# Sample prompts in Russian
SEED_PROMPTS = [
    # MORNING prompts
    {
        "prompt_text": "За что вы благодарны сегодня?",
        "prompt_icon": "🌅",
        "category": "MORNING",
        "prompt_type": "GRATITUDE",
        "order_index": 1,
    },
    {
        "prompt_text": "Какое намерение вы ставите на сегодняшний день?",
        "prompt_icon": "🎯",
        "category": "MORNING",
        "prompt_type": "GOAL",
        "order_index": 2,
    },
    {
        "prompt_text": "Что вас вдохновляет сегодня?",
        "prompt_icon": "✨",
        "category": "MORNING",
        "prompt_type": "EMOTION",
        "order_index": 3,
    },
    
    # DAYTIME prompts
    {
        "prompt_text": "Опишите лучший момент дня",
        "prompt_icon": "🌟",
        "category": "DAYTIME",
        "prompt_type": "REFLECTION",
        "order_index": 4,
    },
    {
        "prompt_text": "Что нового вы узнали сегодня?",
        "prompt_icon": "💡",
        "category": "DAYTIME",
        "prompt_type": "LEARNING",
        "order_index": 5,
    },
    {
        "prompt_text": "Кто вас вдохновил сегодня и почему?",
        "prompt_icon": "👥",
        "category": "DAYTIME",
        "prompt_type": "REFLECTION",
        "order_index": 6,
    },
    
    # EVENING prompts
    {
        "prompt_text": "Каким был ваш день одним словом?",
        "prompt_icon": "🌙",
        "category": "EVENING",
        "prompt_type": "REFLECTION",
        "order_index": 7,
    },
    {
        "prompt_text": "Что вы хотите улучшить завтра?",
        "prompt_icon": "🚀",
        "category": "EVENING",
        "prompt_type": "GOAL",
        "order_index": 8,
    },
    {
        "prompt_text": "За какое маленькое достижение сегодня вы себя хвалите?",
        "prompt_icon": "🏆",
        "category": "EVENING",
        "prompt_type": "GRATITUDE",
        "order_index": 9,
    },
    {
        "prompt_text": "Какую эмоцию вы чаще всего испытывали сегодня?",
        "prompt_icon": "💭",
        "category": "EVENING",
        "prompt_type": "EMOTION",
        "order_index": 10,
    },
    
    # WEEKLY prompts
    {
        "prompt_text": "Какую цель вы достигли на этой неделе?",
        "prompt_icon": "🎯",
        "category": "WEEKLY",
        "prompt_type": "GOAL",
        "order_index": 11,
    },
    {
        "prompt_text": "Что было самым запоминающимся на этой неделе?",
        "prompt_icon": "📸",
        "category": "WEEKLY",
        "prompt_type": "REFLECTION",
        "order_index": 12,
    },
    {
        "prompt_text": "Чему вы научились за последние 7 дней?",
        "prompt_icon": "📚",
        "category": "WEEKLY",
        "prompt_type": "LEARNING",
        "order_index": 13,
    },
    
    # CREATIVITY prompts (any time)
    {
        "prompt_text": "Если бы этот день был фильмом, как бы он назывался?",
        "prompt_icon": "🎬",
        "category": "DAYTIME",
        "prompt_type": "CREATIVITY",
        "order_index": 14,
    },
    {
        "prompt_text": "Напишите короткое стихотворение о вашем настроении",
        "prompt_icon": "✍️",
        "category": "EVENING",
        "prompt_type": "CREATIVITY",
        "order_index": 15,
    },
]


async def seed_daily_prompts():
    """Seed daily prompts into database"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if prompts already exist
            result = await db.execute(text("SELECT COUNT(*) FROM daily_prompts"))
            count = result.scalar()
            
            if count > 0:
                print(f"✅ Daily prompts already seeded ({count} prompts exist)")
                return
            
            # Insert prompts using raw SQL to avoid model loading issues
            for prompt_data in SEED_PROMPTS:
                await db.execute(
                    text("""
                        INSERT INTO daily_prompts 
                        (id, prompt_text, prompt_icon, category, prompt_type, is_active, order_index, created_at, updated_at)
                        VALUES (gen_random_uuid(), :prompt_text, :prompt_icon, :category, :prompt_type, true, :order_index, NOW(), NOW())
                    """),
                    prompt_data
                )
            
            await db.commit()
            print(f"✅ Successfully seeded {len(SEED_PROMPTS)} daily prompts!")
            
        except Exception as e:
            print(f"❌ Error seeding daily prompts: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(seed_daily_prompts())
