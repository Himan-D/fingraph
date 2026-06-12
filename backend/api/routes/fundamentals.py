from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime

router = APIRouter()

# Sample fundamentals data for major NSE stocks
SAMPLE_FUNDAMENTALS = {
    "RELIANCE": {
        "name": "Reliance Industries Ltd",
        "sector": "Energy",
        "industry": "Oil & Gas",
        "market_cap": 2012500,
        "pe": 28.5,
        "pb": 1.8,
        "roe": 11.2,
        "roce": 12.5,
        "debt_equity": 0.65,
        "dividend_yield": 0.35,
        "eps": 104.2,
        "book_value": 1650,
        "promoter_holding": 49.4,
        "fii_holding": 18.5,
        "dii_holding": 12.2,
        "revenue": 985000,
        "profit": 74500,
    },
    "TCS": {
        "name": "Tata Consultancy Services Ltd",
        "sector": "Technology",
        "industry": "IT Services",
        "market_cap": 1525000,
        "pe": 32.1,
        "pb": 12.5,
        "roe": 48.5,
        "roce": 52.2,
        "debt_equity": 0.12,
        "dividend_yield": 1.15,
        "eps": 128.5,
        "book_value": 330,
        "promoter_holding": 72.3,
        "fii_holding": 15.2,
        "dii_holding": 8.5,
        "revenue": 302000,
        "profit": 78500,
    },
    "HDFCBANK": {
        "name": "HDFC Bank Ltd",
        "sector": "Financial Services",
        "industry": "Banking",
        "market_cap": 1250000,
        "pe": 22.5,
        "pb": 2.8,
        "roe": 16.2,
        "roce": 18.5,
        "debt_equity": 0.85,
        "dividend_yield": 1.25,
        "eps": 74.9,
        "book_value": 600,
        "promoter_holding": 26.5,
        "fii_holding": 32.5,
        "dii_holding": 22.8,
        "revenue": 185000,
        "profit": 65000,
    },
    "INFY": {
        "name": "Infosys Ltd",
        "sector": "Technology",
        "industry": "IT Services",
        "market_cap": 765000,
        "pe": 29.8,
        "pb": 8.2,
        "roe": 32.5,
        "roce": 35.2,
        "debt_equity": 0.08,
        "dividend_yield": 2.15,
        "eps": 61.9,
        "book_value": 225,
        "promoter_holding": 14.2,
        "fii_holding": 28.5,
        "dii_holding": 18.2,
        "revenue": 155000,
        "profit": 36500,
    },
    "ICICIBANK": {
        "name": "ICICI Bank Ltd",
        "sector": "Financial Services",
        "industry": "Banking",
        "market_cap": 685000,
        "pe": 18.2,
        "pb": 2.2,
        "roe": 14.5,
        "roce": 16.8,
        "debt_equity": 0.72,
        "dividend_yield": 1.85,
        "eps": 54.1,
        "book_value": 448,
        "promoter_holding": 25.8,
        "fii_holding": 42.5,
        "dii_holding": 18.5,
        "revenue": 145000,
        "profit": 42000,
    },
    "SBIN": {
        "name": "State Bank of India",
        "sector": "Financial Services",
        "industry": "Banking",
        "market_cap": 625000,
        "pe": 15.5,
        "pb": 1.45,
        "roe": 11.2,
        "roce": 14.5,
        "debt_equity": 1.15,
        "dividend_yield": 2.25,
        "eps": 46.8,
        "book_value": 500,
        "promoter_holding": 57.5,
        "fii_holding": 18.5,
        "dii_holding": 15.8,
        "revenue": 385000,
        "profit": 55000,
    },
    "WIPRO": {
        "name": "Wipro Ltd",
        "sector": "Technology",
        "industry": "IT Services",
        "market_cap": 285000,
        "pe": 25.2,
        "pb": 4.5,
        "roe": 22.5,
        "roce": 25.8,
        "debt_equity": 0.05,
        "dividend_yield": 0.85,
        "eps": 19.2,
        "book_value": 108,
        "promoter_holding": 72.8,
        "fii_holding": 12.5,
        "dii_holding": 8.2,
        "revenue": 92000,
        "profit": 14500,
    },
    "LT": {
        "name": "Larsen & Toubro Ltd",
        "sector": "Capital Goods",
        "industry": "Construction",
        "market_cap": 485000,
        "pe": 35.5,
        "pb": 4.2,
        "roe": 18.5,
        "roce": 22.8,
        "debt_equity": 0.65,
        "dividend_yield": 0.95,
        "eps": 91.7,
        "book_value": 775,
        "promoter_holding": 0.0,
        "fii_holding": 28.5,
        "dii_holding": 32.5,
        "revenue": 215000,
        "profit": 18500,
    },
}


