"""
Trading Signals API Routes

Professional trading signals and recommendations.
"""

from fastapi import APIRouter, Query
from typing import List, Optional

from core.services.signals import signal_service, SignalType

router = APIRouter()


@router.get("/signals/{commodity}")
async def get_signal(commodity: str):
    """Get trading signal for a commodity"""
    return await signal_service.get_signal(commodity)


@router.get("/signals")
async def get_all_signals():
    """Get signals for all commodities"""
    return await signal_service.get_all_signals()


@router.get("/top-picks")
async def get_top_picks(direction: str = Query("buy", regex="^(buy|sell)$")):
    """Get top commodity picks"""
    return await signal_service.get_top_picks(direction)


@router.get("/market-summary")
async def get_market_summary():
    """Get market summary with signals"""
    return await signal_service.get_market_summary()


@router.get("/commodity/{commodity}/analysis")
async def get_commodity_analysis(commodity: str):
    """Get complete commodity analysis with signals"""
    signal = await signal_service.get_signal(commodity)
    return signal
