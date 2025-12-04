"""AI service for task analysis and suggestions"""
from typing import Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.task import TimeScope, TaskPriority
import json


class TaskAIService:
    """Service for AI-powered task analysis"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def analyze_task(self, title: str) -> Dict[str, Any]:
        """
        Analyze task title and suggest time_scope, priority, and category
        
        Args:
            title: Task title/description
            
        Returns:
            Dict with suggested time_scope, priority, confidence, and reasoning
        """
        system_prompt = """Ты — AI-ассистент для приложения планирования задач.
Твоя задача: проанализировать название задачи и определить:

1. **time_scope** (временной масштаб):
   - "daily" - ежедневные задачи (чистка зубов, зарядка, готовка)
   - "weekly" - недельные задачи (покупки, уборка, встречи)
   - "monthly" - месячные задачи (оплата счетов, планирование)
   - "long_term" - долгосрочные цели (выучить язык, похудеть, карьера)

2. **priority** (приоритет):
   - "low" - низкий (можно отложить)
   - "medium" - средний (обычные задачи)
   - "high" - высокий (важно сделать скоро)
   - "urgent" - срочно (нужно сделать сегодня/сейчас)

3. **suggested_time** (рекомендуемое время выполнения в формате HH:MM):
   - Для ежедневных задач предлагай конкретное время
   - Примеры: "08:00" (утренние задачи), "12:00" (обеденные), "20:00" (вечерние)
   - Для weekly/monthly/long_term - null

4. **needs_deadline** (требуется ли строгий дедлайн):
   - true - если задача имеет конкретный срок (оплата счетов, встречи, дедлайны)
   - false - для регулярных задач без строгого срока (чистка зубов, зарядка)

5. **category** (категория, если применимо):
   - "movies" - фильмы, сериалы
   - "books" - книги, чтение
   - "places" - места для посещения
   - "recipes" - готовка, рецепты
   - "ideas" - идеи, мысли
   - "products" - покупки
   - null - если не подходит ни одна категория

Примеры:
- "Почистить зубы" → daily, medium, "08:00", false, null
- "Посмотреть Начало" → weekly, medium, null, false, movies
- "Купить молоко" → daily, high, "18:00", false, products
- "Оплатить интернет" → monthly, high, "10:00", true, null
- "Позвонить маме" → daily, high, "19:00", false, null
- "Убраться в квартире" → weekly, medium, null, false, null

Верни ТОЛЬКО валидный JSON без дополнительного текста:
{
  "time_scope": "daily",
  "priority": "medium",
  "suggested_time": "08:00",
  "needs_deadline": false,
  "category": "movies",
  "confidence": 0.95,
  "reasoning": "Краткое объяснение"
}"""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_CLASSIFICATION,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Проанализируй задачу: {title}"}
                ],
                temperature=0.3,
                max_tokens=200,
            )

            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            result = json.loads(content)
            
            return {
                "time_scope": result.get("time_scope", "daily"),
                "priority": result.get("priority", "medium"),
                "suggested_time": result.get("suggested_time"),
                "needs_deadline": result.get("needs_deadline", False),
                "category": result.get("category"),
                "confidence": result.get("confidence", 0.8),
                "reasoning": result.get("reasoning", "AI-анализ задачи")
            }

        except Exception as e:
            print(f"❌ [TASK_AI] Error analyzing task: {e}")
            # Fallback to defaults
            return {
                "time_scope": "daily",
                "priority": "medium",
                "suggested_time": None,
                "needs_deadline": False,
                "category": None,
                "confidence": 0.5,
                "reasoning": "Не удалось проанализировать (используются значения по умолчанию)"
            }

