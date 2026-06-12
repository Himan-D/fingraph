import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db
from db.postgres_models import Company, Fundamental, StockQuote, SavedScreener
from api.deps import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Pydantic Schemas ──────────────────────────────────────────


class ScreenerFilterSchema(BaseModel):
    field: str
    op: str  # eq, neq, gte, lte, gt, lt, contains, between
    value: Any


class ScreenerConfigSchema(BaseModel):
    title: str
    filters: List[ScreenerFilterSchema] = []
    logic: str = "AND"
    columns: List[str] = []
    sort_field: Optional[str] = None
    sort_direction: str = "desc"
    limit: int = 50


class GenerateRequest(BaseModel):
    description: str


class SaveRequest(BaseModel):
    title: str
    config: dict


# ── Config-to-SQL translator ──────────────────────────────────


def _apply_filters(query, filters: List[dict], logic: str):
    from sqlalchemy import or_

    conditions = []
    for f in filters:
        field = f.get("field", "")
        op = f.get("op", "eq")
        value = f.get("value")

        col = _resolve_field(field)
        if col is None:
            continue

        cond = _build_condition(col, op, value)
        if cond is not None:
            conditions.append(cond)

    if not conditions:
        return query

    if logic == "OR":
        return query.where(or_(*conditions))
    return query.where(*conditions)


def _resolve_field(field: str):
    mapping = {
        "symbol": Company.symbol,
        "name": Company.name,
        "sector": Company.sector,
        "industry": Company.industry,
        "market_cap_cr": Company.market_cap,
        "price": StockQuote.close,
        "open": StockQuote.open,
        "high": StockQuote.high,
        "low": StockQuote.low,
        "volume": StockQuote.volume,
        "pe": Fundamental.pe,
        "pb": Fundamental.pb,
        "roe": Fundamental.roe,
        "roce": Fundamental.roce,
        "eps": Fundamental.eps,
        "debt_equity": Fundamental.debt_equity,
        "current_ratio": Fundamental.current_ratio,
        "gross_margin": Fundamental.gross_margin,
        "net_margin": Fundamental.net_margin,
        "dividend_yield": Fundamental.dividend_yield,
        "revenue": Fundamental.revenue,
        "profit": Fundamental.profit,
    }
    return mapping.get(field)


def _build_condition(col, op: str, value):
    if value is None:
        return None
    try:
        if op == "eq":
            return col == value
        elif op == "neq":
            return col != value
        elif op == "gte":
            return col >= float(value)
        elif op == "lte":
            return col <= float(value)
        elif op == "gt":
            return col > float(value)
        elif op == "lt":
            return col < float(value)
        elif op == "contains":
            return col.ilike(f"%{value}%")
        elif op == "between":
            if isinstance(value, list) and len(value) == 2:
                return col.between(float(value[0]), float(value[1]))
    except (ValueError, TypeError):
        return None
    return None


def _to_crores(value):
    if value is None:
        return None
    return round(value / 1e7, 2)


# ── Endpoints ─────────────────────────────────────────────────


@router.post("/screener/execute")
async def execute_screener(config: ScreenerConfigSchema):
    try:
        from sqlalchemy import or_

        query = (
            select(Company, StockQuote, Fundamental)
            .join(StockQuote, Company.id == StockQuote.company_id)
            .join(Fundamental, Company.id == Fundamental.company_id)
            .where(Company.market_cap.isnot(None))
        )

        filters_dict = [f.model_dump() for f in config.filters]
        query = _apply_filters(query, filters_dict, config.logic)

        if config.sort_field:
            sort_col = _resolve_field(config.sort_field)
            if sort_col is not None:
                if config.sort_direction == "asc":
                    query = query.order_by(sort_col)
                else:
                    query = query.order_by(desc(sort_col))

        query = query.limit(min(config.limit, 200))

        from sqlalchemy.ext.asyncio import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(query)
            rows = result.all()

            results = []
            for company, quote, fund in rows:
                row = {
                    "symbol": company.symbol,
                    "name": company.name,
                    "sector": company.sector,
                    "industry": company.industry,
                    "market_cap_cr": _to_crores(company.market_cap),
                    "price": round(quote.close, 2) if quote and quote.close else None,
                    "change_pct": round(quote.pct_change, 2) if quote and hasattr(quote, "pct_change") and quote.pct_change else None,
                    "volume": quote.volume if quote else None,
                    "pe": round(fund.pe, 2) if fund and fund.pe else None,
                    "pb": round(fund.pb, 2) if fund and fund.pb else None,
                    "roe": round(fund.roe, 2) if fund and fund.roe else None,
                    "roce": round(fund.roce, 2) if fund and fund.roce else None,
                    "eps": round(fund.eps, 2) if fund and fund.eps else None,
                    "debt_equity": round(fund.debt_equity, 2) if fund and fund.debt_equity else None,
                    "current_ratio": round(fund.current_ratio, 2) if fund and fund.current_ratio else None,
                    "gross_margin": round(fund.gross_margin, 2) if fund and fund.gross_margin else None,
                    "net_margin": round(fund.net_margin, 2) if fund and fund.net_margin else None,
                    "dividend_yield": round(fund.dividend_yield, 2) if fund and fund.dividend_yield else None,
                    "revenue": fund.revenue,
                    "profit": fund.profit,
                }
                results.append(row)

            return {"success": True, "count": len(results), "data": results}
    except Exception as e:
        logger.error(f"execute_screener error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/screener/generate")
async def generate_screener(req: GenerateRequest):
    try:
        from core.services.agent_tools import tool_generate_screener

        result = await tool_generate_screener(req.description)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"generate_screener error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/screener/saved")
async def list_saved_screeners(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional),
):
    user_id = user.get("id") if user else None
    query = select(SavedScreener).order_by(desc(SavedScreener.updated_at)).limit(limit)
    if user_id:
        query = query.where(SavedScreener.user_id == user_id)
    result = await db.execute(query)
    saved = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "title": s.title,
                "config": s.config,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in saved
        ],
    }


@router.post("/screener/save")
async def save_screener(
    req: SaveRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional),
):
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    user_id = user.get("id") if user else None
    saved = SavedScreener(
        user_id=user_id,
        title=req.title,
        config=req.config,
    )
    db.add(saved)
    await db.flush()
    return {
        "success": True,
        "data": {
            "id": saved.id,
            "title": saved.title,
            "config": saved.config,
            "created_at": saved.created_at.isoformat() if saved.created_at else None,
        },
    }


@router.delete("/screener/saved/{screener_id}")
async def delete_saved_screener(
    screener_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SavedScreener).where(SavedScreener.id == screener_id))
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Screener not found")
    await db.delete(saved)
    return {"success": True, "message": "Screener deleted"}
