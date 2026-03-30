from fastapi import APIRouter, Query
from typing import Optional, List
import asyncio

router = APIRouter()


@router.get("/search")
async def global_search(q: str = Query(..., min_length=1), limit: int = 20):
    """
    Global search across all entities: stocks, sectors, news, etc.
    Uses OpenSearch-like ranking with fuzzy matching
    """
    results = {
        "stocks": [],
        "sectors": [],
        "news": [],
    }

    try:
        # Search stocks from database
        stocks = await search_stocks(q, limit)
        results["stocks"] = stocks

        # Search sectors
        sectors = await search_sectors(q)
        results["sectors"] = sectors

        # Search news
        news = await search_news(q, limit)
        results["news"] = news

        return {"success": True, "data": results}
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def search_stocks(query: str, limit: int = 20) -> List[dict]:
    """Search stocks with fuzzy matching"""
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import Company, StockQuote
    from sqlalchemy import select, func, or_, desc

    query_upper = query.upper()
    query_lower = query.lower()

    async with AsyncSessionLocal() as session:
        # Get companies matching query
        result = await session.execute(
            select(
                Company.symbol,
                Company.name,
                Company.sector,
                Company.industry,
                func.max(StockQuote.close).label("price"),
            )
            .join(StockQuote, Company.id == StockQuote.company_id)
            .where(
                or_(
                    Company.symbol.ilike(f"%{query_upper}%"),
                    Company.name.ilike(f"%{query}%"),
                    Company.sector.ilike(f"%{query}%"),
                    Company.industry.ilike(f"%{query}%"),
                )
            )
            .group_by(Company.id)
            .order_by(desc(func.max(StockQuote.volume)))
            .limit(limit)
        )

        stocks = []
        for row in result:
            # Calculate relevance score
            score = 100
            if query_upper == row.symbol:
                score = 1000  # Exact match
            elif row.symbol.startswith(query_upper):
                score = 500  # Prefix match
            elif query_upper in row.symbol:
                score = 200  # Contains

            stocks.append(
                {
                    "symbol": row.symbol,
                    "name": row.name or row.symbol,
                    "sector": row.sector,
                    "industry": row.industry,
                    "price": float(row.price) if row.price else 0,
                    "type": "stock",
                    "score": score,
                    "id": row.symbol,
                }
            )

        # Sort by score
        stocks.sort(key=lambda x: x["score"], reverse=True)
        return stocks[:limit]


async def search_sectors(query: str) -> List[dict]:
    """Search sectors"""
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import Company
    from sqlalchemy import select, func

    sectors_data = {
        "Technology": {"icon": "💻", "description": "IT Services, Software, Hardware"},
        "Financial Services": {
            "icon": "🏦",
            "description": "Banking, Insurance, NBFCs",
        },
        "Energy": {"icon": "⚡", "description": "Oil & Gas, Power, Renewable Energy"},
        "Automobile": {"icon": "🚗", "description": "Cars, Trucks, Two Wheelers"},
        "Healthcare": {
            "icon": "🏥",
            "description": "Pharma, Hospitals, Medical Devices",
        },
        "FMCG": {"icon": "🛒", "description": "Consumer Goods, Personal Care"},
        "Metals": {"icon": "🥇", "description": "Steel, Aluminum, Mining"},
        "Construction": {"icon": "🏗️", "description": "Infrastructure, Real Estate"},
        "Telecommunication": {"icon": "📱", "description": "Telecom, Networking"},
        "Consumer Durables": {"icon": "🏠", "description": "Appliances, Electronics"},
    }

    query_lower = query.lower()
    results = []

    for sector, data in sectors_data.items():
        if query_lower in sector.lower():
            results.append(
                {
                    "name": sector,
                    "icon": data["icon"],
                    "description": data["description"],
                    "type": "sector",
                    "score": 100
                    if query_lower == sector.lower()[: len(query_lower)]
                    else 50,
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]


async def search_news(query: str, limit: int = 10) -> List[dict]:
    """Search news"""
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import NewsArticle
    from sqlalchemy import select, or_, desc

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(NewsArticle)
            .where(
                or_(
                    NewsArticle.headline.ilike(f"%{query}%"),
                    NewsArticle.summary.ilike(f"%{query}%"),
                    NewsArticle.source.ilike(f"%{query}%"),
                )
            )
            .order_by(desc(NewsArticle.published_at))
            .limit(limit)
        )

        articles = result.scalars().all()
        return [
            {
                "id": article.id,
                "headline": article.headline,
                "source": article.source,
                "url": article.url
                if article.url
                else f"https://www.google.com/search?q={article.headline[:50]}",
                "timestamp": article.published_at.isoformat()
                if article.published_at
                else None,
                "type": "news",
                "score": 100,
            }
            for article in articles
        ]


