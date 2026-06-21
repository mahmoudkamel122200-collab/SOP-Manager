"""
Alembic migration environment — async SQLAlchemy configuration.

How to use:
    cd backend/

    # Create initial migration (auto-detect from models)
    alembic revision --autogenerate -m "initial_schema"

    # Apply migrations
    alembic upgrade head

    # Downgrade one step
    alembic downgrade -1
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Import ALL models so Alembic sees every table ──────────────────────────
# This single import pulls in Base + all model classes via __init__.py
from app.models import Base  # noqa: F401

from app.core.config import settings

# ── Alembic config object ──────────────────────────────────────────────────
config = context.config

# Override URL from pydantic settings (ignores alembic.ini value)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Offline mode (generates SQL without connecting) ───────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,              # detect column type changes
        compare_server_default=True,    # detect server default changes
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connects to DB) ──────────────────────────────────────────
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"prepared_statement_cache_size": 0},
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
