from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.postgres import get_db
from db.postgres_models import NewsArticle

router = APIRouter()


@router.get("")
async def get_news(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get latest market news from database"""
    result = await db.execute(
        select(NewsArticle).order_by(desc(NewsArticle.published_at)).limit(limit)
    )
    news_items = result.scalars().all()

    news = [
        {
            "id": item.id,
            "headline": item.headline,
            "summary": getattr(item, "summary", ""),
            "source": item.source,
            "url": getattr(item, "url", None)
            or f"https://www.google.com/search?q={item.headline.replace(' ', '+')}",
            "category": item.sentiment,
            "timestamp": item.published_at.isoformat() if item.published_at else None,
        }
        for item in news_items
    ]

    return {"success": True, "data": news}


@router.get("/categories/{category}")
async def get_news_by_category(
    category: str, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """Get news by category"""
    result = await db.execute(
        select(NewsArticle)
        .where(NewsArticle.sentiment == category)
        .order_by(desc(NewsArticle.published_at))
        .limit(limit)
    )
    news_items = result.scalars().all()

    news = [
        {
            "id": item.id,
            "headline": item.headline,
            "summary": getattr(item, "summary", ""),
            "source": item.source,
            "url": getattr(item, "url", None)
            or f"https://www.google.com/search?q={item.headline.replace(' ', '+')}",
            "category": item.sentiment,
            "timestamp": item.published_at.isoformat() if item.published_at else None,
        }
        for item in news_items
    ]

    return {"success": True, "data": news}
