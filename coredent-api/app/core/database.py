"""
Database Configuration
SQLAlchemy 2.0 async setup with PostgreSQL
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.base import Base

engine_url = settings.DATABASE_URL or ""
# CRIT-01 FIX: Railway uses postgres://, SQLAlchemy async requires postgresql+asyncpg://
if engine_url.startswith("postgres://"):
    engine_url = engine_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif engine_url.startswith("postgresql://"):
    engine_url = engine_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine_kwargs = {
    "echo": settings.DEBUG,
}

# PostgreSQL pool settings
if engine_url.startswith("postgresql+"):
    engine_kwargs.update(
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        poolclass=NullPool if settings.DEBUG else None,
    )

engine = create_async_engine(
    engine_url,
    **engine_kwargs,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency to get database session
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
