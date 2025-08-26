"""Database models import hub.

Import models here to ensure they are registered with SQLAlchemy metadata for migrations and table creation.
"""
from src.models.user import User  # noqa: F401
from src.models.project import Project, ProjectMember  # noqa: F401
from src.models.task import Task  # noqa: F401
from src.models.comment import Comment  # noqa: F401
from src.models.activity import Activity  # noqa: F401
