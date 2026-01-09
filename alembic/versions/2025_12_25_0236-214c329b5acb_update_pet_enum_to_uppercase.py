"""update pet enum to uppercase

Revision ID: 214c329b5acb
Revises: add_pets_table
Create Date: 2025-12-25 02:36:05.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '214c329b5acb'
down_revision = 'add_pets_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop pets table temporarily
    op.execute('DROP TABLE IF EXISTS pets CASCADE')
    
    # Drop old enums
    op.execute('DROP TYPE IF EXISTS pettype CASCADE')
    op.execute('DROP TYPE IF EXISTS evolutionstage CASCADE')
    
    # Create new enums with uppercase values
    op.execute("CREATE TYPE pettype AS ENUM ('BIRD', 'CAT', 'DRAGON')")
    op.execute("CREATE TYPE evolutionstage AS ENUM ('EGG', 'BABY', 'ADULT', 'LEGEND')")
    
    # Recreate pets table with new enums
    op.execute("""
        CREATE TABLE pets (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            pet_type pettype NOT NULL,
            name VARCHAR(50) NOT NULL,
            level INTEGER NOT NULL DEFAULT 1,
            xp INTEGER NOT NULL DEFAULT 0,
            evolution_stage evolutionstage NOT NULL DEFAULT 'EGG',
            happiness INTEGER NOT NULL DEFAULT 100,
            health INTEGER NOT NULL DEFAULT 100,
            last_fed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_played TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            accessories VARCHAR(500) DEFAULT '{}'
        )
    """)
    
    # Recreate indexes
    op.execute('CREATE INDEX ix_pets_user_id ON pets(user_id)')
    op.execute('CREATE INDEX ix_pets_level ON pets(level)')
    op.execute('CREATE INDEX ix_pets_evolution_stage ON pets(evolution_stage)')


def downgrade() -> None:
    # Drop pets table
    op.execute('DROP TABLE IF EXISTS pets CASCADE')
    
    # Drop uppercase enums
    op.execute('DROP TYPE IF EXISTS pettype CASCADE')
    op.execute('DROP TYPE IF EXISTS evolutionstage CASCADE')
    
    # Recreate lowercase enums
    op.execute("CREATE TYPE pettype AS ENUM ('bird', 'cat', 'dragon')")
    op.execute("CREATE TYPE evolutionstage AS ENUM ('egg', 'baby', 'adult', 'legend')")
    
    # Recreate pets table with old enums
    op.execute("""
        CREATE TABLE pets (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            pet_type pettype NOT NULL,
            name VARCHAR(50) NOT NULL,
            level INTEGER NOT NULL DEFAULT 1,
            xp INTEGER NOT NULL DEFAULT 0,
            evolution_stage evolutionstage NOT NULL DEFAULT 'egg',
            happiness INTEGER NOT NULL DEFAULT 100,
            health INTEGER NOT NULL DEFAULT 100,
            last_fed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_played TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            accessories VARCHAR(500) DEFAULT '{}'
        )
    """)
    
    # Recreate indexes
    op.execute('CREATE INDEX ix_pets_user_id ON pets(user_id)')
    op.execute('CREATE INDEX ix_pets_level ON pets(level)')
    op.execute('CREATE INDEX ix_pets_evolution_stage ON pets(evolution_stage)')
