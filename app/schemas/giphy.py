"""Pydantic schemas for Giphy proxy"""
from pydantic import BaseModel, Field


class GiphyItem(BaseModel):
    id: str
    preview_url: str
    url: str
    width: int = 0
    height: int = 0


class GiphyListResponse(BaseModel):
    gifs: list[GiphyItem]
    total: int = 0
    offset: int = 0
    limit: int = Field(default=24)
