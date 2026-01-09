"""Seed pet shop items"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.pet_shop_service import PetShopService
# Import all models
from app.models import *  # noqa


async def seed_items():
    """Seed default pet shop items"""
    async with AsyncSessionLocal() as db:
        print("🛍️ Seeding pet shop items...")
        await PetShopService.seed_default_items(db)
        print("✅ Pet shop items seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_items())
