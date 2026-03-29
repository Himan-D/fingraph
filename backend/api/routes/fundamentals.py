from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime
import random

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

    if symbol in SAMPLE_FUNDAMENTALS:
        return {"success": True, "data": SAMPLE_FUNDAMENTALS[symbol]}

    return {
        "success": True,
        "data": {"symbol": symbol, "name": f"{symbol} Ltd", "sector": "Other"},
    }


@router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str):
    """Get financial ratios and metrics"""
    symbol = symbol.upper()

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
                "book_value": data.get("book_value"),
                "market_cap": data.get("market_cap"),
            },
        }

    # Generate placeholder
    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "pe": round(random.uniform(10, 40), 2),
            "pb": round(random.uniform(1, 10), 2),
            "roe": round(random.uniform(5, 30), 2),
            "roce": round(random.uniform(8, 35), 2),
            "debt_equity": round(random.uniform(0, 1.5), 2),
            "dividend_yield": round(random.uniform(0, 3), 2),
            "eps": round(random.uniform(10, 100), 2),
            "book_value": round(random.uniform(50, 500), 2),
            "market_cap": round(random.uniform(10000, 500000), 2),
        },
    }


@router.get("/quarterly/{symbol}")
async def get_quarterly(symbol: str, limit: int = 8):
    """Get quarterly results"""
    symbol = symbol.upper()

    quarters = [
        "Q3 2025",
        "Q2 2025",
        "Q1 2025",
        "Q4 2024",
        "Q3 2024",
        "Q2 2024",
        "Q1 2024",
        "Q4 2023",
    ]
    results = []

    base_revenue = 100000
    base_profit = 10000

    if symbol in SAMPLE_FUNDAMENTALS:
        base_revenue = SAMPLE_FUNDAMENTALS[symbol].get("revenue", 100000) / 4
        base_profit = SAMPLE_FUNDAMENTALS[symbol].get("profit", 10000) / 4

    for i, quarter in enumerate(quarters[:limit]):
        growth = 1 - i * 0.05  # Decreasing growth
        results.append(
            {
                "quarter": quarter,
                "revenue": round(base_revenue * growth * random.uniform(0.9, 1.1), 2),
                "profit": round(base_profit * growth * random.uniform(0.85, 1.15), 2),
                "eps": round(
                    (base_profit * growth) / 100 * random.uniform(0.9, 1.1), 2
                ),
                "growth": round(random.uniform(-5, 15), 2) if i > 0 else 0,
            }
        )

    return {"success": True, "data": results}


@router.get("/shareholding/{symbol}")
async def get_shareholding(symbol: str, limit: int = 4):
    """Get shareholding pattern"""
    symbol = symbol.upper()

    if symbol in SAMPLE_FUNDAMENTALS:
        data = SAMPLE_FUNDAMENTALS[symbol]
        promoter = data.get("promoter_holding", 50)
        fii = data.get("fii_holding", 20)
        dii = data.get("dii_holding", 15)
    else:
        promoter = random.uniform(30, 75)
        fii = random.uniform(10, 40)
        dii = random.uniform(10, 25)

    public = 100 - promoter - fii - dii

    results = [
        {
            "quarter": "Q3 2025",
            "promoter": promoter,
            "fii": fii,
            "dii": dii,
            "public": public,
        },
        {
            "quarter": "Q2 2025",
            "promoter": promoter + random.uniform(-0.5, 0.5),
            "fii": fii + random.uniform(-1, 1),
            "dii": dii + random.uniform(-0.5, 0.5),
            "public": public,
        },
        {
            "quarter": "Q1 2025",
            "promoter": promoter + random.uniform(-1, 1),
            "fii": fii + random.uniform(-2, 2),
            "dii": dii + random.uniform(-1, 1),
            "public": public,
        },
        {
            "quarter": "Q4 2024",
            "promoter": promoter + random.uniform(-1.5, 1.5),
            "fii": fii + random.uniform(-3, 3),
            "dii": dii + random.uniform(-1.5, 1.5),
            "public": public,
        },
    ]

    return {"success": True, "data": results[:limit]}


@router.get("/deals/{symbol}")
async def get_deals(symbol: str):
    """Get bulk/block deals"""
    symbol = symbol.upper()

    deals = []
    for i in range(5):
        deal_type = random.choice(["BULK", "BLOCK"])
        is_buy = random.choice([True, False])

        deals.append(
            {
                "date": f"2025-0{random.randint(1, 3)}-{random.randint(10, 28)}",
                "type": deal_type,
                "buyer": f"FII_{random.randint(100, 999)}"
                if is_buy
                else f"Promoter_{symbol}",
                "seller": f"Promoter_{symbol}"
                if is_buy
                else f"FII_{random.randint(100, 999)}",
                "quantity": random.randint(100000, 5000000),
                "price": random.randint(500, 5000),
                "value": random.randint(10000000, 1000000000),
            }
        )

    return {"success": True, "data": deals}


@router.get("/mf-holdings/{symbol}")
async def get_mf_holdings(symbol: str):
    """Get mutual fund holdings"""
    symbol = symbol.upper()

    mfs = [
        "HDFC MF",
        "ICICI Prudential MF",
        "SBI MF",
        "Axis MF",
        "Kotak MF",
        "Mirae Asset MF",
    ]

    holdings = []
    for mf in mfs[:5]:
        holdings.append(
            {
                "mf_name": mf,
                "quantity": random.randint(1000000, 50000000),
                "change": random.randint(-500000, 2000000),
                "quarter": "Q3 2025",
            }
        )

    return {"success": True, "data": holdings}


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
