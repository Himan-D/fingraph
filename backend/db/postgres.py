from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            from db.postgres_models import (
                Company,
                StockQuote,
                Fundamental,
                Shareholding,
            )
            from db.postgres import Base

            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database init: {e}")


async def get_db():
    """Read-write session — caller is responsible for adding/flushing objects.
    The session auto-commits only when the route actually modified state
    (i.e. session.in_transaction() is True after the route returns)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Only commit if the route dirtied the session
            if session.in_transaction():
                await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Close database connections"""
    await engine.dispose()
