"""add phone auth to users

Revision ID: f9e8d7c6b5a4
Revises: b48580d17ab5
Create Date: 2025-12-04 14:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9e8d7c6b5a4'
down_revision = 'b48580d17ab5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('firebase_uid', sa.String(length=128), nullable=True))
    
    # Create indexes
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=True)
    op.create_index(op.f('ix_users_firebase_uid'), 'users', ['firebase_uid'], unique=True)
    
    # Make email and hashed_password nullable (for phone-only users)
    op.alter_column('users', 'email', existing_type=sa.String(length=255), nullable=True)
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=255), nullable=True)
    op.alter_column('users', 'username', existing_type=sa.String(length=100), nullable=True)


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f('ix_users_firebase_uid'), table_name='users')
    op.drop_index(op.f('ix_users_phone_number'), table_name='users')
    
    # Remove columns
    op.drop_column('users', 'firebase_uid')
    op.drop_column('users', 'phone_number')
    
    # Revert nullable changes
    op.alter_column('users', 'username', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=255), nullable=False)
    op.alter_column('users', 'email', existing_type=sa.String(length=255), nullable=False)

