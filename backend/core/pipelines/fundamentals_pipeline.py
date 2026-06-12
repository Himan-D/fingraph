"""
Pipeline: scrape fundamentals from Screener.in -> persist to PostgreSQL.
Supports batch refresh of all stocks, single-company refresh, and scheduler.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from db.postgres import AsyncSessionLocal
from db.postgres_models import Company, Fundamental, Shareholding, StockInventory
from core.scraper.screener_scraper import ScreenerScraper

logger = logging.getLogger(__name__)

_SCRAPE_SEMAPHORE = asyncio.Semaphore(10)


async def refresh_company_fundamentals(
    symbol: str, session: Optional[AsyncSessionLocal] = None
) -> dict:
    """Scrape one company from Screener.in and persist to DB."""
    async with _SCRAPE_SEMAPHORE:
        if session is not None:
            return await _refresh(session, symbol)
        async with AsyncSessionLocal() as s:
            return await _refresh(s, symbol)


async def _refresh(session, symbol: str) -> dict:
    """Inner refresh — caller owns session lifecycle."""
    try:
        company = await _get_or_create_company(session, symbol)
        if not company:
            return {"symbol": symbol, "success": False, "error": "Company not found"}

        async with ScreenerScraper() as scraper:
            data = await scraper.get_company(symbol)
            if not data or not data.get("pe"):
                logger.warning(f"No fundamentals data for {symbol}")
                return {"symbol": symbol, "success": False, "error": "No data"}

        company.market_cap = _safe_float(data.get("market_cap"))
        company.sector = data.get("sector") or company.sector
        quarter = _current_quarter()

        existing = await session.execute(
            select(Fundamental).where(
                Fundamental.company_id == company.id,
                Fundamental.quarter == quarter,
            )
        )
        existing_fund = existing.scalar_one_or_none()

        fund_data = {
            "company_id": company.id,
            "quarter": quarter,
            "eps": _safe_float(data.get("eps")),
            "pe": _safe_float(data.get("pe")),
            "pb": _safe_float(data.get("pb")),
            "roe": _safe_float(data.get("roe")),
            "roce": _safe_float(data.get("roce")),
            "debt_equity": _safe_float(data.get("debt_equity")),
            "dividend_yield": _safe_float(data.get("dividend_yield")),
        }

        if existing_fund:
            for key, val in fund_data.items():
                setattr(existing_fund, key, val)
        else:
            session.add(Fundamental(**fund_data))

        promoter = _safe_float(data.get("promoter_holding"))
        fii = _safe_float(data.get("fii_holding"))
        dii = _safe_float(data.get("dii_holding"))
        if any(v is not None for v in (promoter, fii, dii)):
            existing_sh = await session.execute(
                select(Shareholding).where(
                    Shareholding.company_id == company.id,
                    Shareholding.date == datetime.now().date(),
                )
            )
            existing_sh_row = existing_sh.scalar_one_or_none()
            sh_data = {
                "company_id": company.id,
                "date": datetime.now().date(),
                "promoter": promoter,
                "fii": fii,
                "dii": dii,
            }
            if existing_sh_row:
                for key, val in sh_data.items():
                    setattr(existing_sh_row, key, val)
            else:
                session.add(Shareholding(**sh_data))

        await session.commit()
        logger.info(f"Refreshed fundamentals for {symbol}")
        return {"symbol": symbol, "success": True, "data": data}

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to refresh {symbol}: {e}")
        return {"symbol": symbol, "success": False, "error": str(e)}


async def refresh_all_fundamentals(limit: Optional[int] = None) -> List[dict]:
    """Scrape and persist fundamentals for all tracked stocks concurrently."""
    async with AsyncSessionLocal() as session:
        query = select(StockInventory).where(StockInventory.is_active == 1)
        if limit:
            query = query.limit(limit)
        result = await session.execute(query)
        stocks = result.scalars().all()

    symbols = [s.symbol for s in stocks]
    if not symbols:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Company).limit(limit or 200))
            symbols = [c.symbol for c in result.scalars().all()]

    if not symbols:
        return []

    logger.info(f"Starting concurrent batch refresh for {len(symbols)} stocks")

    async def refresh_one(sym: str) -> dict:
        return await refresh_company_fundamentals(sym)

    results = await asyncio.gather(*[refresh_one(s) for s in symbols])
    success_count = sum(1 for r in results if r.get("success"))
    logger.info(f"Batch refresh complete: {success_count}/{len(results)} succeeded")
    return results


async def refresh_sector_fundamentals(sector: str) -> List[dict]:
    """Refresh fundamentals for all companies in a sector."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Company).where(Company.sector.ilike(f"%{sector}%"))
        )
        companies = result.scalars().all()

    async def refresh_one(c: Company) -> dict:
        return await refresh_company_fundamentals(c.symbol)

    results = await asyncio.gather(*[refresh_one(c) for c in companies])
    return results


def _current_quarter() -> str:
    """Indian financial year: Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar"""
    now = datetime.now()
    q = (now.month - 1) // 3 + 1
    fy = now.year if q < 4 else now.year + 1
    return f"Q{q} FY{fy}"


async def _get_or_create_company(session, symbol: str) -> Optional[Company]:
    result = await session.execute(
        select(Company).where(Company.symbol == symbol.upper())
    )
    company = result.scalar_one_or_none()
    if not company:
        async with ScreenerScraper() as scraper:
            data = await scraper.get_company(symbol)
        if not data:
            return None
        company = Company(
            symbol=symbol.upper(),
            name=data.get("name", symbol),
            sector=data.get("sector"),
        )
        session.add(company)
        await session.flush()
    return company


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
