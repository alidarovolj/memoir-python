"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-02 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('icon', sa.String(100), nullable=False),
        sa.Column('color', sa.String(7), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_categories_name', 'categories', ['name'], unique=True)
    
    # Create memories table
    op.create_table(
        'memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_type', sa.Enum('text', 'link', 'image', 'voice', name='sourcetype'), nullable=False),
        sa.Column('source_url', sa.String(2048), nullable=True),
        sa.Column('memory_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
    )
    op.create_index('ix_memories_user_id', 'memories', ['user_id'])
    op.create_index('ix_memories_category_id', 'memories', ['category_id'])
    op.create_index('ix_memories_created_at', 'memories', ['created_at'], postgresql_using='btree')
    
    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_embeddings_memory_id', 'embeddings', ['memory_id'], unique=True)
    
    # Create vector index for semantic search
    op.execute("""
        CREATE INDEX ix_embeddings_vector ON embeddings 
        USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100)
    """)
    
    # Insert default categories
    op.execute("""
        INSERT INTO categories (id, name, display_name, icon, color, created_at) VALUES
        (gen_random_uuid(), 'movies', 'Movies & TV', 'movie', '#E50914', NOW()),
        (gen_random_uuid(), 'books', 'Books & Articles', 'book', '#4285F4', NOW()),
        (gen_random_uuid(), 'places', 'Places', 'location_on', '#34A853', NOW()),
        (gen_random_uuid(), 'ideas', 'Ideas & Insights', 'lightbulb', '#FBBC04', NOW()),
        (gen_random_uuid(), 'recipes', 'Recipes', 'restaurant', '#FF6D00', NOW()),
        (gen_random_uuid(), 'products', 'Products & Wishlist', 'shopping_bag', '#9C27B0', NOW())
    """)


def downgrade() -> None:
    op.drop_table('embeddings')
    op.drop_table('memories')
    op.drop_table('categories')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS vector')
    op.execute('DROP TYPE IF EXISTS sourcetype')

