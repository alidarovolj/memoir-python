"""Pet shop service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.models.pet_item import PetItem, UserPetItem, ItemType, ItemRarity
from app.models.pet import Pet
from app.models.user import User


class PetShopService:
    """Service for pet shop operations"""
    
    @staticmethod
    async def get_shop_items(db: AsyncSession, user_id: str) -> List[dict]:
        """Get all shop items with user's ownership status"""
        # Get all items
        result = await db.execute(select(PetItem))
        all_items = result.scalars().all()
        
        # Get user's pet and owned items
        pet_result = await db.execute(select(Pet).where(Pet.user_id == user_id))
        pet = pet_result.scalar_one_or_none()
        
        owned_result = await db.execute(
            select(UserPetItem).where(UserPetItem.user_id == user_id)
        )
        owned_items = {str(item.item_id): item for item in owned_result.scalars().all()}
        
        # Build response
        items_response = []
        for item in all_items:
            user_item = owned_items.get(str(item.id))
            
            # Check if unlocked
            is_unlocked = PetShopService._check_unlock_requirement(
                item.unlock_requirement, pet
            )
            
            items_response.append({
                "id": str(item.id),
                "itemType": item.item_type.value,
                "name": item.name,
                "emoji": item.emoji,
                "description": item.description,
                "costXp": item.cost_xp,
                "rarity": item.rarity.value,
                "unlockRequirement": item.unlock_requirement or {},
                "isUnlocked": is_unlocked,
                "isOwned": user_item is not None,
                "isEquipped": user_item.equipped if user_item else False,
            })
        
        return items_response
    
    @staticmethod
    def _check_unlock_requirement(requirement: dict, pet: Pet | None) -> bool:
        """Check if item unlock requirement is met"""
        if not requirement or not pet:
            return True
        
        # Check level requirement
        if "level" in requirement:
            if pet.level < requirement["level"]:
                return False
        
        # TODO: Check achievement requirement when implemented
        
        return True
    
    @staticmethod
    async def purchase_item(
        db: AsyncSession,
        user_id: str,
        item_id: str,
    ) -> dict:
        """Purchase an item"""
        # Get item
        item_result = await db.execute(
            select(PetItem).where(PetItem.id == UUID(item_id))
        )
        item = item_result.scalar_one_or_none()
        if not item:
            raise ValueError("Item not found")
        
        # Check if already owned
        existing_result = await db.execute(
            select(UserPetItem).where(
                UserPetItem.user_id == user_id,
                UserPetItem.item_id == item_id,
            )
        )
        if existing_result.scalar_one_or_none():
            raise ValueError("Item already owned")
        
        # Get pet
        pet_result = await db.execute(select(Pet).where(Pet.user_id == user_id))
        pet = pet_result.scalar_one_or_none()
        if not pet:
            raise ValueError("Pet not found")
        
        # Check unlock requirement
        if not PetShopService._check_unlock_requirement(item.unlock_requirement, pet):
            raise ValueError("Item unlock requirement not met")
        
        # Check if enough XP
        if pet.xp < item.cost_xp:
            raise ValueError(f"Not enough XP. Need {item.cost_xp}, have {pet.xp}")
        
        # Deduct XP
        pet.xp -= item.cost_xp
        
        # Create ownership
        user_item = UserPetItem(
            user_id=UUID(user_id),
            item_id=UUID(item_id),
            equipped=False,
        )
        
        db.add(user_item)
        await db.commit()
        await db.refresh(user_item)
        await db.refresh(pet)
        
        return {
            "message": f"Purchased {item.name}!",
            "item": item,
            "remaining_xp": pet.xp,
        }
    
    @staticmethod
    async def equip_item(
        db: AsyncSession,
        user_id: str,
        item_id: str,
        equipped: bool,
    ) -> dict:
        """Equip or unequip an item"""
        # Get user's item
        result = await db.execute(
            select(UserPetItem).where(
                UserPetItem.user_id == user_id,
                UserPetItem.item_id == item_id,
            )
        )
        user_item = result.scalar_one_or_none()
        if not user_item:
            raise ValueError("Item not owned")
        
        # If equipping, unequip other items of same type
        if equipped:
            item_result = await db.execute(
                select(PetItem).where(PetItem.id == UUID(item_id))
            )
            item = item_result.scalar_one()
            
            # Unequip other items of same type
            other_items_result = await db.execute(
                select(UserPetItem)
                .join(PetItem, UserPetItem.item_id == PetItem.id)
                .where(
                    UserPetItem.user_id == user_id,
                    PetItem.item_type == item.item_type,
                    UserPetItem.equipped == True,
                )
            )
            for other_item in other_items_result.scalars().all():
                other_item.equipped = False
        
        # Update equipped status
        user_item.equipped = equipped
        
        await db.commit()
        await db.refresh(user_item)
        
        return {
            "message": f"Item {'equipped' if equipped else 'unequipped'}!",
            "item": user_item,
        }
    
    @staticmethod
    async def get_user_inventory(db: AsyncSession, user_id: str) -> List[dict]:
        """Get user's owned items"""
        result = await db.execute(
            select(UserPetItem)
            .where(UserPetItem.user_id == user_id)
            .join(PetItem, UserPetItem.item_id == PetItem.id)
        )
        
        items = []
        for user_item in result.scalars().all():
            await db.refresh(user_item, ["item"])
            items.append({
                "id": str(user_item.id),
                "userId": str(user_item.user_id),
                "itemId": str(user_item.item_id),
                "equipped": user_item.equipped,
                "purchasedAt": str(user_item.purchased_at),
                "item": {
                    "id": str(user_item.item.id),
                    "itemType": user_item.item.item_type.value,
                    "name": user_item.item.name,
                    "emoji": user_item.item.emoji,
                    "description": user_item.item.description,
                    "costXp": user_item.item.cost_xp,
                    "rarity": user_item.item.rarity.value,
                },
            })
        
        return items
    
    @staticmethod
    async def seed_default_items(db: AsyncSession):
        """Seed database with default shop items"""
        default_items = [
            # Hats
            PetItem(
                item_type=ItemType.HAT,
                name="Топ шляпа",
                emoji="🎩",
                description="Классическая топ шляпа для стильного питомца",
                cost_xp=100,
                rarity=ItemRarity.COMMON,
            ),
            PetItem(
                item_type=ItemType.HAT,
                name="Корона",
                emoji="👑",
                description="Для истинных королей!",
                cost_xp=500,
                rarity=ItemRarity.EPIC,
                unlock_requirement={"level": 20},
            ),
            # Glasses
            PetItem(
                item_type=ItemType.GLASSES,
                name="Крутые очки",
                emoji="😎",
                description="Выглядь круто!",
                cost_xp=150,
                rarity=ItemRarity.COMMON,
            ),
            # Effects
            PetItem(
                item_type=ItemType.EFFECT,
                name="Sparkle эффект",
                emoji="🌟",
                description="Блестящий эффект вокруг питомца",
                cost_xp=1000,
                rarity=ItemRarity.LEGENDARY,
                unlock_requirement={"level": 40},
            ),
            PetItem(
                item_type=ItemType.EFFECT,
                name="Радужный эффект",
                emoji="🌈",
                description="Радуга следует за питомцем",
                cost_xp=300,
                rarity=ItemRarity.RARE,
            ),
        ]
        
        for item in default_items:
            db.add(item)
        
        await db.commit()
