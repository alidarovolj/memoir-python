"""AI Service for Google Gemini integration"""
import json
import asyncio
from typing import Dict, List, Optional, Any
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.exceptions import AIServiceError


class ClassificationResult:
    """Classification result model"""
    def __init__(
        self,
        category: str,
        confidence: float,
        reasoning: str,
        extracted_data: Dict[str, Any],
    ):
        self.category = category
        self.confidence = confidence
        self.reasoning = reasoning
        self.extracted_data = extracted_data


class AIService:
    """AI service for classification and embeddings using Gemini"""

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL
        self.embedding_model = settings.GEMINI_MODEL_EMBEDDING

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

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Parse JSON from model response, robustly extracting and fixing the first valid JSON object."""
        import re as _re
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        start = text.find("{")
        if start == -1:
            start = text.find("[")
        if start != -1:
            text = text[start:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fixed = _re.sub(r",\s*}", "}", text)
        fixed = _re.sub(r",\s*]", "]", fixed)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
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
        return json.loads(text)

    async def classify_memory(
        self,
        content: str,
        source_type: str = "text",
        title: Optional[str] = None,
    ) -> ClassificationResult:
        try:
            system_prompt = """Ты — AI-ассистент для приложения Personal Memory. 
Твоя задача: классифицировать пользовательский контент в одну из категорий.

Доступные категории:
- movies (фильмы, сериалы, видео)
- books (книги, статьи, блоги)
- places (места, локации, рестораны, кафе)
- ideas (идеи, мысли, инсайты)
- recipes (рецепты, еда)
- products (товары для покупки)

Верни ТОЛЬКО валидный JSON в таком формате:
{
  "category": "название категории",
  "confidence": 0.95,
  "reasoning": "краткое объяснение",
  "extracted_data": {
    "key": "value"
  }
}

Для extracted_data извлеки специфичные данные:
- movies: {"title": "...", "director": "...", "year": ...}
- books: {"title": "...", "author": "...", "genre": "..."}
- places: {"name": "...", "address": "...", "type": "..."}
- ideas: {"topic": "...", "source": "..."}
- recipes: {"dish": "...", "cuisine": "..."}
- products: {"name": "...", "category": "...", "price": "..."}
"""
            user_prompt = f"Контент: {content}"
            if title:
                user_prompt = f"Заголовок: {title}\n{user_prompt}"

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=self._make_config(system_prompt, temperature=0.3, max_output_tokens=500),
            )
            result_json = self._parse_json(response.text)

            return ClassificationResult(
                category=result_json.get("category", "ideas"),
                confidence=result_json.get("confidence", 0.5),
                reasoning=result_json.get("reasoning", ""),
                extracted_data=result_json.get("extracted_data", {}),
            )

        except Exception as e:
            raise AIServiceError(f"Classification failed: {str(e)}")

    async def generate_embedding(self, text: str) -> List[float]:
        try:
            result = await self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            return result.embeddings[0].values

        except Exception as e:
            raise AIServiceError(f"Embedding generation failed: {str(e)}")

    async def generate_tags(self, content: str, max_tags: int = 5) -> List[str]:
        try:
            system_prompt = f"""Сгенерируй до {max_tags} релевантных тегов для контента.
Верни только список тегов через запятую, без нумерации и дополнительного текста.
Теги должны быть на русском языке, короткими и описательными."""

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=content,
                config=self._make_config(system_prompt, temperature=0.5, max_output_tokens=100),
            )
            tags = [tag.strip() for tag in response.text.strip().split(",")]
            return tags[:max_tags]

        except Exception as e:
            raise AIServiceError(f"Tag generation failed: {str(e)}")

    async def extract_entities(
        self,
        content: str,
        category: str,
    ) -> Dict[str, Any]:
        try:
            entity_prompts = {
                "movies": "Извлеки: название фильма, режиссер, актеры, год, жанр",
                "books": "Извлеки: название книги, автор, издательство, жанр, год",
                "places": "Извлеки: название места, адрес, тип места, рейтинг",
                "ideas": "Извлеки: основную тему, источник вдохновения, ключевые концепции",
                "recipes": "Извлеки: название блюда, кухня, время готовки, сложность",
                "products": "Извлеки: название товара, бренд, категория, ориентировочная цена",
            }
            specific_prompt = entity_prompts.get(category, "Извлеки ключевую информацию")
            system_prompt = f"""{specific_prompt}.
Верни ТОЛЬКО валидный JSON с извлеченными данными.
Если информация не найдена, используй null."""

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=content,
                config=self._make_config(system_prompt, temperature=0.2, max_output_tokens=300),
            )
            try:
                return self._parse_json(response.text)
            except Exception:
                return {}

        except Exception as e:
            raise AIServiceError(f"Entity extraction failed: {str(e)}")

    async def detect_content_intent(self, user_input: str) -> Dict[str, Any]:
        try:
            system_prompt = """Проанализируй текст и определи его тип и intent.

Типы контента:
- movie: фильм, сериал, кино, документалка
- book: книга, роман, статья, учебник
- recipe: рецепт, блюдо, готовка, кулинария
- place: ресторан, кафе, город, локация, достопримечательность
- product: товар, покупка, вещь для приобретения
- idea: мысль, идея, заметка (без поиска)
- task: задача, дело, todo, напоминание

Верни JSON:
{
  "intent": "movie",
  "search_query": "Интерстеллар",
  "needs_search": true,
  "confidence": 0.95,
  "reasoning": "краткое объяснение"
}

Правила:
- Если упоминается "купить", "приобрести", "заказать" → product, needs_search=true
- Если "посмотрел", "фильм", "кино", "сериал" → movie, needs_search=true
- Если "прочитал", "книга", "роман" → book, needs_search=true
- Если "рецепт", "приготовить", "блюдо" → recipe, needs_search=true
- Если "ресторан", "кафе", "место" → place, needs_search=true
- Если "идея", "мысль", только размышления → idea, needs_search=false
- Если "надо", "нужно", todo без конкретного объекта → task, needs_search=false
- Для search_query - извлеки только ключевые слова
- Если это просто название — попробуй угадать тип по контексту
"""
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=user_input,
                config=self._make_config(system_prompt, temperature=0.3),
            )
            try:
                return self._parse_json(response.text)
            except Exception:
                return {
                    "intent": "idea",
                    "search_query": user_input,
                    "needs_search": False,
                    "confidence": 0.5,
                    "reasoning": "Failed to parse AI response",
                }

        except Exception as e:
            raise AIServiceError(f"Intent detection failed: {str(e)}")


# Singleton instance
ai_service = AIService()
