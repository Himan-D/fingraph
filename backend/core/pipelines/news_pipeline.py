import logging
from datetime import datetime
from typing import List

from sqlalchemy import select, and_

from db.postgres import AsyncSessionLocal
from db.postgres_models import NewsArticle
from core.services.sentiment import SentimentEngine

logger = logging.getLogger(__name__)


async def process_unsentimented_articles() -> int:
    engine = SentimentEngine()
    processed = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(NewsArticle)
            .where(
                NewsArticle.sentiment == None,
                NewsArticle.headline != None,
            )
            .limit(20)
        )
        articles = result.scalars().all()

        if not articles:
            return 0

        headlines = [
            {"headline": a.headline or "", "source": a.source or ""}
            for a in articles
        ]

        sentiments = await engine.analyze_headlines(headlines)

        for article, sentiment in zip(articles, sentiments):
            article.sentiment = sentiment.get("sentiment", "neutral")
            if sentiment.get("symbols"):
                existing = set(article.related_symbols or [])
                existing.update(sentiment["symbols"])
                article.related_symbols = list(existing)
            processed += 1

        await session.commit()

    logger.info(f"Processed sentiment for {processed} articles")
    return processed
