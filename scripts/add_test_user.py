"""Script to add a test user to the database"""
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

def add_test_user():
    """Add a test user to the database"""
    
    # Create synchronous engine
    engine = create_engine(
        settings.DATABASE_URL.replace("+asyncpg", ""),
        poolclass=NullPool,
        echo=False
    )
    
    try:
        with engine.begin() as conn:
            # Check if user already exists by username or email
            result = conn.execute(text("""
                SELECT id, first_name, last_name, email, phone_number, username
                FROM users 
                WHERE email = :email OR username = :username OR phone_number = :phone
            """), {
                "email": "test.user@memoir.app",
                "username": "testuser",
                "phone": "+77771234567"
            })
            
            existing_user = result.fetchone()
            
            if existing_user:
                print(f"✅ Test user already exists:")
                print(f"  - Name: {existing_user[1]} {existing_user[2]}")
                print(f"  - Email: {existing_user[3]}")
                print(f"  - Phone: {existing_user[4]}")
                print(f"  - Username: {existing_user[5]}")
                print(f"  - ID: {existing_user[0]}")
                print(f"\n💡 You can search for this user by:")
                print(f"  - First name: {existing_user[1]}")
                print(f"  - Last name: {existing_user[2]}")
                print(f"  - Full name: {existing_user[1]} {existing_user[2]}")
                return
            
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
                "phone": "+77771234567",
                "email": "test.user@memoir.app",
                "username": "testuser",
                "first_name": "Тестовый",
                "last_name": "Пользователь"
            })
            
            print("✅ Test user created successfully!")
            print(f"  - Name: Тестовый Пользователь")
            print(f"  - Email: test.user@memoir.app")
            print(f"  - Phone: +77771234567")
            print(f"  - Username: testuser")
            print(f"  - ID: {user_id}")
            print(f"\n💡 You can now search for this user by:")
            print(f"  - First name: Тестовый")
            print(f"  - Last name: Пользователь")
            print(f"  - Full name: Тестовый Пользователь")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_user()
