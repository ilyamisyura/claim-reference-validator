from logging.config import fileConfig
import asyncio

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

# from app.models import Base  # if you want autogenerate, set target_metadata = Base.metadata

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate target metadata (set to your models' Base.metadata if needed)
target_metadata = None  # e.g., Base.metadata


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Offline mode: URL only, no DBAPI needed."""
    url = getattr(settings, "DATABASE_URL", None) or config.get_main_option(
        "sqlalchemy.url"
    )
    if not url:
        raise RuntimeError(
            "No sqlalchemy.url provided. Set DATABASE_URL or configure alembic.ini."
        )
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = getattr(settings, "DATABASE_URL", None) or config.get_main_option(
        "sqlalchemy.url"
    )
    if not url:
        raise RuntimeError(
            "No sqlalchemy.url provided. Set DATABASE_URL or configure alembic.ini."
        )

    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
        future=True,
    )
    async with connectable.connect() as connection:
        # run the sync migration logic against the async connection
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Online mode: run the async path."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
