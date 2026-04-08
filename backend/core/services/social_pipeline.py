import asyncio
import logging
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import AsyncSessionLocal
from db.postgres_models import TwitterPost, RedditPost, SocialSentiment

logger = logging.getLogger(__name__)


async def store_twitter_posts(posts: List[Dict]) -> int:
    """Store Twitter posts to database"""
    stored = 0

    async with AsyncSessionLocal() as session:
        for post in posts:
            try:
                existing = await session.execute(
                    select(TwitterPost).where(TwitterPost.post_id == post.get("id", ""))
                )
                if existing.scalar_one_or_none():
                    continue

                twitter_post = TwitterPost(
                    post_id=post.get("id", ""),
                    username=post.get("username", ""),
                    text=post.get("text", ""),
                    source=post.get("source", "twitter"),
                    symbol=post.get("symbol"),
                    timestamp=datetime.fromisoformat(post["timestamp"])
                    if isinstance(post.get("timestamp"), str)
                    else datetime.now(),
                    likes=post.get("likes", 0),
                    retweets=post.get("retweets", 0),
                )
                session.add(twitter_post)
                stored += 1
            except Exception as e:
                logger.warning(f"Failed to store Twitter post: {e}")

        await session.commit()

    logger.info(f"Stored {stored} Twitter posts")
    return stored


async def store_reddit_posts(posts: List[Dict]) -> int:
    """Store Reddit posts to database"""
    stored = 0

    async with AsyncSessionLocal() as session:
        for post in posts:
            try:
                existing = await session.execute(
                    select(RedditPost).where(RedditPost.post_id == post.get("id", ""))
                )
                if existing.scalar_one_or_none():
                    continue

                reddit_post = RedditPost(
                    post_id=post.get("id", ""),
                    title=post.get("title", ""),
                    text=post.get("text", ""),
                    author=post.get("author", ""),
                    subreddit=post.get("subreddit", ""),
                    url=post.get("url", ""),
                    score=post.get("score", 0),
                    num_comments=post.get("num_comments", 0),
                    symbols=post.get("symbols", []),
                    timestamp=datetime.fromisoformat(post["timestamp"])
                    if isinstance(post.get("timestamp"), str)
                    else datetime.now(),
                )
                session.add(reddit_post)
                stored += 1
            except Exception as e:
                logger.warning(f"Failed to store Reddit post: {e}")

        await session.commit()

    logger.info(f"Stored {stored} Reddit posts")
    return stored


async def calculate_sentiment(symbol: str, source: str) -> Dict:
    """Calculate sentiment for a symbol from social data"""
    async with AsyncSessionLocal() as session:
        today = date.today()

        if source == "twitter":
            query = select(TwitterPost).where(
                TwitterPost.symbol == symbol,
                TwitterPost.timestamp >= datetime.combine(today, datetime.min.time()),
            )
        else:
            query = select(RedditPost).where(
                RedditPost.symbols.contains([symbol]),
                RedditPost.timestamp >= datetime.combine(today, datetime.min.time()),
            )

        result = await session.execute(query)
        posts = result.scalars().all()

        if not posts:
            return {
                "sentiment_score": 0,
                "mention_count": 0,
                "bullish_count": 0,
                "bearish_count": 0,
            }

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
        ]

        bullish = 0
        bearish = 0

        for post in posts:
            text = (post.text or post.title or "").lower()
            for kw in bullish_keywords:
                if kw in text:
                    bullish += 1
                    break
            for kw in bearish_keywords:
                if kw in text:
                    bearish += 1
                    break

        total = len(posts)
        sentiment_score = (bullish - bearish) / max(total, 1) * 100

        return {
            "sentiment_score": round(sentiment_score, 2),
            "mention_count": total,
            "bullish_count": bullish,
            "bearish_count": bearish,
        }


async def store_sentiment(symbol: str, source: str, sentiment: Dict) -> int:
    """Store calculated sentiment"""
    async with AsyncSessionLocal() as session:
        record = SocialSentiment(
            symbol=symbol,
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


async def get_sentiment_history(symbol: str, days: int = 30) -> List[Dict]:
    """Get sentiment history for a symbol"""
    async with AsyncSessionLocal() as session:
        from datetime import timedelta

        query = (
            select(SocialSentiment)
            .where(
                SocialSentiment.symbol == symbol,
                SocialSentiment.date >= date.today() - timedelta(days=days),
            )
            .order_by(SocialSentiment.date.desc())
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


TRACKED_SYMBOLS = [
    "RELIANCE",
    "INFY",
    "TCS",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "ADANIGREEN",
    "TATAMOTORS",
    "WIPRO",
    "HCLTECH",
    "TECHM",
    "LT",
    "ULTRACEMCO",
    "HINDUNILVR",
    "ITC",
    "KOTAKBANK",
]


async def run_pipeline():
    """Run complete social data pipeline"""
    from core.scraper.twitter_scraper import scrape_twitter_finance, scrape_stocktwits
    from core.scraper.reddit_scraper import scrape_reddit

    logger.info("Starting social data pipeline...")

    twitter_posts = await scrape_twitter_finance()
    await store_twitter_posts(twitter_posts)

    stocktwits_posts = await scrape_stocktwits()
    await store_twitter_posts(stocktwits_posts)

    reddit_posts = await scrape_reddit()
    await store_reddit_posts(reddit_posts)

    for symbol in TRACKED_SYMBOLS:
        for source in ["twitter", "reddit"]:
            sentiment = await calculate_sentiment(symbol, source)
            if sentiment["mention_count"] > 0:
                await store_sentiment(symbol, source, sentiment)

    logger.info("Social data pipeline complete")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
