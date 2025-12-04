"""AI Service for OpenAI integration"""
import json
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
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
    """AI service for classification and embeddings"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.classification_model = settings.OPENAI_MODEL_CLASSIFICATION
        self.embedding_model = settings.OPENAI_MODEL_EMBEDDING
    
    async def classify_memory(
        self,
        content: str,
        source_type: str = "text",
        title: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Classify memory content into a category
        
        Args:
            content: Memory content to classify
            source_type: Type of source (text, link, image, voice)
            title: Optional title
        
        Returns:
            ClassificationResult with category and metadata
        """
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
            
            response = await self.client.chat.completions.create(
                model=self.classification_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result_json = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                    result_json = json.loads(result_text)
                else:
                    raise AIServiceError("Failed to parse classification result")
            
            return ClassificationResult(
                category=result_json.get("category", "ideas"),
                confidence=result_json.get("confidence", 0.5),
                reasoning=result_json.get("reasoning", ""),
                extracted_data=result_json.get("extracted_data", {}),
            )
        
        except Exception as e:
            raise AIServiceError(f"Classification failed: {str(e)}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            raise AIServiceError(f"Embedding generation failed: {str(e)}")
    
    async def generate_tags(self, content: str, max_tags: int = 5) -> List[str]:
        """
        Generate tags for content
        
        Args:
            content: Content to generate tags for
            max_tags: Maximum number of tags
        
        Returns:
            List of tags
        """
        try:
            system_prompt = f"""Сгенерируй до {max_tags} релевантных тегов для контента.
Верни только список тегов через запятую, без нумерации и дополнительного текста.
Теги должны быть на русском языке, короткими и описательными."""
            
            response = await self.client.chat.completions.create(
                model=self.classification_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                temperature=0.5,
                max_tokens=100,
            )
            
            tags_text = response.choices[0].message.content.strip()
            tags = [tag.strip() for tag in tags_text.split(",")]
            
            return tags[:max_tags]
        
        except Exception as e:
            raise AIServiceError(f"Tag generation failed: {str(e)}")
    
    async def extract_entities(
        self,
        content: str,
        category: str,
    ) -> Dict[str, Any]:
        """
        Extract entities specific to category
        
        Args:
            content: Content to extract from
            category: Category context
        
        Returns:
            Dictionary of extracted entities
        """
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
            
            response = await self.client.chat.completions.create(
                model=self.classification_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                temperature=0.2,
                max_tokens=300,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                    return json.loads(result_text)
                return {}
        
        except Exception as e:
            raise AIServiceError(f"Entity extraction failed: {str(e)}")
    
    async def detect_content_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Detect user intent from input text
        
        Args:
            user_input: User's input text
        
        Returns:
            Intent information with search query
        """
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
- Для search_query - извлеки только ключевые слова (убери "посмотрел", "купить", "нужно", etc)
- Если это просто название (например "Интерстеллар") - попробуй угадать тип по контексту
"""
            
            response = await self.client.chat.completions.create(
                model=self.classification_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                result_json = json.loads(result_text)
            except json.JSONDecodeError:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                    result_json = json.loads(result_text)
                else:
                    # Fallback
                    return {
                        "intent": "idea",
                        "search_query": user_input,
                        "needs_search": False,
                        "confidence": 0.5,
                        "reasoning": "Failed to parse AI response",
                    }
            
            return result_json
        
        except Exception as e:
            raise AIServiceError(f"Intent detection failed: {str(e)}")


# Singleton instance
ai_service = AIService()

