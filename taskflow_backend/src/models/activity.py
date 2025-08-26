from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.session import Base


class ActivityScope(str, Enum):
    PROJECT = "project"
    TASK = "task"


class ActivityType(str, Enum):
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_MEMBER_ADDED = "project_member_added"
    PROJECT_MEMBER_REMOVED = "project_member_removed"

    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_ASSIGNEE_CHANGED = "task_assignee_changed"
    TASK_DELETED = "task_deleted"

    COMMENT_ADDED = "comment_added"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"


class Activity(Base):
    """Activity feed event across projects/tasks for auditing and notifications."""
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    # Optional task id when scope is task
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)

    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)

    scope: Mapped[str] = mapped_column(String(32), nullable=False, default=ActivityScope.PROJECT.value)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(String(1024), nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    # Relations for possible joins
    task = relationship("Task")
