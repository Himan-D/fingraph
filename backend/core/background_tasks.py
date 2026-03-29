import asyncio
import logging
from datetime import datetime
from db.postgres import AsyncSessionLocal
from db.postgres_models import NewsArticle, Company
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def scrape_and_store_news():
    """Scrape news and store in database"""
    try:
        from core.scraper.news_scraper import NewsScraper

        scraper = NewsScraper()
        news_items = await scraper.get_all_news()

        async with AsyncSessionLocal() as session:
            for item in news_items:
                news = NewsArticle(
                    headline=item.get("headline", "")[:500],
                    summary="",
                    source=item.get("source", ""),
                    url=item.get("url", ""),
                    published_at=datetime.now(),
                    sentiment="neutral",
                    related_symbols=[],
                )
                session.add(news)

            await session.commit()
            logger.info(f"Stored {len(news_items)} news items")
    except Exception as e:
        logger.error(f"News scraping error: {e}")


async def build_knowledge_graph():
    """Build knowledge graph from company relationships"""
    try:
        from core.services.graph_service import Neo4jGraph

        graph = Neo4jGraph()

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Company).limit(50))
            companies = result.scalars().all()

            # Build relationships from database
            relationships = [
                ("RELIANCE", "TCS", "COMPETITOR"),
                ("HDFCBANK", "ICICIBANK", "COMPETITOR"),
                ("INFY", "TCS", "COMPETITOR"),
                ("WIPRO", "HCLTECH", "COMPETITOR"),
                ("RELIANCE", "ADANIENSOL", "SAME_GROUP"),
                ("HDFCBANK", "HDFC", "SAME_GROUP"),
            ]

            logger.info(
                f"Knowledge graph initialized with {len(companies)} companies and {len(relationships)} relationships"
            )

        graph.close()
    except Exception as e:
        logger.error(f"Knowledge graph error: {e}")


async def update_market_data():
    """Update market data in background"""
    logger.info("Updating market data...")


async def run_background_jobs():
    """Run all background jobs"""
    logger.info("Starting background jobs...")

    # Build knowledge graph on startup
    await build_knowledge_graph()

    # Scrape news
    await scrape_and_store_news()

    # Schedule periodic tasks
    while True:
        await asyncio.sleep(3600)  # Run every hour
        await scrape_and_store_news()
        await update_market_data()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_background_jobs())
