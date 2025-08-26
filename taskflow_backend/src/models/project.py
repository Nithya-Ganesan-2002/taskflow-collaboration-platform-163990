from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import String, ForeignKey, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.task import Task  # for type checking only

from src.db.session import Base


class ProjectVisibility(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class Project(Base):
    """Project model representing a team/collaboration space owned by a user."""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Ownership
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Visibility scope (future use)
    visibility: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProjectVisibility.PRIVATE.value,
        server_default=text("'private'")
    )

    is_archived: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProjectMemberRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectMember(Base):
    """Association table between users and projects with role in project."""
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProjectMemberRole.MEMBER.value,
        server_default=text("'member'")
    )

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="members")
