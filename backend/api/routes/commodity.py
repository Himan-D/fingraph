from fastapi import APIRouter, Query
from typing import Optional, List

router = APIRouter()


@router.get("/prices")
async def get_commodity_prices(
    symbol: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    """Get commodity prices"""
    from core.services.commodity_pipeline import get_commodity_prices as get_prices

    if symbol:
        prices = await get_prices(symbol, days=7)
        return {"symbol": symbol.upper(), "prices": prices}

    from core.services.commodity_pipeline import get_latest_prices

    return await get_latest_prices()


@router.get("/prices/{symbol}")
async def get_symbol_prices(
    symbol: str,
    days: int = Query(7, le=90),
):
    """Get historical prices for a commodity"""
    from core.services.commodity_pipeline import get_commodity_prices

    return await get_commodity_prices(symbol, days)


@router.get("/news")
async def get_commodity_news(
    symbol: Optional[str] = None,
    limit: int = Query(50, le=100),
):
    """Get commodity news"""
    from core.services.commodity_pipeline import get_commodity_news

    return await get_commodity_news(symbol, limit)


@router.get("/news/{symbol}")
async def get_symbol_news(
    symbol: str,
    limit: int = Query(20, le=50),
):
    """Get news for specific commodity"""
    from core.services.commodity_pipeline import get_commodity_news

    return await get_commodity_news(symbol, limit)


@router.get("/sentiment/{commodity}")
async def get_sentiment(
    commodity: str,
    days: int = Query(30, le=90),
):
    """Get sentiment history for commodity"""
    from core.services.commodity_pipeline import get_sentiment_history

    return await get_sentiment_history(commodity, days)


@router.get("/sentiment/latest")
async def get_latest_sentiment(
    commodities: str = Query("", description="Comma-separated commodities"),
):
    """Get latest sentiment for commodities"""
    from core.services.commodity_pipeline import calculate_commodity_sentiment

    comm_list = [c.strip().upper() for c in commodities.split(",") if c.strip()]

    if not comm_list:
        comm_list = ["GOLD", "SILVER", "CRUDEOIL", "NATURALGAS"]

    sentiments = {}
    for comm in comm_list:
        try:
            sentiment = await calculate_commodity_sentiment(comm)
            sentiments[comm] = sentiment
        except Exception as e:
            sentiments[comm] = {"error": str(e)}

    return sentiments


@router.get("/summary")
async def get_market_summary():
    """Get commodity market summary"""
    from core.services.commodity_pipeline import get_commodity_summary

    return await get_commodity_summary()


@router.get("/predict/{commodity}")
async def predict_commodity(commodity: str):
    """Get prediction for a commodity"""
    from core.services.commodity_prediction import CommodityPredictionModel

    model = CommodityPredictionModel()
    return await model.predict(commodity)


@router.get("/predict/batch")
async def predict_batch(
    commodities: str = Query("", description="Comma-separated commodities"),
):
    """Get predictions for multiple commodities"""
    from core.services.commodity_prediction import CommodityPredictionModel

    model = CommodityPredictionModel()
    comm_list = [c.strip().upper() for c in commodities.split(",") if c.strip()]
    return await model.predict_batch(comm_list)


@router.get("/predict/technical/{commodity}")
async def predict_with_technicals(commodity: str):
    """Get technical analysis prediction"""
    from core.services.commodity_prediction import CommodityMLPrediction

    model = CommodityMLPrediction()
    return await model.predict_with_technicals(commodity)


@router.get("/predict/correlation/{commodity}")
async def predict_with_correlation(commodity: str):
    """Get correlation-based prediction"""
    from core.services.commodity_prediction import CommodityMLPrediction

    model = CommodityMLPrediction()
    return await model.predict_with_correlation(commodity)


@router.get("/recommendations")
async def get_recommendations():
    """Get market recommendations"""
    from core.services.commodity_prediction import CommodityPredictionModel

    model = CommodityPredictionModel()
    return await model.get_market_summary()


@router.get("/top-picks")
async def get_top_picks(
    direction: str = Query("bullish", regex="^(bullish|bearish)$"),
    limit: int = Query(5, le=10),
):
    """Get top commodity picks"""
    from core.services.commodity_prediction import CommodityPredictionModel

    model = CommodityPredictionModel()
    return await model.get_top_picks(direction, limit)


@router.get("/gds/network")
async def get_commodity_network():
    """Get commodity network analysis"""
    from core.services.commodity_gds import CommodityGDSAnalytics

    gds = CommodityGDSAnalytics()
    await gds.init()
    return await gds.analyze_commodity_network()


@router.get("/gds/influence")
async def get_influence_ranking():
    """Get commodity influence ranking"""
    from core.services.commodity_gds import CommodityGDSAnalytics

    gds = CommodityGDSAnalytics()
    await gds.init()
    return await gds.commodity_influence_ranking()


@router.get("/gds/related/{commodity}")
async def get_related_commodities(
    commodity: str,
    limit: int = Query(5, le=10),
):
    """Get related commodities"""
    from core.services.commodity_gds import CommodityGDSAnalytics

    gds = CommodityGDSAnalytics()
    await gds.init()
    return await gds.get_related_commodities(commodity, limit)


@router.get("/gds/run")
async def run_gds_analytics():
    """Run complete GDS analytics"""
    from core.services.commodity_gds import CommodityGDSAnalytics

    gds = CommodityGDSAnalytics()
    await gds.init()
    return await gds.run_full_analytics()


@router.post("/pipeline/run")
async def run_pipeline(dry_run: bool = False):
    """Manually trigger commodity pipeline"""
    if dry_run:
        return {"message": "Dry run - no action taken"}

    from core.services.commodity_pipeline import run_pipeline

    await run_pipeline()
    return {"message": "Commodity pipeline executed successfully"}


@router.get("/list")
async def list_commodities():
    """List all tracked commodities"""
    return {
        "commodities": [
            {"symbol": "GOLD", "name": "Gold", "unit": "10 gm", "exchange": "MCX"},
            {"symbol": "SILVER", "name": "Silver", "unit": "1 kg", "exchange": "MCX"},
            {
                "symbol": "CRUDEOIL",
                "name": "Crude Oil",
                "unit": "100 bbl",
                "exchange": "MCX",
            },
            {
                "symbol": "NATURALGAS",
                "name": "Natural Gas",
                "unit": "MMBtu",
                "exchange": "MCX",
            },
            {"symbol": "COPPER", "name": "Copper", "unit": "1 kg", "exchange": "MCX"},
            {
                "symbol": "ALUMINIUM",
                "name": "Aluminium",
                "unit": "1 kg",
                "exchange": "MCX",
            },
            {"symbol": "ZINC", "name": "Zinc", "unit": "1 kg", "exchange": "MCX"},
            {"symbol": "NICKEL", "name": "Nickel", "unit": "1 kg", "exchange": "MCX"},
        ]
    }
