"""
Database Configuration
SQLAlchemy 2.0 async setup with PostgreSQL + sync fallback for Celery
"""

from contextlib import contextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.core.config_simple import settings
from app.core.base import Base

engine_url = settings.DATABASE_URL
if engine_url.startswith("postgresql://"):
    engine_url = engine_url.replace("postgresql://", "postgresql+asyncpg://")

engine_kwargs = {
    "echo": settings.DEBUG,
}

# PostgreSQL pool settings (pool_recycle and pool_timeout are PostgreSQL-only)
if engine_url.startswith("postgresql+"):
    engine_kwargs.update(
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_timeout=30,
        poolclass=NullPool if settings.DATABASE_POOL_SIZE == 0 else None,
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

# Sync engine + session for Celery background tasks
sync_engine_url = settings.DATABASE_URL
if sync_engine_url.startswith("postgresql+asyncpg://"):
    sync_engine_url = sync_engine_url.replace("postgresql+asyncpg://", "postgresql://")
if sync_engine_url.startswith("postgresql+psycopg2://"):
    sync_engine_url = sync_engine_url.replace("postgresql+psycopg2://", "postgresql://")

_sync_engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}
if sync_engine_url.startswith("postgresql://"):
    _sync_engine_kwargs.update(
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=3600,
        pool_timeout=30,
    )

try:
    sync_engine = create_engine(sync_engine_url, **_sync_engine_kwargs)
    SyncSessionLocal = sessionmaker(
        sync_engine,
        autocommit=False,
        autoflush=False,
    )
except Exception as e:
    # Fallback: if sync engine fails (e.g., no psycopg2 installed),
    # Celery tasks will need to use the async engine via event loop
    sync_engine = None
    SyncSessionLocal = None
    import warnings
    warnings.warn(f"Sync database engine unavailable: {e}. Celery background tasks requiring sync DB will fail. Install 'psycopg2-binary' for sync support.")

# Re-export Base for backward compatibility (models should import from app.core.base)
# CRIT-01 FIX: Removed duplicate `Base = declarative_base()` that created a separate
# metadata registry, causing table creation to fail in production.


async def get_db() -> AsyncSession:
    """
    Dependency to get async database session
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

@contextmanager
def get_sync_db() -> Session:
    """
    Get synchronous database session for Celery/background tasks.
    Usage: with get_sync_db() as db:
    Automatically commits on success, rolls back on error.
    """
    if SyncSessionLocal is None:
        raise RuntimeError("Sync database engine not available. Install psycopg2-binary.")
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()