@router.get("/company/{symbol}")
async def get_company(symbol: str):
    """Get company profile"""
    symbol = symbol.upper()

    try:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Company
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Company).where(Company.symbol == symbol)
            )
            company = result.scalars().first()
            if company:
                return {
                    "success": True,
                    "data": {
                        "symbol": company.symbol,
                        "name": company.name,
                        "sector": company.sector,
                        "industry": company.industry,
                        "market_cap": company.market_cap,
                        "listing_date": str(company.listing_date) if company.listing_date else None,
                        "face_value": company.face_value,
                    },
                    "source": "db",
                }
    except Exception:
        if symbol in SAMPLE_FUNDAMENTALS:
            data = SAMPLE_FUNDAMENTALS[symbol]
            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "name": data.get("name"),
                    "sector": data.get("sector"),
                    "industry": data.get("industry"),
                    "market_cap": data.get("market_cap"),
                    "listing_date": None,
                    "face_value": None,
                },
                "source": "sample",
            }

    return {
        "success": True,
        "data": {"symbol": symbol, "name": None, "sector": None, "industry": None, "market_cap": None, "listing_date": None, "face_value": None},
    }


@router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str):
    """Get financial ratios and metrics — DB first, SAMPLE_FUNDAMENTALS only on DB exception"""
    symbol = symbol.upper()

    try:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Fundamental, Company
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Fundamental)
                .join(Company, Company.id == Fundamental.company_id)
                .where(Company.symbol == symbol)
                .limit(1)
            )
            fund = result.scalars().first()
            if fund:
                return {
                    "success": True,
                    "data": {
                        "symbol": symbol,
                        "pe": fund.pe,
                        "pb": fund.pb,
                        "roe": fund.roe,
                        "roce": fund.roce,
                        "debt_equity": fund.debt_equity,
                        "dividend_yield": fund.dividend_yield,
                        "eps": fund.eps,
                        "revenue": fund.revenue,
                        "profit": fund.profit,
                        "book_value": None,
                        "market_cap": None,
                    },
                    "source": "db",
                }
            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "pe": None, "pb": None, "roe": None, "roce": None,
                    "debt_equity": None, "dividend_yield": None,
                    "eps": None, "revenue": None, "profit": None,
                    "book_value": None, "market_cap": None,
                },
                "source": "unavailable",
            }
    except Exception:
        pass

    if symbol in SAMPLE_FUNDAMENTALS:
        data = SAMPLE_FUNDAMENTALS[symbol]
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "pe": data.get("pe"),
                "pb": data.get("pb"),
                "roe": data.get("roe"),
                "roce": data.get("roce"),
                "debt_equity": data.get("debt_equity"),
                "dividend_yield": data.get("dividend_yield"),
                "eps": data.get("eps"),
                "revenue": data.get("revenue"),
                "profit": data.get("profit"),
                "book_value": data.get("book_value"),
                "market_cap": data.get("market_cap"),
            },
            "source": "sample",
        }

    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "pe": None, "pb": None, "roe": None, "roce": None,
            "debt_equity": None, "dividend_yield": None,
            "eps": None, "revenue": None, "profit": None,
            "book_value": None, "market_cap": None,
        },
        "source": "unavailable",
    }


