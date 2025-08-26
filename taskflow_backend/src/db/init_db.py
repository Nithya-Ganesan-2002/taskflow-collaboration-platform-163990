import logging

from sqlalchemy.ext.asyncio import AsyncEngine

from src.db.session import Base

logger = logging.getLogger(__name__)


# PUBLIC_INTERFACE
async def init_db(engine: AsyncEngine) -> None:
    """Initialize the database schema (create tables if they don't exist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ensured.")