@router.get("/suggest")
async def search_suggest(q: str = Query(..., min_length=1), limit: int = 10):
    """
    Quick suggestions for autocomplete
    Returns stock symbols and names only for fast dropdown
    """
    try:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Company
        from sqlalchemy import select, or_

        query_upper = q.upper()

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Company.symbol, Company.name, Company.sector)
                .where(
                    or_(
                        Company.symbol.ilike(f"{query_upper}%"),
                        Company.name.ilike(f"%{q}%"),
                    )
                )
                .limit(limit)
            )

            suggestions = []
            for row in result:
                suggestions.append(
                    {
                        "symbol": row.symbol,
                        "name": row.name or row.symbol,
                        "sector": row.sector,
                    }
                )

            return {"success": True, "data": suggestions}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}


@router.get("/trending")
async def get_trending():
    """Get trending stocks based on volume and price movement"""
    try:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Company, StockQuote
        from sqlalchemy import select, func, desc

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Company.symbol,
                    Company.name,
                    func.max(StockQuote.close).label("price"),
                    func.max(StockQuote.volume).label("volume"),
                )
                .join(StockQuote, Company.id == StockQuote.company_id)
                .group_by(Company.id)
                .order_by(desc(func.max(StockQuote.volume)))
                .limit(10)
            )

            trending = []
            for row in result:
                trending.append(
                    {
                        "symbol": row.symbol,
                        "name": row.name or row.symbol,
                        "price": float(row.price) if row.price else 0,
                        "volume": row.volume or 0,
                    }
                )

            return {"success": True, "data": trending}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}


@router.get("/company/{symbol}")
async def get_company_profile(symbol: str):
    """Get detailed company profile"""
    try:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Company, StockQuote, NewsArticle
        from sqlalchemy import select, func, desc
        from datetime import datetime, timedelta

        async with AsyncSessionLocal() as session:
            # Get company
            result = await session.execute(
                select(Company).where(Company.symbol == symbol.upper())
            )
            company = result.scalar_one_or_none()

            if not company:
                return {"success": False, "error": "Company not found"}

            # Get latest quote
            quote_result = await session.execute(
                select(StockQuote)
                .where(StockQuote.company_id == company.id)
                .order_by(desc(StockQuote.timestamp))
                .limit(1)
            )
            quote = quote_result.scalar_one_or_none()

            # Get recent news
            news_result = await session.execute(
                select(NewsArticle).order_by(desc(NewsArticle.published_at)).limit(5)
            )
            news = news_result.scalars().all()

            return {
                "success": True,
                "data": {
                    "symbol": company.symbol,
                    "name": company.name,
                    "sector": company.sector,
                    "industry": company.industry,
                    "market_cap": float(company.market_cap)
                    if company.market_cap
                    else 0,
                    "listing_date": company.listing_date.isoformat()
                    if company.listing_date
                    else None,
                    "face_value": float(company.face_value)
                    if company.face_value
                    else 10,
                    "price": float(quote.close) if quote and quote.close else 0,
                    "volume": quote.volume if quote else 0,
                    "news": [
                        {
                            "headline": n.headline,
                            "source": n.source,
                            "timestamp": n.published_at.isoformat()
                            if n.published_at
                            else None,
                        }
                        for n in news
                    ],
                },
            }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}
