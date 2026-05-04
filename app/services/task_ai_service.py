"""AI service for task analysis and suggestions using Gemini"""
import json
from typing import Dict, Any, List
from google import genai
from google.genai import types
from app.core.config import settings
from app.models.task import TimeScope, TaskPriority
from app.models.memory import Memory


def _parse_json(text: str) -> dict:
    """Parse JSON from model response, robustly extracting and fixing the first valid JSON object."""
    import re as _re
    text = text.strip()
    # Strip markdown fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    # Find first { or [
    start = text.find("{")
    if start == -1:
        start = text.find("[")
    if start != -1:
        text = text[start:]
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fix trailing commas: ,} and ,]
    fixed = _re.sub(r",\s*}", "}", text)
    fixed = _re.sub(r",\s*]", "]", fixed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    # Try to extract balanced JSON by counting braces
    depth = 0
    in_string = False
    escape = False
    end_pos = 0
    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_pos = i + 1
                break
    if end_pos > 0:
        truncated = text[:end_pos]
        truncated = _re.sub(r",\s*}", "}", truncated)
        truncated = _re.sub(r",\s*]", "]", truncated)
        try:
            return json.loads(truncated)
        except json.JSONDecodeError:
            pass
    # Final fallback: raise original error
    return json.loads(text)


class TaskAIService:
    """Service for AI-powered task analysis using Gemini"""

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    def _make_config(
        self,
        system_instruction: str,
        temperature: float = 0.3,
        max_output_tokens: int = 32768,
    ) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    async def analyze_task(self, title: str) -> Dict[str, Any]:
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

5. **needs_deadline** (требуется ли строгий дедлайн):
   - true - если задача имеет конкретный срок (оплата счетов, встречи, дедлайны)
   - false - для регулярных задач без строгого срока

6. **is_recurring** (повторяющаяся ли задача):
   - true - если задача должна повторяться регулярно (чистка зубов, зарядка, душ)
   - false - если задача одноразовая (купить что-то, посмотреть фильм, встреча)

7. **category** (категория, если применимо):
   - "movies", "books", "places", "recipes", "ideas", "products", null

Верни ТОЛЬКО валидный JSON без дополнительного текста:
{
  "time_scope": "daily",
  "priority": "medium",
  "suggested_time": "08:00",
  "suggested_due_date": "today",
  "needs_deadline": false,
  "is_recurring": true,
  "category": null,
  "confidence": 0.95,
  "reasoning": "Краткое объяснение"
}"""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=f"Проанализируй задачу: {title}",
                config=self._make_config(system_prompt, temperature=0.3),
            )
            result = _parse_json(response.text)

            return {
                "time_scope": result.get("time_scope", "daily"),
                "priority": result.get("priority", "medium"),
                "suggested_time": result.get("suggested_time"),
                "suggested_due_date": result.get("suggested_due_date"),
                "needs_deadline": result.get("needs_deadline", False),
                "is_recurring": result.get("is_recurring", False),
                "category": result.get("category"),
                "confidence": result.get("confidence", 0.8),
                "reasoning": result.get("reasoning", "AI-анализ задачи"),
            }

        except Exception as e:
            print(f"❌ [TASK_AI] Error analyzing task: {e}")
            return {
                "time_scope": "daily",
                "priority": "medium",
                "suggested_time": None,
                "suggested_due_date": None,
                "needs_deadline": False,
                "is_recurring": False,
                "category": None,
                "confidence": 0.5,
                "reasoning": "Не удалось проанализировать (используются значения по умолчанию)",
            }

    async def suggest_tasks_from_memory(
        self,
        memory: Memory,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        category_name = memory.category.name if memory.category else "other"

        system_prompt = """Ты — AI-ассистент для приложения Personal Memory & Planning.
Пользователь сохранил воспоминание. Твоя задача: предложить 2-3 релевантные задачи на будущее.

Формат ответа — ТОЛЬКО валидный JSON без дополнительного текста:
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

Требования:
- Предложи ровно 2-3 задачи (не больше, не меньше)
- Задачи должны быть конкретными и действенными
- confidence от 0.7 до 1.0
- time_scope: daily/weekly/monthly/long_term
- priority: low/medium/high/urgent
- reasoning: короткое объяснение (1 предложение)"""

        user_prompt = f"""Воспоминание:
Категория: {category_name}
Название: {memory.title}
Описание: {memory.content[:500]}

Предложи {limit} релевантные задачи на будущее."""

        try:
            print(f"🤖 [TASK_AI] Generating suggestions for memory: {memory.title}")
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=self._make_config(system_prompt, temperature=0.7, max_output_tokens=800),
            )
            print(f"🤖 [TASK_AI] Raw response: {response.text[:200]}...")

            result = _parse_json(response.text)
            suggestions = result.get("suggestions", [])
            print(f"✅ [TASK_AI] Generated {len(suggestions)} suggestions")

            valid_suggestions = []
            for suggestion in suggestions[:limit]:
                if all(k in suggestion for k in ["title", "description", "time_scope", "priority"]):
                    valid_suggestions.append({
                        "title": suggestion["title"],
                        "description": suggestion["description"],
                        "time_scope": suggestion["time_scope"],
                        "priority": suggestion["priority"],
                        "confidence": suggestion.get("confidence", 0.8),
                        "reasoning": suggestion.get("reasoning", "AI рекомендация"),
                        "category": category_name if category_name != "other" else None,
                    })

            return valid_suggestions

        except Exception as e:
            print(f"❌ [TASK_AI] Error generating suggestions: {e}")
            return []

    async def analyze_habit(
        self,
        title: str,
        subtasks_count: int | None = None,
    ) -> Dict[str, Any]:
        if subtasks_count is None:
            count_instruction = (
                "ВАЖНО: Ты сам определяешь оптимальное количество задач на основе глубокого анализа привычки! "
                "Не ограничивай себя — если нужно 2 задачи, создай 2, если нужно 8 — создай 8."
            )
        else:
            count_instruction = f"Создай ровно {subtasks_count} конкретных подзадач"

        system_prompt = f"""Ты — AI-ассистент для приложения планирования привычек и целей.
Твоя задача: проанализировать глобальную цель/привычку и создать группу ежедневных подзадач.

Количество: {count_instruction}

Правила:
- Большинство подзадач должны быть ежедневными (is_recurring: true)
- Разнообразие: физические + ментальные + практические действия
- Время: распредели по времени суток (утро, день, вечер)
- Цвета в hex-формате: #EF4444 (красный), #F97316 (оранжевый), #FBBF24 (желтый), #10B981 (зеленый), #3B82F6 (синий), #8B5CF6 (фиолетовый)
- Иконки в формате "Ionicons.icon_name_outline"
- Для каждой задачи создай 2-4 конкретных шага (subtasks)

Верни ТОЛЬКО валидный JSON:
{{
  "group_name": "Название группы",
  "group_icon": "🎯",
  "subtasks": [
    {{
      "title": "Название задачи",
      "description": "Зачем нужна эта задача",
      "priority": "medium",
      "suggested_time": "08:00",
      "color": "#3B82F6",
      "icon": "Ionicons.water_outline",
      "is_recurring": true,
      "subtasks": ["Шаг 1", "Шаг 2", "Шаг 3"]
    }}
  ],
  "confidence": 0.95,
  "reasoning": "Краткое объяснение"
}}"""

        if subtasks_count is None:
            user_prompt = f"Habit/goal: {title}"
        else:
            user_prompt = f"Habit/goal: {title}. Subtasks count: {subtasks_count}"

        try:
            print(f"🤖 [TASK_AI] Analyzing habit: {title}")
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=self._make_config(system_prompt, temperature=0.8, max_output_tokens=32768),
            )
            print(f"🤖 [TASK_AI] Raw response: {response.text[:200]}...")

            result = _parse_json(response.text)
            print(f"✅ [TASK_AI] Generated {len(result.get('subtasks', []))} subtasks")

            return {
                "group_name": result.get("group_name", title),
                "group_icon": result.get("group_icon", "🎯"),
                "subtasks": result.get("subtasks", []),
                "confidence": result.get("confidence", 0.8),
                "reasoning": result.get("reasoning", "AI-анализ привычки"),
            }

        except Exception as e:
            print(f"❌ [TASK_AI] Error analyzing habit: {e}")
            return {
                "group_name": title,
                "group_icon": "🎯",
                "subtasks": [],
                "confidence": 0.5,
                "reasoning": "Не удалось проанализировать (используйте ручное создание)",
            }
