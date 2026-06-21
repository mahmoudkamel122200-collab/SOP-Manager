"""
core/database.py

Async SQLAlchemy engine and session factory.
get_db() is the FastAPI dependency injected into every router that needs DB access.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,     # test connection before each checkout
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # prevent lazy-load errors after commit
    autoflush=False,
)


# ── FastAPI Dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    Yields an AsyncSession per request.
    - Commits on success
    - Rolls back on any exception
    - Always closes the session
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
