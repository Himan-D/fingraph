from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, text
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from db.postgres import get_db
from db.postgres_models import Company, StockQuote, Fundamental
from api.routes.fundamentals import SAMPLE_FUNDAMENTALS

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize NSE fetcher
_nse_fetcher = None


def get_nse_fetcher():
    global _nse_fetcher
    if _nse_fetcher is None:
        try:
            from core.data_sources.nse import NSEDataFetcher

            _nse_fetcher = NSEDataFetcher()
        except Exception as e:
            logger.warning(f"NSE fetcher init failed: {e}")
    return _nse_fetcher


@router.get("/movers")
async def get_movers(
    segment: str = "equity", limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """Get top gainers and losers - tries NSE first, falls back to DB"""
    fetcher = get_nse_fetcher()

    if fetcher:
        try:
            movers = await fetcher.get_movers()
            if movers.get("gainers") or movers.get("losers"):
                return {"success": True, "data": movers}
        except Exception as e:
            logger.warning(f"NSE movers failed: {e}")

    # Fallback to DB
    result = await db.execute(select(Company).limit(50))
    companies = result.scalars().all()

    gainers = []
    losers = []

    for company in companies:
        quote_result = await db.execute(
            select(StockQuote)
            .where(StockQuote.company_id == company.id)
            .order_by(desc(StockQuote.timestamp))
            .limit(1)
        )
        quote = quote_result.scalars().first()

        if quote and quote.open:
            pct_change = ((quote.close - quote.open) / quote.open) * 100
            data = {
                "symbol": company.symbol,
                "name": company.name,
                "price": quote.close,
                "change": quote.close - quote.open,
                "pct_change": pct_change,
                "volume": quote.volume,
            }

            if pct_change > 0:
                gainers.append(data)
            else:
                losers.append(data)

    gainers = sorted(gainers, key=lambda x: x["pct_change"], reverse=True)[:limit]
    losers = sorted(losers, key=lambda x: x["pct_change"])[:limit]

    return {"success": True, "data": {"gainers": gainers, "losers": losers}}


@router.get("/sectors")
async def get_sectors(db: AsyncSession = Depends(get_db)):
    """Get sector performance heatmap - calculates real change from stock data"""
    # Single query: for each sector, get the latest quote per company using a
    # DISTINCT ON sub-query then aggregate avg change% and total volume.
    sector_sql = text(
        """
        WITH latest AS (
            SELECT DISTINCT ON (sq.company_id)
                sq.company_id,
                sq.close,
                sq.open,
                sq.volume
            FROM stock_quotes sq
            ORDER BY sq.company_id, sq.timestamp DESC
        )
        SELECT
            c.sector                                        AS sector,
            COUNT(c.id)                                     AS count,
            AVG(
                CASE WHEN l.open > 0
                     THEN (l.close - l.open) / l.open * 100
                     ELSE NULL END
            )                                               AS avg_change,
            COALESCE(SUM(l.volume), 0)                      AS total_volume
        FROM companies c
        LEFT JOIN latest l ON l.company_id = c.id
        GROUP BY c.sector
        ORDER BY avg_change DESC NULLS LAST
        """
    )
    rows = (await db.execute(sector_sql)).mappings().all()

    sectors = [
        {
            "sector": (row["sector"] or "Other"),
            "change": round(float(row["avg_change"]), 2) if row["avg_change"] is not None else 0.0,
            "volume": int(row["total_volume"]),
            "count": int(row["count"]),
        }
        for row in rows
    ]
    return {"success": True, "data": sectors}


@router.get("/indices")
async def get_indices(db: AsyncSession = Depends(get_db)):
    """Get index values - tries NSE first"""
    fetcher = get_nse_fetcher()

    if fetcher:
        try:
            indices = await fetcher.get_indices()
            if indices:
                return {"success": True, "data": indices}
        except Exception as e:
            logger.warning(f"NSE indices failed: {e}")

    # Fallback static data
    index_data = [
        {
            "symbol": "NIFTY50",
            "name": "Nifty 50",
            "price": 22815.26,
            "change": 365.26,
            "pct_change": 1.63,
        },
        {
            "symbol": "BANKNIFTY",
            "name": "Bank Nifty",
            "price": 48520.50,
            "change": 420.80,
            "pct_change": 0.87,
        },
        {
            "symbol": "NIFTYIT",
            "name": "Nifty IT",
            "price": 35850.40,
            "change": -125.80,
            "pct_change": -0.35,
        },
        {
            "symbol": "NIFTYAUTO",
            "name": "Nifty Auto",
            "price": 18750.20,
            "change": 85.40,
            "pct_change": 0.46,
        },
        {
            "symbol": "NIFTYPHARMA",
            "name": "Nifty Pharma",
            "price": 18450.80,
            "change": -95.20,
            "pct_change": -0.51,
        },
        {
            "symbol": "NIFTYFMCG",
            "name": "Nifty FMCG",
            "price": 52850.60,
            "change": 125.40,
            "pct_change": 0.24,
        },
        {
            "symbol": "NIFTYMETAL",
            "name": "Nifty Metal",
            "price": 9150.30,
            "change": -185.60,
            "pct_change": -1.99,
        },
    ]

    return {"success": True, "data": index_data}


@router.get("/search")
async def search_symbol(q: str, db: AsyncSession = Depends(get_db)):
    """Search for symbols"""
    q = q.upper()
    results = []

    result = await db.execute(select(Company).where(Company.symbol.like(f"%{q}%")))
    companies = result.scalars().all()

    for company in companies:
        results.append(
            {
                "symbol": company.symbol,
                "name": company.name,
                "sector": company.sector,
                "industry": company.industry,
                "type": "stock",
            }
        )

    return {"success": True, "data": results[:20]}


@router.get("/option-chain/{symbol}")
async def get_option_chain(symbol: str = "NIFTY", db: AsyncSession = Depends(get_db)):
    """Get option chain for Nifty/BankNifty"""
    fetcher = get_nse_fetcher()

    if fetcher:
        try:
            chain = await fetcher.get_option_chain(symbol)
            if chain:
                return {"success": True, "data": chain}
        except Exception as e:
            logger.warning(f"NSE option chain failed: {e}")

    # Fallback mock data
    symbol = symbol.upper()

    if symbol == "NIFTY":
        underlying = 22500
    elif symbol == "BANKNIFTY":
        underlying = 48000
    else:
        underlying = 1000

    strikes = list(range(int(underlying * 0.9), int(underlying * 1.1), 100))

    calls = []
    puts = []

    for strike in strikes[:20]:
        oi = random.randint(100000, 5000000)
        vol = random.randint(50000, 2000000)
        call_price = max(underlying - strike, 5)
        put_price = max(strike - underlying, 5)

        calls.append(
            {
                "strike": strike,
                "bid": round(call_price * 0.95, 2),
                "ask": round(call_price * 1.05, 2),
                "last": round(call_price, 2),
                "volume": vol,
                "oi": oi,
                "oi_change": random.randint(-50000, 100000),
            }
        )

        puts.append(
            {
                "strike": strike,
                "bid": round(put_price * 0.95, 2),
                "ask": round(put_price * 1.05, 2),
                "last": round(put_price, 2),
                "volume": vol,
                "oi": oi,
                "oi_change": random.randint(-50000, 100000),
            }
        )

    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "underlying": underlying,
            "calls": calls,
            "puts": puts,
            "expiry": "27MAR2025",
            "timestamp": datetime.now().isoformat(),
        },
    }


