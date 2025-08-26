"""Database models import hub.

Import models here to ensure they are registered with SQLAlchemy metadata for migrations and table creation.
"""
from src.models.user import User  # noqa: F401
# from src.models.project import Project  # noqa: F401
# from src.models.task import Task  # noqa: F401
