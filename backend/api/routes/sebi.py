from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random

router = APIRouter()


class SebiFiling(BaseModel):
    id: int
    company: str
    symbol: Optional[str]
    filing_type: str
    description: str
    date: str
    amount: Optional[float]


class BulkDeal(BaseModel):
    id: int
    date: str
    symbol: str
    buyer: str
    seller: str
    quantity: int
    price: float
    value: float


class CircuitBreaker(BaseModel):
    index: str
    name: str
    upper_limit: float
    lower_limit: float
    current_value: float
    change_percent: float


MOCK_FILINGS = [
    {
        "id": 1,
        "company": "Reliance Industries",
        "symbol": "RELIANCE",
        "filing_type": "Insider Trading",
        "description": "Promoter sold 1.5% stake",
        "date": "2026-03-28",
        "amount": 25000,
    },
    {
        "id": 2,
        "company": "Tata Motors",
        "symbol": "TATAMOTORS",
        "filing_type": "FPO",
        "description": "Follow-on public offer of ₹10,000 Cr",
        "date": "2026-03-27",
        "amount": 10000,
    },
    {
        "id": 3,
        "company": "Infosys",
        "symbol": "INFY",
        "filing_type": "Buyback",
        "description": "Board approved ₹9,200 Cr buyback",
        "date": "2026-03-26",
        "amount": 9200,
    },
    {
        "id": 4,
        "company": "HDFC Bank",
        "symbol": "HDFCBANK",
        "filing_type": "Merger",
        "description": "Merger with HDFC completes",
        "date": "2026-03-25",
        "amount": None,
    },
    {
        "id": 5,
        "company": "Adani Power",
        "symbol": "ADANIPOWER",
        "filing_type": "Insider Trading",
        "description": "Promoter increased holding by 2%",
        "date": "2026-03-24",
        "amount": 5000,
    },
]

MOCK_BULK_DEALS = [
    {
        "id": 1,
        "date": "2026-03-28",
        "symbol": "RELIANCE",
        "buyer": "FII",
        "seller": "DII",
        "quantity": 5000000,
        "price": 1592.30,
        "value": 796.15,
    },
    {
        "id": 2,
        "date": "2026-03-28",
        "symbol": "TCS",
        "buyer": "Mutual Fund",
        "seller": "Promoter",
        "quantity": 1000000,
        "price": 4473.90,
        "value": 447.39,
    },
    {
        "id": 3,
        "date": "2026-03-28",
        "symbol": "INFY",
        "buyer": "FII",
        "seller": "Mutual Fund",
        "quantity": 2000000,
        "price": 1999.70,
        "value": 399.94,
    },
    {
        "id": 4,
        "date": "2026-03-27",
        "symbol": "HDFCBANK",
        "buyer": "DII",
        "seller": "FII",
        "quantity": 3000000,
        "price": 1685.40,
        "value": 505.62,
    },
    {
        "id": 5,
        "date": "2026-03-27",
        "symbol": "SBIN",
        "buyer": "FII",
        "seller": "Government",
        "quantity": 10000000,
        "price": 725.80,
        "value": 725.80,
    },
]

MOCK_CIRCUIT_BREAKERS = [
    {
        "index": "NIFTY50",
        "name": "Nifty 50",
        "upper_limit": 23956.03,
        "lower_limit": 21674.49,
        "current_value": 22815.26,
        "change_percent": 1.63,
    },
    {
        "index": "BANKNIFTY",
        "name": "Bank Nifty",
        "upper_limit": 50946.53,
        "lower_limit": 46094.48,
        "current_value": 48520.50,
        "change_percent": 0.87,
    },
    {
        "index": "NIFTYIT",
        "name": "Nifty IT",
        "upper_limit": 37642.92,
        "lower_limit": 34057.88,
        "current_value": 35850.40,
        "change_percent": -0.35,
    },
    {
        "index": "NIFTYFMCG",
        "name": "Nifty FMCG",
        "upper_limit": 55493.13,
        "lower_limit": 50208.07,
        "current_value": 52850.60,
        "change_percent": 0.24,
    },
]


@router.get("/filings")
async def get_sebi_filings(limit: int = 20):
    """Get latest SEBI filings (insider trading, FPOs, buybacks)"""
    return {
        "success": True,
        "data": MOCK_FILINGS[:limit],
        "source": "SEBI",
    }


@router.get("/bulk-deals")
async def get_bulk_deals(limit: int = 20):
    """Get bulk/block deals from NSE/BSE"""
    return {
        "success": True,
        "data": MOCK_BULK_DEALS[:limit],
        "source": "NSE/BSE",
    }


