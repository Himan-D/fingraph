from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class ScreenerFilters(BaseModel):
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    pe_min: Optional[float] = None
    pe_max: Optional[float] = None
    pb_min: Optional[float] = None
    pb_max: Optional[float] = None
    roe_min: Optional[float] = None
    roce_min: Optional[float] = None
    net_margin_min: Optional[float] = None
    revenue_growth_min: Optional[float] = None
    profit_growth_min: Optional[float] = None
    dividend_yield_min: Optional[float] = None
    debt_equity_max: Optional[float] = None
    sector: Optional[str] = None
    sort_by: Optional[str] = "market_cap"
    sort_order: Optional[str] = "desc"
    limit: int = 50


async def get_stocks_from_db():
    """Get all stocks from database, joining Fundamental table for real ratios."""
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import Company, StockQuote, Fundamental
    from sqlalchemy import select, func, desc, outerjoin

    async with AsyncSessionLocal() as session:
        # Latest quote per company via sub-query
        latest_quote_sq = (
            select(
                StockQuote.company_id,
                func.max(StockQuote.timestamp).label("max_ts"),
            )
            .group_by(StockQuote.company_id)
            .subquery()
        )

        result = await session.execute(
            select(
                Company.id,
                Company.symbol,
                Company.name,
                Company.sector,
                Company.industry,
                Company.market_cap,
                StockQuote.close.label("price"),
                StockQuote.open.label("open_price"),
                StockQuote.volume,
                StockQuote.high.label("week52_high"),
                StockQuote.low.label("week52_low"),
                Fundamental.pe_ratio,
                Fundamental.pb_ratio,
                Fundamental.roe,
                Fundamental.roce,
                Fundamental.debt_to_equity,
                Fundamental.dividend_yield,
            )
            .join(latest_quote_sq, Company.id == latest_quote_sq.c.company_id, isouter=True)
            .join(
                StockQuote,
                (StockQuote.company_id == Company.id)
                & (StockQuote.timestamp == latest_quote_sq.c.max_ts),
                isouter=True,
            )
            .join(Fundamental, Fundamental.company_id == Company.id, isouter=True)
            .order_by(desc(Company.market_cap))
            .limit(200)
        )

        stocks = []
        for row in result.mappings():
            price = float(row.price) if row.price else 0.0
            open_price = float(row.open_price) if row.open_price else price
            change = round(price - open_price, 2)
            pct_change = round((change / open_price) * 100, 2) if open_price else 0.0

            stocks.append(
                {
                    "symbol": row.symbol,
                    "name": row.name or row.symbol,
                    "sector": row.sector or "Other",
                    "industry": row.industry or "",
                    "price": round(price, 2),
                    "change": change,
                    "pct_change": pct_change,
                    "volume": int(row.volume) if row.volume else 0,
                    "market_cap": float(row.market_cap) if row.market_cap else 0.0,
                    "pe_ratio": float(row.pe_ratio) if row.pe_ratio is not None else None,
                    "roe": float(row.roe) if row.roe is not None else None,
                    "debt_equity": float(row.debt_to_equity) if row.debt_to_equity is not None else None,
                    "dividend_yield": float(row.dividend_yield) if row.dividend_yield is not None else None,
                    "week52_high": float(row.week52_high) if row.week52_high else None,
                    "week52_low": float(row.week52_low) if row.week52_low else None,
                }
            )
        return stocks


def sort_stocks(stocks: List[dict], sort_by: str, sort_order: str) -> List[dict]:
    """Sort stocks by field"""
    reverse = sort_order == "desc"
    sort_keys = {
        "market_cap": lambda x: x.get("market_cap", 0),
        "price": lambda x: x.get("price", 0),
        "pct_change": lambda x: x.get("pct_change", 0),
        "volume": lambda x: x.get("volume", 0),
        "pe_ratio": lambda x: x.get("pe_ratio", 0),
        "roe": lambda x: x.get("roe", 0),
    }
    key_func = sort_keys.get(sort_by, sort_keys["market_cap"])
    return sorted(stocks, key=key_func, reverse=reverse)


