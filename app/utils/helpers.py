"""Helper utility functions"""
import uuid
from datetime import datetime
from typing import Optional


def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string"""
    if dt is None:
        return None
    return dt.isoformat()

