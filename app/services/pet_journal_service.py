"""Pet journal service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from uuid import UUID

from app.models.pet_journal import PetJournalEntry, JournalEntryType
from app.models.pet import Pet


class PetJournalService:
    """Service for pet journal/timeline"""
    
    @staticmethod
    async def create_entry(
        db: AsyncSession,
        pet_id: str,
        entry_type: JournalEntryType,
        title: str,
        description: str = None,
        image_url: str = None,
    ) -> PetJournalEntry:
        """Create a journal entry"""
        # Get pet to record stats at time
        pet_result = await db.execute(select(Pet).where(Pet.id == UUID(pet_id)))
        pet = pet_result.scalar_one_or_none()
        if not pet:
            raise ValueError("Pet not found")
        
        entry = PetJournalEntry(
            pet_id=UUID(pet_id),
            entry_type=entry_type,
            title=title,
            description=description,
            image_url=image_url,
            level_at_time=pet.level,
            evolution_stage_at_time=pet.evolution_stage.value,
        )
        
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        
        return entry
    
    @staticmethod
    async def get_journal(db: AsyncSession, pet_id: str) -> List[dict]:
        """Get pet's journal entries (timeline)"""
        result = await db.execute(
            select(PetJournalEntry)
            .where(PetJournalEntry.pet_id == UUID(pet_id))
            .order_by(desc(PetJournalEntry.created_at))
        )
        
        entries = []
        for entry in result.scalars().all():
            entries.append({
                "id": str(entry.id),
                "petId": str(entry.pet_id),
                "entryType": entry.entry_type.value,
                "title": entry.title,
                "description": entry.description,
                "imageUrl": entry.image_url,
                "levelAtTime": entry.level_at_time,
                "evolutionStageAtTime": entry.evolution_stage_at_time,
                "createdAt": str(entry.created_at),
            })
        
        return entries
    
    @staticmethod
    async def get_milestones(db: AsyncSession, pet_id: str) -> dict:
        """Get key milestones for pet"""
        # Get pet
        pet_result = await db.execute(select(Pet).where(Pet.id == UUID(pet_id)))
        pet = pet_result.scalar_one_or_none()
        if not pet:
            raise ValueError("Pet not found")
        
        # Get evolution entries
        evolutions = await db.execute(
            select(PetJournalEntry)
            .where(
                PetJournalEntry.pet_id == UUID(pet_id),
                PetJournalEntry.entry_type == JournalEntryType.EVOLUTION,
            )
            .order_by(PetJournalEntry.created_at)
        )
        
        return {
            "petName": pet.name,
            "petType": pet.pet_type.value,
            "currentLevel": pet.level,
            "currentStage": pet.evolution_stage.value,
            "createdAt": str(pet.created_at),
            "totalEvolutions": len(list(evolutions.scalars().all())),
            "isShiny": pet.is_shiny,
        }
    
    @staticmethod
    async def auto_create_evolution_entry(db: AsyncSession, pet: Pet):
        """Automatically create evolution journal entry"""
        await PetJournalService.create_entry(
            db,
            str(pet.id),
            JournalEntryType.EVOLUTION,
            f"Эволюция в {pet.evolution_stage.value}!",
            f"{pet.name} evolved to {pet.evolution_stage.value} at level {pet.level}!",
        )
