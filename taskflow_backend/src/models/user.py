from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """SQLAlchemy User model with unique email and role."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=UserRole.USER.value, server_default=text("'user'"))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("1"))

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