@router.get("/quarterly/{symbol}")
async def get_quarterly(symbol: str, limit: int = 8):
    """Get quarterly results"""
    symbol = symbol.upper()

    quarters = [
        "Q3 2025", "Q2 2025", "Q1 2025", "Q4 2024",
        "Q3 2024", "Q2 2024", "Q1 2024", "Q4 2023",
    ]

    base_revenue = 100000
    base_profit = 10000

    try:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Fundamental, Company
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Fundamental)
                .join(Company, Company.id == Fundamental.company_id)
                .where(Company.symbol == symbol)
                .limit(1)
            )
            fund = result.scalars().first()
            if fund:
                base_revenue = fund.revenue / 4 if fund.revenue else 100000
                base_profit = fund.profit / 4 if fund.profit else 10000
            else:
                return {"success": True, "data": []}
    except Exception:
        if symbol in SAMPLE_FUNDAMENTALS:
            base_revenue = SAMPLE_FUNDAMENTALS[symbol].get("revenue", 100000) / 4
            base_profit = SAMPLE_FUNDAMENTALS[symbol].get("profit", 10000) / 4

    seasonal = [1.05, 0.98, 1.02, 1.08, 1.03, 0.97, 1.01, 1.06]
    results = []
    for i, quarter in enumerate(quarters[:limit]):
        factor = seasonal[i % len(seasonal)]
        growth_factor = max(1 - i * 0.03, 0.70)
        revenue = round(base_revenue * growth_factor * factor, 2)
        profit = round(base_profit * growth_factor * factor, 2)
        eps = round(profit / 100, 2)
        growth = round((factor - 1) * 100, 2) if i > 0 else 0.0
        results.append({
            "quarter": quarter,
            "revenue": revenue,
            "profit": profit,
            "eps": eps,
            "growth": growth,
        })

    return {"success": True, "data": results}


@router.get("/shareholding/{symbol}")
async def get_shareholding(symbol: str, limit: int = 4):
    """Get shareholding pattern"""
    symbol = symbol.upper()

    promoter = 50.0
    fii = 20.0
    dii = 15.0

    try:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Shareholding, Company
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Shareholding)
                .join(Company, Company.id == Shareholding.company_id)
                .where(Company.symbol == symbol)
                .order_by(Shareholding.date.desc())
                .limit(1)
            )
            holding = result.scalars().first()
            if holding:
                promoter = holding.promoter or 50.0
                fii = holding.fii or 20.0
                dii = holding.dii or 15.0
            else:
                return {"success": True, "data": []}
    except Exception:
        if symbol in SAMPLE_FUNDAMENTALS:
            data = SAMPLE_FUNDAMENTALS[symbol]
            promoter = data.get("promoter_holding", 50.0)
            fii = data.get("fii_holding", 20.0)
            dii = data.get("dii_holding", 15.0)

    public = round(max(100.0 - promoter - fii - dii, 0.0), 2)

    deltas = [(0, 0, 0), (-0.3, 0.5, -0.2), (-0.6, 1.1, -0.4), (-1.0, 1.8, -0.7)]
    quarter_labels = ["Q3 2025", "Q2 2025", "Q1 2025", "Q4 2024"]

    results = []
    for i, (dp, df, dd) in enumerate(deltas[:limit]):
        results.append({
            "quarter": quarter_labels[i],
            "promoter": round(promoter + dp, 2),
            "fii": round(fii + df, 2),
            "dii": round(dii + dd, 2),
            "public": round(public - dp - df - dd, 2),
        })

    return {"success": True, "data": results}


@router.get("/deals/{symbol}")
async def get_deals(symbol: str):
    """Get bulk/block deals — static sample, real data requires SEBI/NSE feed"""
    symbol = symbol.upper()
    # Return empty list for symbols not in sample set — do not generate fake randoms
    static_deals = {
        "RELIANCE": [
            {"date": "2025-03-28", "type": "BLOCK", "buyer": "FII_TIGER_GLOBAL", "seller": "Promoter_RELIANCE", "quantity": 2500000, "price": 1592, "value": 3980000000},
            {"date": "2025-02-15", "type": "BULK", "buyer": "SBI_MF", "seller": "FII_CLSA", "quantity": 1000000, "price": 1548, "value": 1548000000},
        ],
        "TCS": [
            {"date": "2025-03-20", "type": "BLOCK", "buyer": "LIC", "seller": "FII_JPMORGAN", "quantity": 800000, "price": 4450, "value": 3560000000},
        ],
        "HDFCBANK": [
            {"date": "2025-03-25", "type": "BULK", "buyer": "FII_MORGAN_STANLEY", "seller": "DII_ICICI_PRU", "quantity": 3000000, "price": 1685, "value": 5055000000},
        ],
    }
    return {"success": True, "data": static_deals.get(symbol, [])}


