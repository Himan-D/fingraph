from fastapi import APIRouter, Query
from typing import Optional
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import AsyncSessionLocal
from db.postgres_models import TwitterPost, RedditPost, SocialSentiment

router = APIRouter()


@router.get("/twitter")
async def get_twitter_posts(
    symbol: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    """Get Twitter posts, optionally filtered by symbol"""
    async with AsyncSessionLocal() as session:
        query = select(TwitterPost).order_by(TwitterPost.timestamp.desc())

        if symbol:
            query = query.where(TwitterPost.symbol == symbol.upper())

        query = query.limit(limit)

        result = await session.execute(query)
        posts = result.scalars().all()

        return [
            {
                "id": p.post_id,
                "username": p.username,
                "text": p.text,
                "symbol": p.symbol,
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
                "likes": p.likes,
                "retweets": p.retweets,
            }
            for p in posts
        ]


@router.get("/reddit")
async def get_reddit_posts(
    subreddit: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    """Get Reddit posts, optionally filtered by subreddit or symbol"""
    async with AsyncSessionLocal() as session:
        query = select(RedditPost).order_by(RedditPost.timestamp.desc())

        if subreddit:
            query = query.where(RedditPost.subreddit == subreddit.lower())

        query = query.limit(limit)

        result = await session.execute(query)
        posts = result.scalars().all()

        filtered = posts
        if symbol:
            sym = symbol.upper()
            filtered = [p for p in posts if sym in (p.symbols or [])]

        return [
            {
                "id": p.post_id,
                "title": p.title,
                "text": p.text,
                "author": p.author,
                "subreddit": p.subreddit,
                "url": p.url,
                "score": p.score,
                "num_comments": p.num_comments,
                "symbols": p.symbols,
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            }
            for p in filtered[:limit]
        ]


@router.get("/sentiment/{symbol}")
async def get_sentiment(
    symbol: str,
    source: Optional[str] = None,
    days: int = Query(30, le=90),
):
    """Get sentiment data for a symbol"""
    from datetime import timedelta

    async with AsyncSessionLocal() as session:
        query = select(SocialSentiment).where(
            SocialSentiment.symbol == symbol.upper(),
            SocialSentiment.date >= date.today() - timedelta(days=days),
        )

        if source:
            query = query.where(SocialSentiment.source == source)

        query = query.order_by(SocialSentiment.date.desc())

        result = await session.execute(query)
        records = result.scalars().all()

        if not records:
            return {"message": "No sentiment data found", "data": []}

        return {
            "symbol": symbol.upper(),
            "data": [
                {
                    "date": r.date.isoformat(),
                    "source": r.source,
                    "sentiment_score": r.sentiment_score,
                    "mention_count": r.mention_count,
                    "bullish_count": r.bullish_count,
                    "bearish_count": r.bearish_count,
                }
                for r in records
            ],
        }


@router.get("/sentiment/latest")
async def get_latest_sentiment(
    symbols: str = Query("", description="Comma-separated symbols"),
    limit: int = Query(20, le=50),
):
    """Get latest sentiment for multiple symbols"""
    async with AsyncSessionLocal() as session:
        sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        if not sym_list:
            query = (
                select(SocialSentiment)
                .where(SocialSentiment.date == date.today())
                .order_by(SocialSentiment.mention_count.desc())
                .limit(limit)
            )
        else:
            query = (
                select(SocialSentiment)
                .where(
                    SocialSentiment.symbol.in_(sym_list),
                    SocialSentiment.date == date.today(),
                )
                .order_by(SocialSentiment.mention_count.desc())
            )

        result = await session.execute(query)
        records = result.scalars().all()

        latest = {}
        for r in records:
            if r.symbol not in latest:
                latest[r.symbol] = {
                    "symbol": r.symbol,
                    "sentiment_score": r.sentiment_score,
                    "mention_count": r.mention_count,
                    "source": r.source,
                }

        return list(latest.values())


@router.post("/pipeline/run")
async def run_social_pipeline(
    dry_run: bool = False,
):
    """Manually trigger the social data pipeline"""
    if dry_run:
        return {"message": "Dry run - no action taken"}

    from core.services.social_pipeline import run_pipeline

    await run_pipeline()
    return {"message": "Social pipeline executed successfully"}


@router.get("/trending")
async def get_trending_symbols(
    limit: int = Query(20, le=50),
    source: Optional[str] = None,
):
    """Get trending symbols by mention count"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import func

        query = select(
            SocialSentiment.symbol,
            func.sum(SocialSentiment.mention_count).label("total_mentions"),
            func.avg(SocialSentiment.sentiment_score).label("avg_sentiment"),
        ).where(SocialSentiment.date >= date.today())

        if source:
            query = query.where(SocialSentiment.source == source)

        query = (
            query.group_by(SocialSentiment.symbol)
            .order_by(func.sum(SocialSentiment.mention_count).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        rows = result.all()

        return [
            {
                "symbol": r.symbol,
                "mentions": r.total_mentions,
                "sentiment": round(r.avg_sentiment or 0, 2),
            }
            for r in rows
        ]
