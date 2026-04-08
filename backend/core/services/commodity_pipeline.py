import asyncio
import logging
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import AsyncSessionLocal
from db.postgres_models import (
    Commodity,
    CommodityPrice,
    CommodityNews,
    CommoditySentiment,
    TwitterPost,
    RedditPost,
)

logger = logging.getLogger(__name__)

COMMODITIES = [
    {
        "symbol": "GOLD",
        "name": "Gold",
        "exchange": "MCX",
        "category": "precious",
        "unit": "10 gm",
    },
    {
        "symbol": "SILVER",
        "name": "Silver",
        "exchange": "MCX",
        "category": "precious",
        "unit": "1 kg",
    },
    {
        "symbol": "CRUDEOIL",
        "name": "Crude Oil",
        "exchange": "MCX",
        "category": "energy",
        "unit": "100 bbl",
    },
    {
        "symbol": "NATURALGAS",
        "name": "Natural Gas",
        "exchange": "MCX",
        "category": "energy",
        "unit": "MMBtu",
    },
    {
        "symbol": "COPPER",
        "name": "Copper",
        "exchange": "MCX",
        "category": "base",
        "unit": "1 kg",
    },
    {
        "symbol": "NICKEL",
        "name": "Nickel",
        "exchange": "MCX",
        "category": "base",
        "unit": "1 kg",
    },
    {
        "symbol": "ZINC",
        "name": "Zinc",
        "exchange": "MCX",
        "category": "base",
        "unit": "1 kg",
    },
    {
        "symbol": "LEAD",
        "name": "Lead",
        "exchange": "MCX",
        "category": "base",
        "unit": "1 kg",
    },
    {
        "symbol": "ALUMINIUM",
        "name": "Aluminium",
        "exchange": "MCX",
        "category": "base",
        "unit": "1 kg",
    },
]


async def initialize_commodities():
    """Initialize commodity master data"""
    async with AsyncSessionLocal() as session:
        for comm in COMMODITIES:
            existing = await session.execute(
                select(Commodity).where(Commodity.symbol == comm["symbol"])
            )
            if not existing.scalar_one_or_none():
                commodity = Commodity(**comm)
                session.add(commodity)

        await session.commit()
    logger.info("Commodities initialized")


async def store_commodity_prices(prices: List[Dict]) -> int:
    """Store commodity prices to database"""
    stored = 0

    async with AsyncSessionLocal() as session:
        for price in prices:
            symbol = price.get("symbol", "")
            if not symbol:
                continue

            result = await session.execute(
                select(Commodity).where(Commodity.symbol == symbol)
            )
            commodity = result.scalar_one_or_none()

            if commodity:
                price_record = CommodityPrice(
                    commodity_id=commodity.id,
                    timestamp=datetime.now(),
                    open=price.get("open"),
                    high=price.get("high"),
                    low=price.get("low"),
                    close=price.get("close"),
                    settlement=price.get("settlement"),
                    previous_close=price.get("previous_close"),
                    change=price.get("change"),
                    change_pct=price.get("change_pct"),
                    volume=price.get("volume"),
                    open_interest=price.get("open_interest"),
                    delivery=price.get("delivery"),
                    turnover=price.get("turnover"),
                )
                session.add(price_record)
                stored += 1

        await session.commit()

    logger.info(f"Stored {stored} commodity prices")
    return stored


async def store_commodity_news(news_items: List[Dict]) -> int:
    """Store commodity news to database"""
    stored = 0

    async with AsyncSessionLocal() as session:
        for news in news_items:
            news_record = CommodityNews(
                headline=news.get("headline", ""),
                summary=news.get("summary", ""),
                source=news.get("source", ""),
                url=news.get("url", ""),
                commodities=news.get("commodities", []),
                published_at=datetime.now(),
                sentiment=news.get("sentiment", "neutral"),
                tags=news.get("tags", []),
            )
            session.add(news_record)
            stored += 1

        await session.commit()

    logger.info(f"Stored {stored} commodity news")
    return stored


async def calculate_commodity_sentiment(commodity: str, source: str = "reddit") -> Dict:
    """Calculate sentiment for a commodity from social data"""
    async with AsyncSessionLocal() as session:
        from datetime import timedelta

        query = select(RedditPost).where(
            RedditPost.created_at >= datetime.now() - timedelta(days=7)
        )

        result = await session.execute(query)
        posts = result.scalars().all()

        commodity_posts = [p for p in posts if commodity.upper() in (p.symbols or [])]

        if not posts:
            return {"sentiment_score": 0, "mention_count": 0}

        bullish_keywords = [
            "bullish",
            "buy",
            "long",
            "moon",
            "gain",
            "profit",
            "up",
            "call",
            "beat",
            "higher",
            "rise",
            "rally",
        ]
        bearish_keywords = [
            "bearish",
            "sell",
            "short",
            "dump",
            "loss",
            "down",
            "put",
            "miss",
            "lower",
            "fall",
            "decline",
        ]

        bullish = 0
        bearish = 0

        for post in commodity_posts:
            text = (post.title or "" + " " + post.text or "").lower()

            for kw in bullish_keywords:
                if kw in text:
                    bullish += 1
                    break
            for kw in bearish_keywords:
                if kw in text:
                    bearish += 1
                    break

        total = len(commodity_posts)
        sentiment_score = (bullish - bearish) / max(total, 1) * 100

        return {
            "sentiment_score": round(sentiment_score, 2),
            "mention_count": total,
            "bullish_count": bullish,
            "bearish_count": bearish,
        }


