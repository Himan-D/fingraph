import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from config import settings


async def init_db():
    """Initialize database tables"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Import all models to register them
        from db.postgres_models import (
            Company,
            StockQuote,
            Fundamental,
            Shareholding,
            CorporateAction,
            Deal,
            MFHolding,
            NewsArticle,
            Watchlist,
        )

        # Create all tables
        from db.postgres import Base

        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
