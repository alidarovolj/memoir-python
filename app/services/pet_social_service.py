"""Pet social service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from uuid import UUID
from datetime import datetime

from app.models.pet_social import PetVisit, PetGift, GiftType
from app.models.pet import Pet
from app.models.user import User


class PetSocialService:
    """Service for pet social features"""
    
    @staticmethod
    async def get_village(db: AsyncSession, user_id: str, limit: int = 20) -> List[dict]:
        """Get pet village - list of other users' pets"""
        # Get all users with pets except current user
        result = await db.execute(
            select(User, Pet)
            .join(Pet, User.id == Pet.user_id)
            .where(User.id != user_id)
            .order_by(desc(Pet.level))
            .limit(limit)
        )
        
        pets = []
        for user, pet in result.all():
            pets.append({
                "userId": str(user.id),
                "username": user.username or user.email.split('@')[0],
                "petName": pet.name,
                "petType": pet.pet_type.value,
                "petLevel": pet.level,
                "evolutionStage": pet.evolution_stage.value,
                "isShiny": pet.is_shiny,
            })
        
        return pets
    
    @staticmethod
    async def visit_pet(db: AsyncSession, visitor_id: str, visited_id: str) -> dict:
        """Visit another user's pet"""
        # Check if users exist and have pets
        visited_result = await db.execute(select(Pet).where(Pet.user_id == visited_id))
        visited_pet = visited_result.scalar_one_or_none()
        if not visited_pet:
            raise ValueError("Visited user doesn't have a pet")
        
        # Create visit record
        visit = PetVisit(
            visitor_id=UUID(visitor_id),
            visited_id=UUID(visited_id),
        )
        db.add(visit)
        await db.commit()
        
        return {
            "message": f"Visited {visited_pet.name}!",
            "pet": {
                "name": visited_pet.name,
                "type": visited_pet.pet_type.value,
                "level": visited_pet.level,
            }
        }
    
    @staticmethod
    async def send_gift(
        db: AsyncSession,
        from_user_id: str,
        to_user_id: str,
        gift_type: GiftType,
    ) -> dict:
        """Send a gift to another user's pet"""
        if from_user_id == to_user_id:
            raise ValueError("Cannot send gift to yourself")
        
        # Check if recipient has pet
        recipient_result = await db.execute(select(Pet).where(Pet.user_id == to_user_id))
        recipient_pet = recipient_result.scalar_one_or_none()
        if not recipient_pet:
            raise ValueError("Recipient doesn't have a pet")
        
        # Create gift
        gift = PetGift(
            from_user_id=UUID(from_user_id),
            to_user_id=UUID(to_user_id),
            gift_type=gift_type,
        )
        db.add(gift)
        await db.commit()
        await db.refresh(gift)
        
        return {
            "message": f"Sent {gift_type.value} to {recipient_pet.name}!",
            "gift": {
                "id": str(gift.id),
                "giftType": gift.gift_type.value,
                "sentAt": str(gift.sent_at),
            }
        }
    
    @staticmethod
    async def get_gifts(db: AsyncSession, user_id: str) -> List[dict]:
        """Get user's received gifts"""
        result = await db.execute(
            select(PetGift, User)
            .join(User, PetGift.from_user_id == User.id)
            .where(PetGift.to_user_id == user_id)
            .order_by(desc(PetGift.sent_at))
        )
        
        gifts = []
        for gift, sender in result.all():
            gifts.append({
                "id": str(gift.id),
                "fromUserId": str(gift.from_user_id),
                "fromUsername": sender.username or sender.email.split('@')[0],
                "giftType": gift.gift_type.value,
                "claimed": gift.claimed,
                "sentAt": str(gift.sent_at),
            })
        
        return gifts
    
    @staticmethod
    async def claim_gift(db: AsyncSession, user_id: str, gift_id: str) -> dict:
        """Claim a received gift"""
        # Get gift
        result = await db.execute(
            select(PetGift).where(
                PetGift.id == UUID(gift_id),
                PetGift.to_user_id == user_id,
            )
        )
        gift = result.scalar_one_or_none()
        if not gift:
            raise ValueError("Gift not found")
        
        if gift.claimed:
            raise ValueError("Gift already claimed")
        
        # Get pet
        pet_result = await db.execute(select(Pet).where(Pet.user_id == user_id))
        pet = pet_result.scalar_one_or_none()
        if not pet:
            raise ValueError("Pet not found")
        
        # Apply gift effects
        if gift.gift_type == GiftType.TREAT:
            pet.happiness = min(100, pet.happiness + 15)
            pet.xp += 5
        elif gift.gift_type == GiftType.TOY:
            pet.health = min(100, pet.health + 15)
            pet.xp += 5
        elif gift.gift_type == GiftType.HUG:
            pet.happiness = min(100, pet.happiness + 10)
            pet.health = min(100, pet.health + 10)
        
        # Mark as claimed
        gift.claimed = True
        gift.claimed_at = str(datetime.now())
        
        await db.commit()
        await db.refresh(pet)
        
        return {
            "message": f"Claimed {gift.gift_type.value}!",
            "pet": {
                "happiness": pet.happiness,
                "health": pet.health,
                "xp": pet.xp,
            }
        }
    
    @staticmethod
    async def get_leaderboard(
        db: AsyncSession,
        category: str = "level",
        limit: int = 50,
    ) -> List[dict]:
        """Get pet leaderboard"""
        # Build query based on category
        if category == "level":
            order_by = [desc(Pet.level), desc(Pet.xp)]
        elif category == "games":
            # Will need to join with game stats when implemented
            order_by = [desc(Pet.level)]
        else:
            order_by = [desc(Pet.level)]
        
        result = await db.execute(
            select(User, Pet)
            .join(Pet, User.id == Pet.user_id)
            .order_by(*order_by)
            .limit(limit)
        )
        
        leaderboard = []
        rank = 1
        for user, pet in result.all():
            leaderboard.append({
                "rank": rank,
                "userId": str(user.id),
                "username": user.username or user.email.split('@')[0],
                "petName": pet.name,
                "petType": pet.pet_type.value,
                "level": pet.level,
                "xp": pet.xp,
                "evolutionStage": pet.evolution_stage.value,
                "isShiny": pet.is_shiny,
            })
            rank += 1
        
        return leaderboard
