from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from config import settings
from api.routes import (
    quotes,
    fundamentals,
    screener,
    graph,
    ai,
    news,
    watchlist,
    search,
    webhooks,
    sebi,
    social,
    analytics,
    commodity,
    agent,
    billing,
    signals,
    monitoring,
)
from db.postgres import init_db
from db.redis_client import init_redis, close_redis
from core.services.truedata_service import TrueDataService
from core.background_tasks import build_knowledge_graph, scrape_and_store_news
from core.scheduler import start_scheduler, stop_scheduler
from middleware.logging_middleware import RequestLoggingMiddleware
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.rate_limiter import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

background_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FinGraph Terminal...")

    # Initialize databases
    await init_db()
    await init_redis()

    # Initialize TrueData service
    if settings.TRUEDATA_USERNAME and settings.TRUEDATA_PASSWORD:
        app.state.truedata = TrueDataService()
        await app.state.truedata.connect()
        logger.info("TrueData service connected")

    # Start background scheduler
    try:
        start_scheduler()
    except Exception as e:
        logger.warning(f"Scheduler start skipped: {e}")

    # Run initial data fetch
    try:
        await build_knowledge_graph()
    except Exception as e:
        logger.warning(f"Knowledge graph init skipped: {e}")

    try:
        await scrape_and_store_news()
    except Exception as e:
        logger.warning(f"News scraping skipped: {e}")

    yield

    # Cleanup
    if hasattr(app.state, "truedata"):
        await app.state.truedata.disconnect()
    stop_scheduler()
    await close_redis()
    logger.info("FinGraph Terminal shutdown complete")


app = FastAPI(
    title="FinGraph Terminal API",
    description="Indian Stock Market Intelligence Terminal",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware — order matters: outermost runs first
# ErrorHandler must wrap everything so it catches errors from other middleware too
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware, window=60, max_requests=120)
app.add_middleware(RequestLoggingMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    commodity.router,
    prefix=f"{settings.API_V1_PREFIX}/commodities",
    tags=["commodities"],
)
app.include_router(
    agent.router, prefix=f"{settings.API_V1_PREFIX}/agent", tags=["agent"]
)
app.include_router(
    fundamentals.router, prefix=f"{settings.API_V1_PREFIX}", tags=["fundamentals"]
)
app.include_router(
    screener.router, prefix=f"{settings.API_V1_PREFIX}/screen", tags=["screener"]
)
app.include_router(
    graph.router, prefix=f"{settings.API_V1_PREFIX}/graph", tags=["graph"]
)
app.include_router(ai.router, prefix=f"{settings.API_V1_PREFIX}/ai", tags=["ai"])
app.include_router(news.router, prefix=f"{settings.API_V1_PREFIX}/news", tags=["news"])
app.include_router(
    watchlist.router, prefix=f"{settings.API_V1_PREFIX}/watchlist", tags=["watchlist"]
)
app.include_router(
    search.router, prefix=f"{settings.API_V1_PREFIX}/search", tags=["search"]
)
app.include_router(
    webhooks.router, prefix=f"{settings.API_V1_PREFIX}/webhooks", tags=["webhooks"]
)
app.include_router(sebi.router, prefix=f"{settings.API_V1_PREFIX}/sebi", tags=["sebi"])
app.include_router(
    social.router, prefix=f"{settings.API_V1_PREFIX}/social", tags=["social"]
)
app.include_router(
    analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["analytics"]
)
app.include_router(
    commodity.router,
    prefix=f"{settings.API_V1_PREFIX}/commodities",
    tags=["commodities"],
)
app.include_router(
    agent.router, prefix=f"{settings.API_V1_PREFIX}/agent", tags=["agent"]
)
app.include_router(
    billing.router, prefix=f"{settings.API_V1_PREFIX}/billing", tags=["billing"]
)
app.include_router(
    signals.router, prefix=f"{settings.API_V1_PREFIX}/signals", tags=["signals"]
)
app.include_router(
    monitoring.router,
    prefix=f"{settings.API_V1_PREFIX}/monitoring",
    tags=["monitoring"],
)


@app.get("/")
async def root():
    return {"message": "FinGraph Terminal API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Dependency health check — used by Docker / load-balancer probes."""
    status: dict = {"status": "ok", "services": {}}

    # PostgreSQL
    try:
        from db.postgres import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["services"]["postgres"] = "ok"
    except Exception as e:
        status["services"]["postgres"] = f"error: {e}"
        status["status"] = "degraded"

    # Redis
    try:
        from db.redis_client import get_redis

        redis = await get_redis()
        await redis.ping()
        status["services"]["redis"] = "ok"
    except Exception as e:
        status["services"]["redis"] = f"error: {e}"
        status["status"] = "degraded"

    return status
