"""Universal search service combining AI intent and external APIs"""
from typing import Dict, Any, List
from app.services.ai_service import ai_service
from app.services.external_search_service import external_search_service


class UniversalSearchService:
    """AI-powered universal search service"""
    
    async def smart_search(
        self, 
        user_input: str,
        force_intent: str | None = None,
    ) -> Dict[str, Any]:
        """
        Smart search with AI intent detection
        
        Args:
            user_input: User's input text
            force_intent: Force specific intent (optional)
        
        Returns:
            Search results with intent information
        """
        # Step 1: AI Intent Detection (if not forced)
        if force_intent:
            intent_data = {
                "intent": force_intent,
                "search_query": user_input,
                "needs_search": force_intent not in ["idea", "task"],
                "confidence": 1.0,
                "reasoning": "Forced intent",
            }
        else:
            intent_data = await ai_service.detect_content_intent(user_input)
        
        result = {
            "intent": intent_data["intent"],
            "search_query": intent_data["search_query"],
            "needs_search": intent_data["needs_search"],
            "confidence": intent_data["confidence"],
            "sources": {}
        }
        
        # If no search needed (ideas, tasks)
        if not intent_data["needs_search"]:
            return result
        
        # Step 2: Search in appropriate sources
        search_query = intent_data["search_query"]
        intent = intent_data["intent"]
        
        if intent == "movie":
            movies = await external_search_service.search_movies(search_query)
            if movies:
                result["sources"]["tmdb"] = movies
        
        elif intent == "book":
            books = await external_search_service.search_books(search_query)
            if books:
                result["sources"]["google_books"] = books
        
        elif intent in ["product", "place"]:
            # Universal web search for products and places
            web_results = await external_search_service.search_web(search_query)
            if web_results:
                result["sources"]["web"] = web_results
        
        # Step 3: Fallback to web search if no results
        if not result["sources"]:
            web_results = await external_search_service.search_web(search_query)
            if web_results:
                result["sources"]["web"] = web_results
        
        return result
    
    async def get_content_details(
        self,
        external_id: str,
        source: str,
        content_type: str,
    ) -> Dict[str, Any]:
        """
        Get detailed information for selected content
        
        Args:
            external_id: External content ID
            source: Source (tmdb, google_books, web)
            content_type: Type (movie, book, etc)
        
        Returns:
            Detailed content information
        """
        if source == "tmdb" and content_type == "movie":
            return await external_search_service.get_movie_details(external_id)
        
        # For other sources, return basic info (already have it from search)
        return {
            "external_id": external_id,
            "source": source,
            "type": content_type,
        }


# Singleton instance
universal_search_service = UniversalSearchService()