@router.get("/historical/{symbol}")
async def get_historical(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    db: AsyncSession = Depends(get_db),
):
    """Get historical price data"""
    symbol = symbol.upper()

    result = await db.execute(select(Company).where(Company.symbol == symbol))
    company = result.scalars().first()

    if not company:
        return {"success": False, "error": "Company not found"}

    periods_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "2y": 730, "5y": 1825}
    days = periods_map.get(period, 365)

    result = await db.execute(
        select(StockQuote)
        .where(StockQuote.company_id == company.id)
        .order_by(desc(StockQuote.timestamp))
        .limit(days)
    )
    quotes = result.scalars().all()

    data = [
        {
            "timestamp": q.timestamp.isoformat(),
            "open": q.open,
            "high": q.high,
            "low": q.low,
            "close": q.close,
            "volume": q.volume,
        }
        for q in reversed(quotes)
    ]

    return {"success": True, "data": data}


@router.get("/batch")
async def get_batch_quotes(symbols: str, db: AsyncSession = Depends(get_db)):
    """Get multiple quotes"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = []

    for symbol in symbol_list:
        result = await db.execute(select(Company).where(Company.symbol == symbol))
        company = result.scalars().first()

        if company:
            quote_result = await db.execute(
                select(StockQuote)
                .where(StockQuote.company_id == company.id)
                .order_by(desc(StockQuote.timestamp))
                .limit(1)
            )
            quote = quote_result.scalars().first()

            if quote:
                results.append(
                    {
                        "symbol": company.symbol,
                        "name": company.name,
                        "price": quote.close,
                        "change": quote.close - quote.open,
                        "pct_change": ((quote.close - quote.open) / quote.open) * 100
                        if quote.open
                        else 0,
                        "sector": company.sector,
                    }
                )
            else:
                results.append({"symbol": symbol, "error": "No quote data"})
        else:
            results.append({"symbol": symbol, "error": "Not found"})

    return {"success": True, "data": results}


@router.get("/{symbol}")
async def get_quote(symbol: str, db: AsyncSession = Depends(get_db)):
    """Get live quote for a symbol - tries NSE first"""
    symbol = symbol.upper()

    # Try NSE first
    fetcher = get_nse_fetcher()
    if fetcher:
        try:
            nse_data = await fetcher.get_quote(symbol)
            if nse_data:
                return {"success": True, "data": nse_data}
        except Exception as e:
            logger.warning(f"NSE quote failed for {symbol}: {e}")

    # Fallback to DB
    result = await db.execute(select(Company).where(Company.symbol == symbol))
    company = result.scalars().first()

    if not company:
        return {"success": False, "error": "Company not found"}

    result = await db.execute(
        select(StockQuote)
        .where(StockQuote.company_id == company.id)
        .order_by(desc(StockQuote.timestamp))
        .limit(1)
    )
    quote = result.scalars().first()

    if not quote:
        return {"success": False, "error": "No quote data"}

    # Get 52-week high/low from historical data
    year_ago = datetime.now() - timedelta(days=365)
    hist_result = await db.execute(
        select(StockQuote)
        .where(StockQuote.company_id == company.id)
        .where(StockQuote.timestamp >= year_ago)
    )
    hist_quotes = hist_result.scalars().all()
    week52_high = (
        max((q.high for q in hist_quotes), default=0) if hist_quotes else quote.high
    )
    week52_low = (
        min((q.low for q in hist_quotes), default=0) if hist_quotes else quote.low
    )

    # Get PE ratio from SAMPLE_FUNDAMENTALS or DB
    pe_ratio = None
    if symbol in SAMPLE_FUNDAMENTALS:
        pe_ratio = SAMPLE_FUNDAMENTALS[symbol].get("pe")
    else:
        fund_result = await db.execute(
            select(Fundamental)
            .where(Fundamental.company_id == company.id)
            .order_by(desc(Fundamental.created_at))
            .limit(1)
        )
        fundamental = fund_result.scalars().first()
        pe_ratio = fundamental.pe if fundamental else None

    return {
        "success": True,
        "data": {
            "symbol": company.symbol,
            "name": company.name,
            "price": quote.close,
            "change": quote.close - quote.open,
            "pct_change": ((quote.close - quote.open) / quote.open) * 100
            if quote.open
            else 0,
            "open": quote.open,
            "high": quote.high,
            "low": quote.low,
            "volume": quote.volume,
            "market_cap": company.market_cap,
            "sector": company.sector,
            "industry": company.industry,
            "pe_ratio": pe_ratio,
            "week52_high": week52_high,
            "week52_low": week52_low,
            "timestamp": quote.timestamp.isoformat(),
        },
    }
