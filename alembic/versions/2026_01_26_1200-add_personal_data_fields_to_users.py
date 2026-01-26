"""add personal data fields to users

Revision ID: add_personal_data
Revises: a2b3c4d5e6f7
Create Date: 2026-01-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_personal_data'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('profession', sa.String(200), nullable=True))
    op.add_column('users', sa.Column('telegram_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('whatsapp_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('youtube_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('about_me', sa.String(2000), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('education', sa.String(200), nullable=True))
    op.add_column('users', sa.Column('hobbies', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'hobbies')
    op.drop_column('users', 'education')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'city')
    op.drop_column('users', 'about_me')
    op.drop_column('users', 'youtube_url')
    op.drop_column('users', 'whatsapp_url')
    op.drop_column('users', 'telegram_url')
    op.drop_column('users', 'profession')
