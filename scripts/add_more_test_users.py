"""Script to add more test users to the database"""
import sys
import os
from pathlib import Path
import uuid

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Test users to add
TEST_USERS = [
    {
        "username": "anna_test",
        "first_name": "Анна",
        "last_name": "Иванова",
        "email": "anna.ivanova@memoir.app",
        "phone": "+77771234568"
    },
    {
        "username": "dmitry_test",
        "first_name": "Дмитрий",
        "last_name": "Смирнов",
        "email": "dmitry.smirnov@memoir.app",
        "phone": "+77771234569"
    },
    {
        "username": "maria_test",
        "first_name": "Мария",
        "last_name": "Петрова",
        "email": "maria.petrova@memoir.app",
        "phone": "+77771234570"
    }
]

def add_test_users():
    """Add multiple test users to the database"""
    
    # Create synchronous engine
    engine = create_engine(
        settings.DATABASE_URL.replace("+asyncpg", ""),
        poolclass=NullPool,
        echo=False
    )
    
    added_count = 0
    existing_count = 0
    
    try:
        for user_data in TEST_USERS:
            with engine.begin() as conn:
                # Check if user already exists
                result = conn.execute(text("""
                    SELECT id, first_name, last_name
                    FROM users 
                    WHERE username = :username OR email = :email
                """), {
                    "username": user_data["username"],
                    "email": user_data["email"]
                })
                
                existing_user = result.fetchone()
                
                if existing_user:
                    print(f"⏭️  User '{user_data['username']}' already exists: {existing_user[1]} {existing_user[2]}")
                    existing_count += 1
                    continue
                
                # Create test user
                user_id = str(uuid.uuid4())
                conn.execute(text("""
                    INSERT INTO users (
                        id, phone_number, email, username, 
                        first_name, last_name, 
                        created_at, updated_at,
                        task_reminders_enabled, reminder_hours_before
                    )
                    VALUES (
                        :id, :phone, :email, :username,
                        :first_name, :last_name,
                        NOW(), NOW(),
                        true, 1
                    )
                """), {
                    "id": user_id,
                    "phone": user_data["phone"],
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"]
                })
                
                print(f"✅ Created user: {user_data['first_name']} {user_data['last_name']} (@{user_data['username']})")
                added_count += 1
        
        print(f"\n📊 Summary:")
        print(f"  - New users added: {added_count}")
        print(f"  - Already existed: {existing_count}")
        print(f"\n💡 You can search for these users by their first or last names!")
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_users()