@router.post("/run")
async def run_screener(filters: ScreenerFilters = None):
    """Run stock screener with filters"""
    try:
        stocks = await get_stocks_from_db()

        if filters:
            if filters.market_cap_min is not None:
                stocks = [
                    s for s in stocks if s["market_cap"] >= filters.market_cap_min
                ]
            if filters.market_cap_max is not None:
                stocks = [
                    s for s in stocks if s["market_cap"] <= filters.market_cap_max
                ]
            if filters.pe_min is not None:
                stocks = [s for s in stocks if s["pe_ratio"] is not None and s["pe_ratio"] >= filters.pe_min]
            if filters.pe_max is not None:
                stocks = [s for s in stocks if s["pe_ratio"] is not None and s["pe_ratio"] <= filters.pe_max]
            if filters.roe_min is not None:
                stocks = [s for s in stocks if s["roe"] is not None and s["roe"] >= filters.roe_min]
            if filters.debt_equity_max is not None:
                stocks = [
                    s for s in stocks if s["debt_equity"] is not None and s["debt_equity"] <= filters.debt_equity_max
                ]
            if filters.dividend_yield_min is not None:
                stocks = [
                    s
                    for s in stocks
                    if s["dividend_yield"] is not None and s["dividend_yield"] >= filters.dividend_yield_min
                ]
            if filters.sector:
                stocks = [
                    s
                    for s in stocks
                    if s["sector"] and filters.sector.lower() in s["sector"].lower()
                ]

            stocks = sort_stocks(
                stocks, filters.sort_by or "market_cap", filters.sort_order or "desc"
            )
            stocks = stocks[: filters.limit]

        return {"success": True, "data": stocks, "count": len(stocks)}
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e), "data": [], "count": 0}


@router.get("/run")
async def run_screener_get(
    market_cap_min: Optional[float] = None,
    market_cap_max: Optional[float] = None,
    pe_min: Optional[float] = None,
    pe_max: Optional[float] = None,
    roe_min: Optional[float] = None,
    sector: Optional[str] = None,
    sort_by: Optional[str] = "market_cap",
    sort_order: Optional[str] = "desc",
    limit: int = 50,
):
    """Run stock screener with query parameters"""
    filters = ScreenerFilters(
        market_cap_min=market_cap_min,
        market_cap_max=market_cap_max,
        pe_min=pe_min,
        pe_max=pe_max,
        roe_min=roe_min,
        sector=sector,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
    )
    return await run_screener(filters)


@router.get("/templates")
async def get_templates():
    """Get saved screener templates"""
    templates = [
        {
            "id": 1,
            "name": "Large Cap Blue Chips",
            "description": "High market cap stocks with stable returns",
            "filters": {"market_cap_min": 50000, "pe_max": 30, "roe_min": 15},
        },
        {
            "id": 2,
            "name": "High Growth Small Cap",
            "description": "Small caps with high growth potential",
            "filters": {"market_cap_min": 500, "market_cap_max": 10000, "roe_min": 20},
        },
        {
            "id": 3,
            "name": "Undervalued Stocks",
            "description": "Stocks with low P/E ratio",
            "filters": {"pe_max": 15, "roe_min": 15},
        },
        {
            "id": 4,
            "name": "High Dividend Yield",
            "description": "Stocks with dividend yield > 3%",
            "filters": {"dividend_yield_min": 3},
        },
        {
            "id": 5,
            "name": "Low Debt",
            "description": "Stocks with low debt-to-equity",
            "filters": {"debt_equity_max": 0.5},
        },
        {
            "id": 6,
            "name": "IT Sector",
            "description": "Technology and IT stocks",
            "filters": {"sector": "Technology"},
        },
        {
            "id": 7,
            "name": "Banking Sector",
            "description": "Financial and banking stocks",
            "filters": {"sector": "Financial"},
        },
    ]
    return {"success": True, "data": templates}


@router.get("/sectors")
async def get_sectors():
    """Get list of available sectors"""
    return {
        "success": True,
        "data": [
            "Technology",
            "Financial Services",
            "Energy",
            "Automobile",
            "Healthcare",
            "FMCG",
            "Metals",
            "Construction",
            "Telecommunication",
            "Consumer Durables",
        ],
    }


@router.post("/save")
async def save_screener(name: str, filters: ScreenerFilters):
    """Save custom screener"""
    return {"success": True, "message": f"Screener '{name}' saved"}


@router.get("/compare")
async def compare_stocks(symbols: str):
    """Compare multiple stocks"""
    symbol_list = symbols.split(",")
    stocks = await get_stocks_from_db()
    filtered = [s for s in stocks if s["symbol"] in symbol_list]
    return {"success": True, "data": filtered}