async def store_commodity_sentiment(
    commodity: str, source: str, sentiment: Dict
) -> int:
    """Store calculated sentiment"""
    async with AsyncSessionLocal() as session:
        record = CommoditySentiment(
            commodity_symbol=commodity,
            date=date.today(),
            source=source,
            sentiment_score=sentiment.get("sentiment_score", 0),
            mention_count=sentiment.get("mention_count", 0),
            bullish_count=sentiment.get("bullish_count", 0),
            bearish_count=sentiment.get("bearish_count", 0),
        )
        session.add(record)
        await session.commit()

    return 1


async def get_commodity_prices(symbol: str, days: int = 7) -> List[Dict]:
    """Get historical prices for a commodity"""
    from datetime import timedelta

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Commodity).where(Commodity.symbol == symbol.upper())
        )
        commodity = result.scalar_one_or_none()

        if not commodity:
            return []

        query = (
            select(CommodityPrice)
            .where(
                CommodityPrice.commodity_id == commodity.id,
                CommodityPrice.timestamp >= datetime.now() - timedelta(days=days),
            )
            .order_by(CommodityPrice.timestamp.desc())
        )

        result = await session.execute(query)
        prices = result.scalars().all()

        return [
            {
                "timestamp": p.timestamp.isoformat(),
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "change": p.change,
                "change_pct": p.change_pct,
                "volume": p.volume,
                "open_interest": p.open_interest,
            }
            for p in prices
        ]


async def get_commodity_news(symbol: str = None, limit: int = 50) -> List[Dict]:
    """Get commodity news"""
    async with AsyncSessionLocal() as session:
        query = select(CommodityNews).order_by(CommodityNews.published_at.desc())

        if symbol:
            query = query.where(
                CommodityNews.commodities.cast(String).like(f"%{symbol.upper()}%")
            )

        query = query.limit(limit)

        result = await session.execute(query)
        news = result.scalars().all()

        return [
            {
                "id": n.id,
                "headline": n.headline,
                "summary": n.summary,
                "source": n.source,
                "url": n.url,
                "commodities": n.commodities,
                "published_at": n.published_at.isoformat() if n.published_at else None,
                "sentiment": n.sentiment,
            }
            for n in news
        ]


async def get_sentiment_history(commodity: str, days: int = 30) -> List[Dict]:
    """Get sentiment history"""
    from datetime import timedelta

    async with AsyncSessionLocal() as session:
        query = (
            select(CommoditySentiment)
            .where(
                CommoditySentiment.commodity_symbol == commodity.upper(),
                CommoditySentiment.date >= date.today() - timedelta(days=days),
            )
            .order_by(CommoditySentiment.date.desc())
        )

        result = await session.execute(query)
        records = result.scalars().all()

        return [
            {
                "date": r.date.isoformat(),
                "source": r.source,
                "sentiment_score": r.sentiment_score,
                "mention_count": r.mention_count,
                "bullish_count": r.bullish_count,
                "bearish_count": r.bearish_count,
            }
            for r in records
        ]


async def run_pipeline():
    """Run complete commodity data pipeline"""
    logger.info("Starting commodity pipeline...")

    from core.scraper.commodity_scraper import scrape_all_commodities
    from core.scraper.commodity_news_scraper import scrape_commodity_news
    from core.scraper.commodity_social_scraper import (
        scrape_commodity_social,
        get_commodity_sentiment,
    )

    await initialize_commodities()

    prices = await scrape_all_commodities()
    await store_commodity_prices(prices)

    news = await scrape_commodity_news()
    await store_commodity_news(news)

    social_data = await scrape_commodity_social()

    for commodity in ["GOLD", "SILVER", "CRUDEOIL", "NATURALGAS"]:
        sentiment = await get_commodity_sentiment(commodity)
        if sentiment.get("mention_count", 0) > 0:
            await store_commodity_sentiment(commodity, "reddit", sentiment)

    logger.info("Commodity pipeline complete")


async def get_latest_prices() -> Dict:
    """Get latest prices for all commodities"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CommodityPrice).order_by(CommodityPrice.timestamp.desc()).limit(50)
        )
        prices = result.scalars().all()

        latest = {}
        for p in prices:
            comm_result = await session.execute(
                select(Commodity).where(Commodity.id == p.commodity_id)
            )
            comm = comm_result.scalar_one_or_none()
            if comm and comm.symbol not in latest:
                latest[comm.symbol] = {
                    "symbol": comm.symbol,
                    "name": comm.name,
                    "close": p.close,
                    "change": p.change,
                    "change_pct": p.change_pct,
                    "high": p.high,
                    "low": p.low,
                    "volume": p.volume,
                    "timestamp": p.timestamp.isoformat(),
                }

        return latest


async def get_commodity_summary() -> Dict:
    """Get commodity market summary"""
    prices = await get_latest_prices()

    sentiment_summary = {}
    for symbol in ["GOLD", "SILVER", "CRUDEOIL"]:
        sentiment = await calculate_commodity_sentiment(symbol)
        sentiment_summary[symbol] = sentiment

    return {
        "prices": prices,
        "sentiment": sentiment_summary,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    asyncio.run(run_pipeline())
