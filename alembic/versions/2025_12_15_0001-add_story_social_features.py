"""add_story_social_features

Revision ID: add_story_social_features
Revises: 92697bd0e411
Create Date: 2025-12-15 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_story_social_features'
down_revision = '92697bd0e411'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем таблицу для лайков историй
    op.create_table('story_likes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('story_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('story_id', 'user_id', name='uq_story_like_user')
    )
    op.create_index('ix_story_likes_story_id', 'story_likes', ['story_id'])
    op.create_index('ix_story_likes_user_id', 'story_likes', ['user_id'])
    
    # Создаем таблицу для комментариев к историям
    op.create_table('story_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('story_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_story_comments_story_id', 'story_comments', ['story_id'])
    op.create_index('ix_story_comments_created_at', 'story_comments', ['created_at'])
    
    # Создаем таблицу для отправки историй другим пользователям
    op.create_table('story_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('story_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_story_shares_story_id', 'story_shares', ['story_id'])
    op.create_index('ix_story_shares_recipient_id', 'story_shares', ['recipient_id'])
    
    # Добавляем поле для репостов в таблицу stories
    op.add_column('stories', sa.Column('original_story_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_stories_original_story_id', 'stories', 'stories', ['original_story_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_stories_original_story_id', 'stories', ['original_story_id'])


def downgrade() -> None:
    # Удаляем индексы и поле для репостов
    op.drop_index('ix_stories_original_story_id', table_name='stories')
    op.drop_constraint('fk_stories_original_story_id', 'stories', type_='foreignkey')
    op.drop_column('stories', 'original_story_id')
    
    # Удаляем таблицу story_shares
    op.drop_index('ix_story_shares_recipient_id', table_name='story_shares')
    op.drop_index('ix_story_shares_story_id', table_name='story_shares')
    op.drop_table('story_shares')
    
    # Удаляем таблицу story_comments
    op.drop_index('ix_story_comments_created_at', table_name='story_comments')
    op.drop_index('ix_story_comments_story_id', table_name='story_comments')
    op.drop_table('story_comments')
    
    # Удаляем таблицу story_likes
    op.drop_index('ix_story_likes_user_id', table_name='story_likes')
    op.drop_index('ix_story_likes_story_id', table_name='story_likes')
    op.drop_table('story_likes')
