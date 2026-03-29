from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class ScreenerFilters(BaseModel):
    # Valuation filters
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    pe_min: Optional[float] = None
    pe_max: Optional[float] = None
    pb_min: Optional[float] = None
    pb_max: Optional[float] = None

    # Profitability filters
    roe_min: Optional[float] = None
    roce_min: Optional[float] = None
    net_margin_min: Optional[float] = None

    # Growth filters
    revenue_growth_min: Optional[float] = None
    profit_growth_min: Optional[float] = None

    # Dividend filters
    dividend_yield_min: Optional[float] = None

    # Debt filters
    debt_equity_max: Optional[float] = None

    # Sector
    sector: Optional[str] = None

    # Limits
    limit: int = 50


@router.post("/run")
async def run_screener(filters: ScreenerFilters):
    """Run stock screener with filters"""
    try:
        # TODO: Implement actual screening logic with database queries
        # For now, return empty results

        return {"success": True, "data": [], "count": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_templates():
    """Get saved screener templates"""
    templates = [
        {"id": 1, "name": "Large Cap Value", "filters": {"pe_max": 15, "roe_min": 15}},
        {
            "id": 2,
            "name": "High Growth",
            "filters": {"revenue_growth_min": 20, "profit_growth_min": 20},
        },
        {"id": 3, "name": "Dividend Yield", "filters": {"dividend_yield_min": 3}},
        {"id": 4, "name": "Low Debt", "filters": {"debt_equity_max": 0.5}},
        {
            "id": 5,
            "name": "Mid Cap Gems",
            "filters": {"market_cap_min": 5000, "market_cap_max": 50000, "roe_min": 20},
        },
    ]

    return {"success": True, "data": templates}


@router.post("/save")
async def save_screener(name: str, filters: ScreenerFilters):
    """Save custom screener"""
    return {"success": True, "message": f"Screener '{name}' saved"}


@router.get("/compare")
async def compare_stocks(symbols: str):
    """Compare multiple stocks"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    return {"success": True, "data": {"symbols": symbol_list, "metrics": {}}}
