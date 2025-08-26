from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.session import Base


class CommentVisibility(str, Enum):
    # Reserved for future moderation/visibility controls
    VISIBLE = "visible"
    HIDDEN = "hidden"


class Comment(Base):
    """Comment entity associated with a task within a project."""
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)

    body: Mapped[str] = mapped_column(String(4096), nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default=CommentVisibility.VISIBLE.value)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    # Lightweight relations for potential future eager loading
    task = relationship("Task")