@router.get("/circuit-breakers")
async def get_circuit_breakers():
    """Get circuit breaker levels for indices"""
    return {
        "success": True,
        "data": MOCK_CIRCUIT_BREAKERS,
        "source": "NSE",
    }


@router.get("/circuit-breakers/{index}")
async def get_circuit_breaker(index: str):
    """Get circuit breaker for specific index"""
    index_upper = index.upper()
    for cb in MOCK_CIRCUIT_BREAKERS:
        if cb["index"].upper() == index_upper or index_upper in cb[
            "name"
        ].upper().replace(" ", ""):
            return {"success": True, "data": cb}

    return {"success": False, "error": "Index not found"}


@router.get("/compliance")
async def get_compliance_updates():
    """Get SEBI compliance and regulatory updates"""
    updates = [
        {
            "date": "2026-03-28",
            "type": "Circular",
            "title": "T+1 settlement for SME stocks",
            "description": "SEBI mandates T+1 settlement for SME segment effective April 1, 2026",
        },
        {
            "date": "2026-03-27",
            "type": "Order",
            "title": "Penalty on Karvy Stock Broking",
            "description": "SEBI imposes ₹5 Cr penalty for misappropriation of client securities",
        },
        {
            "date": "2026-03-26",
            "type": "Circular",
            "title": "Enhanced disclosure norms",
            "description": "Listed companies must disclose promoter pledge within 24 hours",
        },
        {
            "date": "2026-03-25",
            "type": "Notification",
            "title": "Demat account rules",
            "description": "New rules for demat account opening and maintenance",
        },
        {
            "date": "2026-03-24",
            "type": "Order",
            "title": "Insider trading case - Satyam",
            "description": "SEBI concludes 15-year case with ₹200 Cr settlement",
        },
    ]
    return {"success": True, "data": updates, "source": "SEBI"}


@router.get("/market-surveillance")
async def get_market_surveillance():
    """Get market surveillance actions"""
    return {
        "success": True,
        "data": [
            {
                "action": "Cold Ring",
                "stocks": ["XYZ", "ABC"],
                "reason": "Unusual volume",
                "date": "2026-03-28",
            },
            {
                "action": "UC Upper",
                "stocks": ["RELIANCE"],
                "reason": "Circuit triggered",
                "date": "2026-03-27",
            },
            {
                "action": "Short-selling restriction",
                "stocks": ["TATAMOTORS", "MARUTI"],
                "reason": "High volatility",
                "date": "2026-03-26",
            },
        ],
        "source": "NSE/BSE",
    }


@router.get("/fpi-investments")
async def get_fpi_investments():
    """Get FPI (Foreign Portfolio Investor) investment data"""
    return {
        "success": True,
        "data": {
            "date": "2026-03-28",
            "net_buying": 2450.50,
            "net_selling": 1800.25,
            "net_investment": 650.25,
            "top_buyers": ["HDFCBANK", "RELIANCE", "TCS"],
            "top_sellers": ["INFY", "SBIN", "ICICIBANK"],
        },
        "source": "NSE",
    }


@router.get("/promoter-pledge")
async def get_promoter_pledge(symbol: str = None):
    """Get promoter pledge data"""
    pledges = [
        {
            "symbol": "RELIANCE",
            "company": "Reliance Industries",
            "pledged_percent": 0.5,
            "previous": 0.8,
            "change": -0.3,
            "date": "2026-03-28",
        },
        {
            "symbol": "TATAMOTORS",
            "company": "Tata Motors",
            "pledged_percent": 4.2,
            "previous": 5.1,
            "change": -0.9,
            "date": "2026-03-28",
        },
        {
            "symbol": "ADANIENT",
            "company": "Adani Enterprises",
            "pledged_percent": 12.5,
            "previous": 14.2,
            "change": -1.7,
            "date": "2026-03-27",
        },
        {
            "symbol": "DHFL",
            "company": "Dewan Housing Finance",
            "pledged_percent": 85.2,
            "previous": 88.5,
            "change": -3.3,
            "date": "2026-03-26",
        },
        {
            "symbol": "INFY",
            "company": "Infosys",
            "pledged_percent": 0.1,
            "previous": 0.1,
            "change": 0.0,
            "date": "2026-03-25",
        },
    ]

    if symbol:
        symbol = symbol.upper()
        for pledge in pledges:
            if pledge["symbol"].upper() == symbol:
                return {"success": True, "data": pledge}
        return {"success": False, "error": "Symbol not found"}

    return {"success": True, "data": pledges, "source": "SEBI"}
