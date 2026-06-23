"""
Alembic Environment Configuration
"""

from logging.config import fileConfig
import asyncio
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine

from alembic import context

from app.core.base import Base
from app.models import *  # noqa
from app.core.config_simple import settings

# this is the Alembic Config object
config = context.config

# Note: config is already loaded by Alembic, no need to reload it

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set sqlalchemy.url from settings (sync URL for Alembic)
# SECURITY: Strip async driver suffixes (+asyncpg, +aiosqlite) so the
# sync create_engine below can connect.  Without this, Alembic crashes
# with NoSuchModuleError on any PostgreSQL deployment URL.
sync_db_url = settings.DATABASE_URL
for _async_suffix in ("+asyncpg", "+aiosqlite", "+aiomysql"):
    if _async_suffix in sync_db_url:
        sync_db_url = sync_db_url.replace(_async_suffix, "")
        break
# Railway uses postgres://; SQLAlchemy needs postgresql://
if sync_db_url.startswith("postgres://"):
    sync_db_url = sync_db_url.replace("postgres://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", sync_db_url)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()



def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()



def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Get database URL
    url = config.get_main_option("sqlalchemy.url")
    
    # Configure connect_args based on database type
    connect_args = {}
    if "postgresql" in url:
        connect_args = {
            "connect_timeout": 10,
            "options": "-c statement_timeout=300000"  # 5 minutes in milliseconds
        }
    # SQLite doesn't support these parameters, so leave connect_args empty
    
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        connect_args=connect_args
    )
    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
