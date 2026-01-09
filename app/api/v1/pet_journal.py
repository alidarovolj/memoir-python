"""
Pet Journal API endpoints

Routes:
- GET /api/v1/pets/journal - Get pet's journal/timeline
- POST /api/v1/pets/journal - Create journal entry
- GET /api/v1/pets/milestones - Get key milestones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.pet import Pet
from app.schemas.pet_journal import (
    CreateJournalEntryRequest,
    PetJournalEntryResponse,
)
from app.services.pet_journal_service import PetJournalService
from sqlalchemy import select

router = APIRouter()


@router.get("/journal", response_model=List[PetJournalEntryResponse])
async def get_journal(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get pet's journal (timeline of events)
    
    Shows evolution history, milestones, photos
    """
    try:
        # Get user's pet
        result = await db.execute(select(Pet).where(Pet.user_id == current_user.id))
        pet = result.scalar_one_or_none()
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet not found"
            )
        
        entries = await PetJournalService.get_journal(db, str(pet.id))
        return entries
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get journal: {str(e)}"
        )


@router.post("/journal", response_model=PetJournalEntryResponse)
async def create_journal_entry(
    request: CreateJournalEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a journal entry
    
    User can manually add photos or notes
    """
    try:
        # Get user's pet
        result = await db.execute(select(Pet).where(Pet.user_id == current_user.id))
        pet = result.scalar_one_or_none()
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet not found"
            )
        
        entry = await PetJournalService.create_entry(
            db,
            str(pet.id),
            request.entry_type,
            request.title,
            request.description,
            request.image_url,
        )
        
        return {
            "id": str(entry.id),
            "petId": str(entry.pet_id),
            "entryType": entry.entry_type.value,
            "title": entry.title,
            "description": entry.description,
            "imageUrl": entry.image_url,
            "levelAtTime": entry.level_at_time,
            "evolutionStageAtTime": entry.evolution_stage_at_time,
            "createdAt": str(entry.created_at),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entry: {str(e)}"
        )


@router.get("/milestones")
async def get_milestones(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get key pet milestones
    
    Summary of pet's journey
    """
    try:
        # Get user's pet
        result = await db.execute(select(Pet).where(Pet.user_id == current_user.id))
        pet = result.scalar_one_or_none()
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet not found"
            )
        
        milestones = await PetJournalService.get_milestones(db, str(pet.id))
        return milestones
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get milestones: {str(e)}"
        )
