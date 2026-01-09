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
    from app.models.story_like import StoryLike  # noqa
    from app.models.story_comment import StoryComment  # noqa
    from app.models.story_share import StoryShare  # noqa
    from app.models.task import Task  # noqa
    from app.models.subtask import Subtask  # noqa
    from app.models.pet import Pet  # noqa
    from app.models.time_capsule import TimeCapsule  # noqa
    from app.models.daily_prompt import DailyPrompt  # noqa
    from app.models.challenge import GlobalChallenge, ChallengeParticipant  # noqa
    from app.models.achievement import Achievement, UserAchievement  # noqa

