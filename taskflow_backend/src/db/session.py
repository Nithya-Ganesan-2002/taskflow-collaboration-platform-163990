from collections.abc import AsyncGenerator
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""
    pass


_engine = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _build_engine():
    """Build async engine based on settings.DATABASE_URL."""
    settings = get_settings()
    database_url = settings.DATABASE_URL

    # If user provided a non-async URL by mistake for sqlite, try to adapt
    if database_url.startswith("sqlite:///"):
        # enforce async driver
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        future=True,
    )
    logger.info("Initialized async DB engine for URL: %s", database_url.split("@")[-1])
    return engine


def get_engine():
    """Singleton engine getter."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_session_factory():
    """Singleton sessionmaker getter."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


# PUBLIC_INTERFACE
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            # session closed by context manager
            ...
