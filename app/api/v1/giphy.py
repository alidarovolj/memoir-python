"""Giphy proxy endpoints for chat GIF picker"""
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.giphy import GiphyItem, GiphyListResponse

router = APIRouter()

GIPHY_BASE_URL = "https://api.giphy.com/v1/gifs"


def _parse_giphy_items(payload: dict) -> tuple[list[GiphyItem], int]:
    items: list[GiphyItem] = []
    for entry in payload.get("data", []):
        images = entry.get("images") or {}
        preview = (
            (images.get("fixed_width") or {}).get("url")
            or (images.get("downsized") or {}).get("url")
            or (images.get("original") or {}).get("url")
        )
        full = (
            (images.get("downsized") or {}).get("url")
            or (images.get("fixed_width") or {}).get("url")
            or (images.get("original") or {}).get("url")
        )
        if not preview or not full:
            continue

        width = int((images.get("fixed_width") or {}).get("width") or 0)
        height = int((images.get("fixed_width") or {}).get("height") or 0)
        items.append(
            GiphyItem(
                id=str(entry.get("id") or ""),
                preview_url=preview,
                url=full,
                width=width,
                height=height,
            )
        )

    pagination = payload.get("pagination") or {}
    total = int(pagination.get("total_count") or len(items))
    return items, total


async def _fetch_giphy(path: str, params: dict) -> dict:
    if not settings.GIPHY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Giphy API key is not configured",
        )

    query = {"api_key": settings.GIPHY_API_KEY, "rating": "g", **params}
    url = f"{GIPHY_BASE_URL}/{path}"

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(url, params=query)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Giphy request failed: {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Giphy request failed: {exc}",
        ) from exc


@router.get("/trending", response_model=GiphyListResponse)
async def get_trending_gifs(
    limit: int = Query(default=24, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
):
    payload = await _fetch_giphy("trending", {"limit": limit, "offset": offset})
    gifs, total = _parse_giphy_items(payload)
    return GiphyListResponse(gifs=gifs, total=total, offset=offset, limit=limit)


@router.get("/search", response_model=GiphyListResponse)
async def search_gifs(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(default=24, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
):
    payload = await _fetch_giphy(
        "search",
        {"q": q.strip(), "limit": limit, "offset": offset},
    )
    gifs, total = _parse_giphy_items(payload)
    return GiphyListResponse(gifs=gifs, total=total, offset=offset, limit=limit)
