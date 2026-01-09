"""Pet service for virtual companion logic"""
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.pet import Pet, PetType, EvolutionStage
from app.models.user import User


class PetService:
    """Service for managing virtual pets"""
    
    @staticmethod
    def calculate_shiny_chance() -> bool:
        """5% chance for shiny pet"""
        return random.random() < 0.05
    
    @staticmethod
    def get_random_mutation() -> tuple[str, str]:
        """Get random mutation type and special effect"""
        mutations = [
            ("sparkle", "✨ Блестки"),
            ("aura", "🌟 Аура"),
            ("glow", "💫 Сияние"),
            ("rainbow", "🌈 Радужный эффект"),
        ]
        return random.choice(mutations)
    
    @staticmethod
    async def create_pet(
        db: AsyncSession,
        user_id: str,
        pet_type: PetType,
        name: str,
    ) -> Pet:
        """Create new pet for user"""
        # Check if shiny
        is_shiny = PetService.calculate_shiny_chance()
        mutation_type = None
        special_effect = None
        
        if is_shiny:
            mutation_type, special_effect = PetService.get_random_mutation()
        
        pet = Pet(
            user_id=user_id,
            pet_type=pet_type,
            name=name,
            is_shiny=is_shiny,
            mutation_type=mutation_type,
            special_effect=special_effect,
        )
        
        db.add(pet)
        await db.commit()
        await db.refresh(pet)
        
        return pet
    
    @staticmethod
    async def get_pet(db: AsyncSession, user_id: str) -> Pet | None:
        """Get user's pet"""
        result = await db.execute(
            select(Pet).where(Pet.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def feed_pet(db: AsyncSession, user_id: str, xp_amount: int = 10) -> dict:
        """Feed pet (increase happiness and XP)"""
        pet = await PetService.get_pet(db, user_id)
        if not pet:
            raise ValueError("Pet not found")
        
        # Update stats
        pet.happiness = min(100, pet.happiness + 10)
        pet.xp += xp_amount
        pet.last_fed = datetime.now()
        
        # Check for level ups
        level_ups = 0
        evolved = False
        
        while pet.xp >= pet.xp_for_next_level:
            pet.xp -= pet.xp_for_next_level
            pet.level += 1
            level_ups += 1
            
            # Check evolution
            if pet.can_evolve():
                evolved = pet.evolve()
        
        await db.commit()
        await db.refresh(pet)
        
        return {
            "pet": pet,
            "level_ups": level_ups,
            "evolved": evolved,
            "message": PetService.get_action_message(level_ups, evolved, is_shiny=pet.is_shiny),
        }
    
    @staticmethod
    def get_action_message(level_ups: int, evolved: bool, is_shiny: bool = False) -> str:
        """Get appropriate message for action"""
        if evolved:
            if is_shiny:
                return "✨ Ваш сияющий питомец эволюционировал! Потрясающе!"
            return "🎉 Питомец эволюционировал!"
        
        if level_ups > 0:
            if is_shiny:
                return f"✨ Ваш редкий питомец вырос на {level_ups} уровень!"
            return f"🎊 Питомец вырос на {level_ups} уровень!"
        
        return "😊 Питомец доволен!"
    
    @staticmethod
    async def get_available_types() -> list[dict]:
        """Get all available pet types with descriptions"""
        return [
            {
                "type": PetType.BIRD.value,
                "name": "Птица",
                "emoji": "🐦",
                "description": "Свободная и певучая",
                "rarity": "common"
            },
            {
                "type": PetType.CAT.value,
                "name": "Кот",
                "emoji": "🐱",
                "description": "Независимый и игривый",
                "rarity": "common"
            },
            {
                "type": PetType.DRAGON.value,
                "name": "Дракон",
                "emoji": "🐉",
                "description": "Могущественный и мудрый",
                "rarity": "rare"
            },
            {
                "type": PetType.FOX.value,
                "name": "Лиса",
                "emoji": "🦊",
                "description": "Хитрая и умная",
                "rarity": "common"
            },
            {
                "type": PetType.PANDA.value,
                "name": "Панда",
                "emoji": "🐼",
                "description": "Милая и спокойная",
                "rarity": "rare"
            },
            {
                "type": PetType.UNICORN.value,
                "name": "Единорог",
                "emoji": "🦄",
                "description": "Магический и редкий",
                "rarity": "epic"
            },
            {
                "type": PetType.RABBIT.value,
                "name": "Кролик",
                "emoji": "🐰",
                "description": "Быстрый и энергичный",
                "rarity": "common"
            },
            {
                "type": PetType.OWL.value,
                "name": "Сова",
                "emoji": "🦉",
                "description": "Мудрая и ночная",
                "rarity": "rare"
            },
        ]
