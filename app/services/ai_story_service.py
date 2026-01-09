"""AI Story Generation Service using OpenAI"""
from typing import Optional, List
import openai
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.config import settings
from app.models.memory import Memory
from app.models.user import User


class AIStoryService:
    """Service for AI-powered story generation and creative features"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o-mini"  # Fast and cost-effective
    
    @staticmethod
    async def _get_user_memories(
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
        category: Optional[str] = None,
        days_ago: Optional[int] = None,
    ) -> List[Memory]:
        """Get user's memories for context"""
        query = select(Memory).where(Memory.user_id == user_id)
        
        if category:
            query = query.where(Memory.category_id == category)
        
        if days_ago:
            cutoff_date = datetime.now() - timedelta(days=days_ago)
            query = query.where(Memory.created_at >= cutoff_date)
        
        query = query.order_by(Memory.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def generate_story(
        self,
        db: AsyncSession,
        user_id: str,
        story_type: str,
        memory_id: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> dict:
        """
        Generate creative story from user's memories
        
        Args:
            story_type: poem, letter, story, haiku
            memory_id: specific memory to transform (optional)
            custom_prompt: additional instructions (optional)
        """
        # Get memory content
        if memory_id:
            memory_query = select(Memory).where(
                and_(Memory.id == memory_id, Memory.user_id == user_id)
            )
            memory_result = await db.execute(memory_query)
            memory = memory_result.scalar_one_or_none()
            
            if not memory:
                raise ValueError("Memory not found")
            
            content = f"Название: {memory.title}\nСодержание: {memory.content}"
        else:
            # Use recent memories
            memories = await self._get_user_memories(db, user_id, limit=10)
            if not memories:
                raise ValueError("No memories found")
            
            content = "\n\n".join([
                f"- {m.title}: {m.content[:100]}..."
                for m in memories
            ])
        
        # Build prompt based on story type
        prompts = {
            "poem": "Напиши красивое лирическое стихотворение на основе этого воспоминания. Используй метафоры и образы.",
            "haiku": "Напиши хайку (3 строки: 5-7-5 слогов) на основе этого воспоминания. Передай суть момента.",
            "story": "Напиши короткий рассказ (200-300 слов) на основе этого воспоминания. Добавь детали и эмоции.",
            "letter": "Напиши письмо будущему себе на основе этого воспоминания. Поделись мыслями и надеждами.",
            "gratitude": "Напиши текст благодарности на основе этого воспоминания. Что особенного в этом моменте?",
        }
        
        system_prompt = prompts.get(story_type, prompts["story"])
        
        if custom_prompt:
            system_prompt += f"\n\nДополнительные инструкции: {custom_prompt}"
        
        # Call OpenAI
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                temperature=0.8,
                max_tokens=500,
            )
            
            generated_text = response.choices[0].message.content
            
            return {
                "story_type": story_type,
                "generated_text": generated_text,
                "source_memory_id": memory_id,
                "tokens_used": response.usage.total_tokens,
            }
        
        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")
    
    async def chat_with_past(
        self,
        db: AsyncSession,
        user_id: str,
        user_message: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> dict:
        """
        Chat with past self based on memories
        AI acts as past version of user
        """
        # Get memories for context
        memories = await self._get_user_memories(db, user_id, limit=30, days_ago=365)
        
        if not memories:
            raise ValueError("No memories found for context")
        
        # Build context from memories
        context = "Контекст воспоминаний пользователя:\n"
        context += "\n".join([
            f"- {m.created_at.strftime('%Y-%m-%d')}: {m.title} - {m.content[:150]}"
            for m in memories[:15]
        ])
        
        system_prompt = f"""Ты - прошлая версия пользователя, основанная на его воспоминаниях.
Отвечай от первого лица, как будто ты сам пользователь из прошлого.
Используй информацию из воспоминаний, но добавляй эмоции и рефлексию.
Будь искренним, вдумчивым и поддерживающим.

{context}"""
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Last 3 exchanges
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.9,
                max_tokens=300,
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "response": ai_response,
                "tokens_used": response.usage.total_tokens,
            }
        
        except Exception as e:
            raise Exception(f"Chat failed: {str(e)}")
    
    async def generate_year_summary(
        self,
        db: AsyncSession,
        user_id: str,
        year: int = None,
    ) -> dict:
        """
        Generate year in review summary
        """
        if not year:
            year = datetime.now().year
        
        # Get memories from the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        query = select(Memory).where(
            and_(
                Memory.user_id == user_id,
                Memory.created_at >= start_date,
                Memory.created_at <= end_date,
            )
        ).order_by(Memory.created_at.desc())
        
        result = await db.execute(query)
        memories = result.scalars().all()
        
        if not memories:
            raise ValueError(f"No memories found for {year}")
        
        # Prepare summary
        memory_summaries = "\n".join([
            f"- {m.created_at.strftime('%B')}: {m.title}"
            for m in memories[:30]
        ])
        
        system_prompt = f"""Создай вдохновляющее резюме года для пользователя.
Год: {year}
Количество воспоминаний: {len(memories)}

Включи:
1. Краткое введение о годе
2. Ключевые темы и моменты
3. Личностный рост и достижения
4. Вдохновляющее заключение

Воспоминания:
{memory_summaries}

Напиши тепло, лично и вдохновляюще. 300-400 слов."""
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Создай резюме моего {year} года."},
                ],
                temperature=0.8,
                max_tokens=600,
            )
            
            summary_text = response.choices[0].message.content
            
            return {
                "year": year,
                "summary": summary_text,
                "memories_count": len(memories),
                "tokens_used": response.usage.total_tokens,
            }
        
        except Exception as e:
            raise Exception(f"Year summary failed: {str(e)}")
