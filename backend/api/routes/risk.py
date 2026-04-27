from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/commodity/{symbol}")
async def get_risk_analysis(symbol: str):
    """Get full risk analysis for a commodity"""
    from core.services.risk_engine import get_risk_engine
    
    engine = await get_risk_engine()
    
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import CommodityPrice
    from sqlalchemy import select, desc
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == symbol.upper())
            .order_by(desc(CommodityPrice.timestamp))
            .limit(1)
        )
        price = result.scalar_one_or_none()
        current_price = float(price.price) if price else 0
    
    if current_price == 0:
        current_price = 4775.0
    
    return await engine.run_full_risk_analysis(symbol.upper(), current_price)


@router.get("/var/{symbol}")
async def get_var(symbol: str):
    """Get VaR calculation"""
    from core.services.risk_engine import get_risk_engine
    
    engine = await get_risk_engine()
    return await engine.var_calculation(symbol.upper())


@router.get("/monte-carlo/{symbol}")
async def get_monte_carlo(
    symbol: str,
    price: float = Query(0),
    days: int = Query(30)
):
    """Get Monte Carlo simulation"""
    from core.services.risk_engine import get_risk_engine
    
    engine = await get_risk_engine()
    
    if price == 0:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice
        from sqlalchemy import select, desc
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CommodityPrice)
                .where(CommodityPrice.symbol == symbol.upper())
                .order_by(desc(CommodityPrice.timestamp))
                .limit(1)
            )
            p = result.scalar_one_or_none()
            price = float(p.price) if p else 4775.0
    
    return await engine.monte_carlo_simulation(symbol.upper(), price, days)


@router.get("/stress/{symbol}")
async def get_stress_test(symbol: str):
    """Get stress test scenarios"""
    from core.services.risk_engine import get_risk_engine
    
    engine = await get_risk_engine()
    return await engine.stress_test(symbol.upper())


@router.get("/portfolio")
async def get_portfolio_risk(
    positions: str = Query(..., description="JSON array of positions")
):
    """Get portfolio VaR"""
    import json
    
    from core.services.risk_engine import get_risk_engine
    
    engine = await get_risk_engine()
    
    try:
        pos_list = json.loads(positions)
    except:
        pos_list = []
    
    return await engine.portfolio_var(pos_list)


@router.get("/greeks")
async def get_greeks(
    symbol: str = Query(...),
    strike: float = Query(...),
    expiry: str = Query(...),
    option_type: str = Query("CE")
):
    """Calculate options Greeks"""
    from core.services.risk_engine import get_risk_engine
    from datetime import datetime
    
    engine = await get_risk_engine()
    
    try:
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
    except:
        from datetime import timedelta
        expiry_date = datetime.now() + timedelta(days=30)
    
    return await engine.options_greeks(
        symbol.upper(), strike, expiry_date, option_type
    )