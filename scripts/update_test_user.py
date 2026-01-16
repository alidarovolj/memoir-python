"""Script to update the test user with first and last name"""
import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from app.core.config import settings

def update_test_user():
    """Update test user with first and last name"""
    
    # Create synchronous engine
    engine = create_engine(
        settings.DATABASE_URL.replace("+asyncpg", ""),
        poolclass=NullPool,
        echo=False
    )
    
    try:
        with engine.begin() as conn:
            # Update the existing testuser
            result = conn.execute(text("""
                UPDATE users
                SET first_name = :first_name,
                    last_name = :last_name,
                    email = :email,
                    phone_number = :phone,
                    updated_at = NOW()
                WHERE username = :username
                RETURNING id, first_name, last_name, email, phone_number, username
            """), {
                "username": "testuser",
                "first_name": "Тестовый",
                "last_name": "Пользователь",
                "email": "test.user@memoir.app",
                "phone": "+77771234567"
            })
            
            updated_user = result.fetchone()
            
            if updated_user:
                print("✅ Test user updated successfully!")
                print(f"  - Name: {updated_user[1]} {updated_user[2]}")
                print(f"  - Email: {updated_user[3]}")
                print(f"  - Phone: {updated_user[4]}")
                print(f"  - Username: {updated_user[5]}")
                print(f"  - ID: {updated_user[0]}")
                print(f"\n💡 You can now search for this user by:")
                print(f"  - First name: {updated_user[1]}")
                print(f"  - Last name: {updated_user[2]}")
                print(f"  - Full name: {updated_user[1]} {updated_user[2]}")
            else:
                print("❌ User 'testuser' not found")
        
    except Exception as e:
        print(f"❌ Error updating test user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_test_user()
