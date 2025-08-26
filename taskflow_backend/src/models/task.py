from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import String, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.project import Project  # for type checking only

from src.db.session import Base


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(Base):
    """Task entity that belongs to a Project, optionally assigned to a user."""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TaskStatus.TODO.value,
        server_default=text("'todo'")
    )
    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TaskPriority.MEDIUM.value,
        server_default=text("'medium'")
    )

    # Assignment
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    due_date: Mapped[datetime | None] = mapped_column(nullable=True)

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    is_archived: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tasks")