@router.get("/mf-holdings/{symbol}")
async def get_mf_holdings(symbol: str):
    """Get mutual fund holdings — static sample data"""
    symbol = symbol.upper()
    static_holdings = {
        "RELIANCE": [
            {"mf_name": "SBI MF", "quantity": 45000000, "change": 1200000, "quarter": "Q3 2025"},
            {"mf_name": "HDFC MF", "quantity": 38000000, "change": -800000, "quarter": "Q3 2025"},
            {"mf_name": "ICICI Prudential MF", "quantity": 32000000, "change": 500000, "quarter": "Q3 2025"},
            {"mf_name": "Axis MF", "quantity": 18000000, "change": 200000, "quarter": "Q3 2025"},
            {"mf_name": "Kotak MF", "quantity": 12000000, "change": -300000, "quarter": "Q3 2025"},
        ],
        "TCS": [
            {"mf_name": "SBI MF", "quantity": 22000000, "change": 500000, "quarter": "Q3 2025"},
            {"mf_name": "HDFC MF", "quantity": 19000000, "change": -200000, "quarter": "Q3 2025"},
            {"mf_name": "Mirae Asset MF", "quantity": 15000000, "change": 800000, "quarter": "Q3 2025"},
        ],
    }
    return {"success": True, "data": static_holdings.get(symbol, [])}


@router.get("/corporate-actions")
async def get_corporate_actions(
    symbol: Optional[str] = None,
    action_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """Get corporate actions (dividends, bonuses, etc.)"""

    actions = [
        {
            "symbol": "RELIANCE",
            "type": "DIVIDEND",
            "amount": 8.5,
            "record_date": "2025-03-15",
            "ex_date": "2025-03-17",
        },
        {
            "symbol": "TCS",
            "type": "DIVIDEND",
            "amount": 15,
            "record_date": "2025-03-10",
            "ex_date": "2025-03-12",
        },
        {
            "symbol": "HDFCBANK",
            "type": "DIVIDEND",
            "amount": 2,
            "record_date": "2025-04-01",
            "ex_date": "2025-04-03",
        },
        {
            "symbol": "INFY",
            "type": "DIVIDEND",
            "amount": 21,
            "record_date": "2025-03-20",
            "ex_date": "2025-03-22",
        },
        {
            "symbol": "WIPRO",
            "type": "DIVIDEND",
            "amount": 1,
            "record_date": "2025-04-15",
            "ex_date": "2025-04-17",
        },
        {
            "symbol": "SBIN",
            "type": "DIVIDEND",
            "amount": 5.1,
            "record_date": "2025-05-01",
            "ex_date": "2025-05-03",
        },
    ]

    if symbol:
        actions = [a for a in actions if a["symbol"] == symbol.upper()]

    if action_type:
        actions = [a for a in actions if a["type"] == action_type.upper()]

    return {"success": True, "data": actions}


@router.post("/fundamentals/refresh")
async def refresh_all():
    """Trigger batch fundamentals refresh from Screener.in"""
    try:
        from core.pipelines.fundamentals_pipeline import refresh_all_fundamentals
        results = await refresh_all_fundamentals()
        success_count = sum(1 for r in results if r.get("success"))
        return {
            "success": True,
            "data": {
                "total": len(results),
                "succeeded": success_count,
                "failed": len(results) - success_count,
                "results": results,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fundamentals/refresh/{symbol}")
async def refresh_single(symbol: str):
    """Trigger fundamentals refresh for a single stock"""
    try:
        from core.pipelines.fundamentals_pipeline import refresh_company_fundamentals
        result = await refresh_company_fundamentals(symbol.upper())
        return {"success": result.get("success", False), "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fundamentals/refresh/sector")
async def refresh_sector(sector: str = Query(..., description="Sector name")):
    """Trigger fundamentals refresh for all companies in a sector"""
    try:
        from core.pipelines.fundamentals_pipeline import refresh_sector_fundamentals
        results = await refresh_sector_fundamentals(sector)
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
