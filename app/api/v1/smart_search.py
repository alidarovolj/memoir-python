"""Smart content search endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.services.universal_search_service import universal_search_service

router = APIRouter()


class SmartSearchResponse(BaseModel):
    """Smart search response"""
    intent: str
    search_query: str
    needs_search: bool
    confidence: float
    sources: dict


class ContentDetailsRequest(BaseModel):
    """Request for content details"""
    external_id: str
    source: str
    content_type: str


@router.post("/smart-search", response_model=SmartSearchResponse)
async def smart_content_search(
    query: str = Query(..., min_length=2, description="User input text"),
    force_intent: Optional[str] = Query(
        None, 
        description="Force specific intent (movie, book, product, place, idea, task)"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    AI-powered smart content search
    
    1. AI analyzes input and detects intent
    2. Searches in appropriate external sources
    3. Returns rich results with metadata
    
    Examples:
    - "Интерстеллар" → searches TMDB for movies
    - "Надо купить брелок" → searches web for products
    - "Идея для стартапа" → no search needed, just save as idea
    """
    try:
        results = await universal_search_service.smart_search(
            user_input=query,
            force_intent=force_intent,
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post("/content-details")
async def get_content_details(
    request: ContentDetailsRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information for selected content
    
    Args:
        external_id: External content ID (e.g., TMDB movie ID)
        source: Source (tmdb, google_books, web)
        content_type: Type (movie, book, product, etc)
    
    Returns:
        Detailed content information
    """
    try:
        details = await universal_search_service.get_content_details(
            external_id=request.external_id,
            source=request.source,
            content_type=request.content_type,
        )
        return details
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get details: {str(e)}",
        )

