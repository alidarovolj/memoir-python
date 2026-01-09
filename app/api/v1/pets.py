"""
Pet API endpoints - Virtual companion management

Routes:
- POST /api/v1/pets - Create new pet
- GET /api/v1/pets/me - Get user's pet
- POST /api/v1/pets/feed - Feed pet (create memory action)
- POST /api/v1/pets/play - Play with pet (complete task action)
- PUT /api/v1/pets/name - Update pet name
- GET /api/v1/pets/stats - Get pet statistics
- GET /api/v1/pets/available-types - Get available pet types (NEW)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.pet import Pet, PetType as ModelPetType, EvolutionStage as ModelEvolutionStage
from app.schemas.pet import (
    PetCreate,
    PetResponse,
    PetActionResponse,
    PetUpdateName,
    PetStats,
)
from app.services.pet_service import PetService

router = APIRouter()


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def create_pet(
    pet_data: PetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new virtual pet for the user
    
    User can only have one pet at a time.
    Has 5% chance to be shiny with special effects!
    """
    # Check if user already has a pet
    result = await db.execute(select(Pet).filter(Pet.user_id == current_user.id))
    existing_pet = result.scalar_one_or_none()
    
    if existing_pet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pet. Each user can only have one pet."
        )
    
    # Create new pet using PetService (handles shiny chance)
    pet_type_enum = ModelPetType(pet_data.pet_type)
    new_pet = await PetService.create_pet(
        db=db,
        user_id=str(current_user.id),
        pet_type=pet_type_enum,
        name=pet_data.name,
    )
    
    # Convert to response
    response = _pet_to_response(new_pet)
    return response


@router.get("/available-types")
async def get_available_pet_types():
    """
    Get all available pet types with info
    
    Returns list of pet types with names, emojis, descriptions, and rarity
    """
    return await PetService.get_available_types()


@router.get("/me", response_model=Optional[PetResponse])
async def get_my_pet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's pet
    
    Returns None if user doesn't have a pet yet.
    """
    result = await db.execute(select(Pet).filter(Pet.user_id == current_user.id))
    pet = result.scalar_one_or_none()
    
    if not pet:
        return None
    
    # Check for stat decay
    await _check_and_update_stats(pet, db)
    
    return _pet_to_response(pet)


@router.post("/feed", response_model=PetActionResponse)
async def feed_pet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Feed the pet (triggered when user creates a memory)
    
    - Increases happiness by 10
    - Gives 10 XP
    - May trigger level up or evolution
    """
    result = await db.execute(select(Pet).filter(Pet.user_id == current_user.id))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a pet yet. Create one first!"
        )
    
    # Feed the pet
    feed_result = pet.feed(xp_amount=10)
    from datetime import timezone
    pet.last_fed = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(pet)
    
    # Build response message
    message = f"🍔 You fed {pet.name}! "
    if feed_result["level_ups"] > 0:
        message += f"🎉 Level up! Now level {feed_result['current_level']}. "
    if feed_result["evolved"]:
        message += f"✨ {pet.name} evolved to {feed_result['current_stage']}! "
    
    return PetActionResponse(
        message=message,
        pet=_pet_to_response(pet),
        level_ups=feed_result["level_ups"],
        evolved=feed_result["evolved"],
    )


@router.post("/play", response_model=PetActionResponse)
async def play_with_pet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Play with the pet (triggered when user completes a task)
    
    - Increases health by 15
    - Gives 15 XP (more than feeding)
    - May trigger level up or evolution
    """
    result = await db.execute(select(Pet).filter(Pet.user_id == current_user.id))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a pet yet. Create one first!"
        )
    
    # Play with the pet
    play_result = pet.play(xp_amount=15)
    from datetime import timezone
    pet.last_played = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(pet)
    
    # Build response message
    message = f"🎾 You played with {pet.name}! "
    if play_result["level_ups"] > 0:
        message += f"🎉 Level up! Now level {play_result['current_level']}. "
    if play_result["evolved"]:
        message += f"✨ {pet.name} evolved to {play_result['current_stage']}! "
    
    return PetActionResponse(
        message=message,
        pet=_pet_to_response(pet),
        level_ups=play_result["level_ups"],
        evolved=play_result["evolved"],
    )


@router.put("/name", response_model=PetResponse)
async def update_pet_name(
    name_data: PetUpdateName,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update pet's name
    """
    result = await db.execute(select(Pet).filter(Pet.user_id == current_user.id))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a pet yet. Create one first!"
        )
    
    pet.name = name_data.name
    from datetime import timezone
    pet.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(pet)
    
    return _pet_to_response(pet)


@router.get("/stats", response_model=PetStats)
async def get_pet_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get pet statistics (compact version)
    """
    result = await db.execute(select(Pet).filter(Pet.user_id == current_user.id))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a pet yet. Create one first!"
        )
    
    await _check_and_update_stats(pet, db)
    
    return PetStats(
        level=pet.level,
        xp=pet.xp,
        xp_for_next_level=pet.xp_for_next_level,
        evolution_stage=pet.evolution_stage.value,
        happiness=pet.happiness,
        health=pet.health,
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_pet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete current user's pet (for testing/debugging)
    """
    result = await db.execute(select(Pet).filter(Pet.user_id == current_user.id))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a pet to delete"
        )
    
    await db.delete(pet)
    await db.commit()
    
    return None


# Helper functions

def _pet_to_response(pet: Pet) -> PetResponse:
    """Convert Pet model to PetResponse"""
    from datetime import datetime
    
    # Determine time of day
    hour = datetime.now().hour
    if hour < 6 or hour >= 22:
        time_of_day = "night"
    elif hour < 12:
        time_of_day = "morning"
    elif hour < 18:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"
    
    # Get emotion and speech bubble
    emotion = pet.get_emotion(time_of_day)
    speech_bubble = pet.get_speech_bubble(emotion)
    
    return PetResponse(
        id=str(pet.id),
        user_id=str(pet.user_id),
        pet_type=pet.pet_type.value,
        name=pet.name,
        level=pet.level,
        xp=pet.xp,
        xp_for_next_level=pet.xp_for_next_level,
        evolution_stage=pet.evolution_stage.value,
        happiness=pet.happiness,
        health=pet.health,
        last_fed=pet.last_fed,
        last_played=pet.last_played,
        created_at=pet.created_at,
        accessories=pet.accessories,
        is_shiny=pet.is_shiny,
        mutation_type=pet.mutation_type,
        special_effect=pet.special_effect,
        needs_attention=pet.happiness < 30 or pet.health < 30,
        can_evolve=pet.can_evolve(),
        current_emotion=emotion,
        speech_bubble=speech_bubble,
    )


async def _check_and_update_stats(pet: Pet, db: AsyncSession) -> None:
    """
    Check if pet stats need decay and update them
    Called when getting pet info
    """
    from datetime import timezone
    now = datetime.now(timezone.utc)
    
    # Calculate hours since last activities
    hours_since_fed = (now - pet.last_fed).total_seconds() / 3600 if pet.last_fed else 0
    hours_since_played = (now - pet.last_played).total_seconds() / 3600 if pet.last_played else 0
    
    # Only decay if more than 24 hours passed
    if hours_since_fed > 24 or hours_since_played > 24:
        max_hours = max(hours_since_fed, hours_since_played)
        result = pet.decay_stats(int(max_hours))
        
        # Save if stats changed
        if result["happiness"] != pet.happiness or result["health"] != pet.health:
            pet.updated_at = datetime.now(timezone.utc)
            await db.commit()
