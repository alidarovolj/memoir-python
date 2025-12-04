"""Database initialization and seeding"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.core.security import get_password_hash


async def init_categories(db: AsyncSession) -> None:
    """Initialize default categories"""
    categories = [
        {
            "name": "movies",
            "display_name": "Movies & TV",
            "icon": "movie",
            "color": "#E50914"
        },
        {
            "name": "books",
            "display_name": "Books & Articles",
            "icon": "book",
            "color": "#4285F4"
        },
        {
            "name": "places",
            "display_name": "Places",
            "icon": "location_on",
            "color": "#34A853"
        },
        {
            "name": "ideas",
            "display_name": "Ideas & Insights",
            "icon": "lightbulb",
            "color": "#FBBC04"
        },
        {
            "name": "recipes",
            "display_name": "Recipes",
            "icon": "restaurant",
            "color": "#FF6D00"
        },
        {
            "name": "products",
            "display_name": "Products & Wishlist",
            "icon": "shopping_bag",
            "color": "#9C27B0"
        },
    ]
    
    for cat_data in categories:
        category = Category(**cat_data)
        db.add(category)
    
    await db.commit()


async def init_db(db: AsyncSession) -> None:
    """Initialize database with default data"""
    # Check if categories already exist
    result = await db.execute("SELECT COUNT(*) FROM categories")
    count = result.scalar()
    
    if count == 0:
        await init_categories(db)
        print("✅ Database initialized with default categories")
    else:
        print("✅ Database already initialized")

