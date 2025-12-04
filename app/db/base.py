"""SQLAlchemy Base for models"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here for Alembic - but only if we're running alembic
# This avoids circular imports during normal app runtime
def import_models():
    """Import all models - call this only from alembic env.py"""
    from app.models.user import User  # noqa
    from app.models.category import Category  # noqa
    from app.models.memory import Memory  # noqa
    from app.models.embedding import Embedding  # noqa
    from app.models.story import Story  # noqa
    from app.models.task import Task  # noqa

