"""AI service for task analysis and suggestions"""
from typing import Dict, Any, List
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.task import TimeScope, TaskPriority
from app.models.memory import Memory
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

4. **suggested_due_date** (рекомендуемая дата выполнения):
   - Для daily задач: "today" или "tomorrow"
   - Для weekly задач: "this_week" (в течение 7 дней)
   - Для monthly задач: "this_month" (в течение 30 дней)
   - Для urgent задач: "today"
   - null - если нет конкретного срока
   
   Примеры:
   - "Купить молоко" → "today"
   - "Посмотреть фильм" → "this_week"
   - "Оплатить интернет" → конкретная дата если известно, иначе "this_month"
   - "Почистить зубы" → null (регулярная задача)

5. **needs_deadline** (требуется ли строгий дедлайн):
   - true - если задача имеет конкретный срок (оплата счетов, встречи, дедлайны)
   - false - для регулярных задач без строгого срока (чистка зубов, зарядка)

6. **category** (категория, если применимо):
   - "movies" - фильмы, сериалы
   - "books" - книги, чтение
   - "places" - места для посещения
   - "recipes" - готовка, рецепты
   - "ideas" - идеи, мысли
   - "products" - покупки
   - null - если не подходит ни одна категория

Примеры:
- "Почистить зубы" → daily, medium, "08:00", null, false, null
- "Посмотреть Начало" → weekly, medium, null, "this_week", false, movies
- "Купить молоко" → daily, high, "18:00", "today", false, products
- "Оплатить интернет" → monthly, high, "10:00", "this_month", true, null
- "Позвонить маме" → daily, high, "19:00", "today", false, null
- "Убраться в квартире" → weekly, medium, null, "this_week", false, null

Верни ТОЛЬКО валидный JSON без дополнительного текста:
{
  "time_scope": "daily",
  "priority": "medium",
  "suggested_time": "08:00",
  "suggested_due_date": "today",
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
                "suggested_due_date": result.get("suggested_due_date"),
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
                "suggested_due_date": None,
                "needs_deadline": False,
                "category": None,
                "confidence": 0.5,
                "reasoning": "Не удалось проанализировать (используются значения по умолчанию)"
            }

    async def suggest_tasks_from_memory(
        self,
        memory: Memory,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        AI предлагает задачи на основе воспоминания
        
        Args:
            memory: Воспоминание для анализа
            limit: Максимальное количество предложений
            
        Returns:
            Список предложенных задач с confidence scores
        """
        # Получаем категорию если есть
        category_name = memory.category.name if memory.category else "other"
        
        system_prompt = """Ты — AI-ассистент для приложения Personal Memory & Planning.
Пользователь сохранил воспоминание. Твоя задача: предложить 2-3 релевантные задачи на будущее.

**Правила предложений по категориям:**

📽️ **movies** (фильмы/сериалы):
- Похожие фильмы того же жанра
- Фильмы того же режиссера
- Продолжения/приквелы
- Похожие по настроению

📚 **books** (книги):
- Другие книги автора
- Похожие книги по жанру/теме
- Книги из той же серии
- Похожие по стилю

📍 **places** (места):
- Похожие места/рестораны
- Места поблизости
- Места с похожей кухней/атмосферой
- Достопримечательности в том же городе

💡 **ideas** (идеи):
- Конкретные шаги для реализации
- Связанные идеи для изучения
- Практические действия
- Следующие этапы развития идеи

🍳 **recipes** (рецепты):
- Похожие блюда
- Варианты рецепта
- Блюда из тех же ингредиентов
- Комплементарные блюда

🛍️ **products** (товары):
- Дополнительные аксессуары
- Похожие товары
- Сопутствующие товары
- Альтернативы

**Формат ответа:**
Верни ТОЛЬКО валидный JSON без дополнительного текста:
{
  "suggestions": [
    {
      "title": "Посмотреть Интерстеллар",
      "description": "Похожий научно-фантастический фильм от Кристофера Нолана",
      "time_scope": "weekly",
      "priority": "medium",
      "confidence": 0.95,
      "reasoning": "Тот же режиссер, похожий жанр и темы"
    }
  ]
}

**Требования:**
- Предложи ровно 2-3 задачи (не больше, не меньше)
- Задачи должны быть конкретными и действенными
- Используй формулировку "Посмотреть X", "Прочитать X", "Посетить X"
- confidence должен быть от 0.7 до 1.0 (предлагай только уверенные варианты)
- time_scope: daily/weekly/monthly/long_term
- priority: low/medium/high/urgent
- reasoning: короткое объяснение (1 предложение)

Примеры:

1. Воспоминание: "Посмотрел Начало" (movies)
→ Предложи: "Посмотреть Интерстеллар", "Посмотреть Престиж", "Посмотреть Помни"

2. Воспоминание: "Прочитал 1984" (books)
→ Предложи: "Прочитать Скотный двор", "Прочитать О дивный новый мир", "Прочитать 451 градус по Фаренгейту"

3. Воспоминание: "Посетил ресторан итальянской кухни X" (places)
→ Предложи: "Посетить ресторан Y", "Попробовать ресторан Z", "Сходить в траттория A"

4. Воспоминание: "Идея: создать приложение для X" (ideas)
→ Предложи: "Изучить технологии для X", "Набросать прототип", "Исследовать конкурентов"
"""

        user_prompt = f"""Воспоминание:
Категория: {category_name}
Название: {memory.title}
Описание: {memory.content[:500]}

Предложи {limit} релевантные задачи на будущее."""

        try:
            print(f"🤖 [TASK_AI] Generating suggestions for memory: {memory.title}")
            
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_CLASSIFICATION,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Немного креативности
                max_tokens=800,
            )

            content = response.choices[0].message.content.strip()
            print(f"🤖 [TASK_AI] Raw response: {content[:200]}...")
            
            # Parse JSON response
            result = json.loads(content)
            suggestions = result.get("suggestions", [])
            
            print(f"✅ [TASK_AI] Generated {len(suggestions)} suggestions")
            
            # Validate and filter suggestions
            valid_suggestions = []
            for suggestion in suggestions[:limit]:
                if all(key in suggestion for key in ["title", "description", "time_scope", "priority"]):
                    valid_suggestions.append({
                        "title": suggestion["title"],
                        "description": suggestion["description"],
                        "time_scope": suggestion["time_scope"],
                        "priority": suggestion["priority"],
                        "confidence": suggestion.get("confidence", 0.8),
                        "reasoning": suggestion.get("reasoning", "AI рекомендация"),
                        "category": category_name if category_name != "other" else None
                    })
            
            return valid_suggestions

        except Exception as e:
            print(f"❌ [TASK_AI] Error generating suggestions: {e}")
            # Return empty list on error
            return []

