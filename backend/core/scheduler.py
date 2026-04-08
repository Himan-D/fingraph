import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db.postgres import AsyncSessionLocal
from db.postgres_models import NewsArticle, Company, StockQuote
from sqlalchemy import select, delete

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scrape_and_store_news():
    """Scrape news from RSS feeds and store in database"""
    try:
        from core.scraper.rss_scraper import RSSScraper

        scraper = RSSScraper()
        news_items = await scraper.get_all_rss_news()

        if not news_items:
            # Fallback to web scraper
            from core.scraper.news_scraper import NewsScraper

            web_scraper = NewsScraper()
            news_items = await web_scraper.get_all_news()

        async with AsyncSessionLocal() as session:
            # Don't delete - just add new news
            # Keep only last 500 articles to prevent DB bloat
            result = await session.execute(
                select(NewsArticle).order_by(NewsArticle.id.desc())
            )
            existing = result.scalars().all()
            if len(existing) > 500:
                # Delete oldest
                to_delete = existing[500:]
                for old in to_delete:
                    await session.delete(old)

            for item in news_items:
                news = NewsArticle(
                    headline=item.get("headline", ""),  # No limit
                    summary=item.get("summary", ""),  # No limit
                    source=item.get("source", ""),
                    url=item.get("url", ""),
                    published_at=datetime.now(),
                    sentiment="neutral",
                    related_symbols=[],
                )
                session.add(news)

            await session.commit()
            logger.info(f"Stored {len(news_items)} news items from RSS")
    except Exception as e:
        logger.error(f"News scraping error: {e}")


async def scrape_sebi_filings():
    """Scrape SEBI filings"""
    try:
        from core.scraper.sebi_scraper import SebiScraper

        scraper = SebiScraper()
        filings = await scraper.get_latest_filings()

        async with AsyncSessionLocal() as session:
            for item in filings:
                news = NewsArticle(
                    headline=item.get("title", "")[:500],
                    summary="",
                    source="SEBI",
                    url=item.get("url", ""),
                    published_at=datetime.now(),
                    sentiment="regulatory",
                    related_symbols=[],
                )
                session.add(news)

            await session.commit()
            logger.info(f"Stored {len(filings)} SEBI filings")
    except Exception as e:
        logger.error(f"SEBI scraping error: {e}")


async def update_stock_prices():
    """Update stock prices from various sources"""
    try:
        from core.scraper.historical_scraper import HistoricalDataScraper
        from core.data_sources.nse import NSEDataFetcher

        fetcher = NSEDataFetcher()
        scraper = HistoricalDataScraper()

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Company).limit(30))
            companies = result.scalars().all()

            # Update prices for each company
            for company in companies:
                try:
                    quote_data = await fetcher.get_quote(company.symbol)
                    if quote_data:
                        quote = StockQuote(
                            company_id=company.id,
                            timestamp=datetime.now(),
                            open=quote_data.get("open", 0),
                            high=quote_data.get("high", 0),
                            low=quote_data.get("low", 0),
                            close=quote_data.get("price", 0),
                            volume=quote_data.get("volume", 0),
                        )
                        session.add(quote)
                except Exception as e:
                    logger.debug(f"Failed to update {company.symbol}: {e}")

            await session.commit()
            logger.info(f"Updated stock prices")

        await fetcher.close()
    except Exception as e:
        logger.error(f"Stock update error: {e}")


async def scrape_historical_data():
    """Scrape historical data for all companies"""
    try:
        from core.scraper.historical_scraper import scrape_all_historical

        await scrape_all_historical()
    except Exception as e:
        logger.error(f"Historical data scrape error: {e}")


async def scrape_social_media():
    """Scrape Twitter and Reddit for finance data"""
    try:
        from core.services.social_pipeline import run_pipeline

        await run_pipeline()
    except Exception as e:
        logger.error(f"Social media pipeline error: {e}")


async def scrape_commodities():
    """Scrape commodity prices and news"""
    try:
        from core.services.commodity_pipeline import run_pipeline

        await run_pipeline()
    except Exception as e:
        logger.error(f"Commodity pipeline error: {e}")


async def build_knowledge_graph_nodes():
    """Build knowledge graph in Neo4j using AI to determine relationships"""
    try:
        from core.services.graph_service import Neo4jGraph
        from core.services.relationship_ai import analyze_and_build_graph

        graph = Neo4jGraph()

        if not graph.driver:
            logger.warning("Neo4j not connected, skipping knowledge graph")
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Company).limit(100))
            companies = result.scalars().all()

            # Get unique sectors
            sectors = set()

            # Add all companies as nodes
            for company in companies:
                try:
                    graph.add_company_node(
                        company.symbol,
                        company.name,
                        company.sector or "Other",
                        company.industry or "",
                        float(company.market_cap) if company.market_cap else 0,
                    )
                    if company.sector:
                        sectors.add(company.sector)
                except Exception as e:
                    logger.debug(f"Failed to add {company.symbol}: {e}")

            # Add all sectors
            for sector in sectors:
                graph.add_sector_node(sector)
                # Link companies to sectors
                sector_companies = [c for c in companies if c.sector == sector]
                for sc in sector_companies:
                    graph.add_sector_relationship(sc.symbol, sector)

            # Use AI to determine relationships dynamically
            logger.info("Analyzing company relationships with AI...")
            relationships = await analyze_and_build_graph()

            # Add AI-generated relationships
            for src, tgt, rel_type in relationships:
                graph.add_relationship(src, tgt, rel_type)

            # Get graph stats
            graph_data = graph.get_all_nodes()
            logger.info(
                f"Knowledge graph populated: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges"
            )

        graph.close()
    except Exception as e:
        logger.error(f"Knowledge graph error: {e}")


def start_scheduler():
    """Start background scheduler"""
    try:
        # Schedule news scraping every 30 minutes
        scheduler.add_job(
            scrape_and_store_news,
            trigger=IntervalTrigger(minutes=30),
            id="news_scraper",
            replace_existing=True,
        )

        # Schedule SEBI filings every 2 hours
        scheduler.add_job(
            scrape_sebi_filings,
            trigger=IntervalTrigger(hours=2),
            id="sebi_scraper",
            replace_existing=True,
        )

        # Schedule stock updates every 5 minutes
        scheduler.add_job(
            update_stock_prices,
            trigger=IntervalTrigger(minutes=5),
            id="stock_updater",
            replace_existing=True,
        )

        # Schedule historical data once daily
        scheduler.add_job(
            scrape_historical_data,
            trigger=IntervalTrigger(hours=24),
            id="historical_scraper",
            replace_existing=True,
        )

        # Schedule knowledge graph every hour
        scheduler.add_job(
            build_knowledge_graph_nodes,
            trigger=IntervalTrigger(hours=1),
            id="kg_builder",
            replace_existing=True,
        )

        # Schedule social media scraping every 15 minutes
        scheduler.add_job(
            scrape_social_media,
            trigger=IntervalTrigger(minutes=15),
            id="social_media_scraper",
            replace_existing=True,
        )

        # Schedule commodity scraping every 15 minutes
        scheduler.add_job(
            scrape_commodities,
            trigger=IntervalTrigger(minutes=15),
            id="commodity_scraper",
            replace_existing=True,
        )

        scheduler.start()
        logger.info(
            "Scheduler started: news(30m), sebi(2h), stocks(5min), historical(24h), kg(1h), social(15min), commodities(15min)"
        )
    except Exception as e:
        logger.error(f"Scheduler error: {e}")


def stop_scheduler():
    """Stop background scheduler"""
    try:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.warning(f"Scheduler shutdown error: {e}")
