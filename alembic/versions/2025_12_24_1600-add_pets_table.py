"""add pets table for virtual companion

Revision ID: add_pets_table
Revises: add_story_social_features
Create Date: 2025-12-24 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_pets_table'
down_revision = 'add_story_social_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pet_type enum
    pet_type_enum = postgresql.ENUM('bird', 'cat', 'dragon', name='pettype', create_type=False)
    pet_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create evolution_stage enum
    evolution_stage_enum = postgresql.ENUM('egg', 'baby', 'adult', 'legend', name='evolutionstage', create_type=False)
    evolution_stage_enum.create(op.get_bind(), checkfirst=True)
    
    # Create pets table
    op.create_table('pets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pet_type', pet_type_enum, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('evolution_stage', evolution_stage_enum, nullable=False, server_default='egg'),
        sa.Column('happiness', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('health', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('last_fed', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_played', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accessories', sa.String(length=500), server_default='{}'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_pet')
    )
    op.create_index('ix_pets_user_id', 'pets', ['user_id'])
    op.create_index('ix_pets_level', 'pets', ['level'])
    op.create_index('ix_pets_evolution_stage', 'pets', ['evolution_stage'])


def downgrade() -> None:
    op.drop_index('ix_pets_evolution_stage', table_name='pets')
    op.drop_index('ix_pets_level', table_name='pets')
    op.drop_index('ix_pets_user_id', table_name='pets')
    op.drop_table('pets')
    
    # Drop enums
    postgresql.ENUM(name='evolutionstage').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='pettype').drop(op.get_bind(), checkfirst=True)
