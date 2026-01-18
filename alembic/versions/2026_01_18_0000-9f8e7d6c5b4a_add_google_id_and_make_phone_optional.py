"""add_google_id_and_make_phone_optional

Revision ID: 9f8e7d6c5b4a
Revises: 8b45c299cebc
Create Date: 2026-01-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f8e7d6c5b4a'
down_revision = '8b45c299cebc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add google_id column
    op.add_column('users', sa.Column('google_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)
    
    # Make phone_number nullable for Google auth users
    op.alter_column('users', 'phone_number',
                    existing_type=sa.String(length=20),
                    nullable=True)


def downgrade() -> None:
    # Revert phone_number to non-nullable
    op.alter_column('users', 'phone_number',
                    existing_type=sa.String(length=20),
                    nullable=False)
    
    # Remove google_id
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_column('users', 'google_id')
