"""
Factory Management System — SQLAlchemy Async Database Session
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,        # validate connections before checkout
    pool_size=10,
    max_overflow=20,
    connect_args={"prepared_statement_cache_size": 0}, # Required for PgBouncer / Supabase Pooler
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # prevent lazy-load errors post-commit
)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
