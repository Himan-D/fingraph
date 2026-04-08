from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.post("/query")
async def agent_query(
    query: str = Query(..., description="Natural language query"),
):
    """Process natural language query through AI agent"""
    from core.services.agent import process_agent_query

    return await process_agent_query(query)


@router.get("/overview")
async def get_market_overview():
    """Get complete market overview"""
    from core.services.agent import get_agent_market_overview

    return await get_agent_market_overview()


@router.post("/gds")
async def run_gds_analysis(
    query: str = Query(..., description="GDS analysis query"),
):
    """Run GDS graph analysis"""
    from core.services.agent import FinGraphAgent

    agent = FinGraphAgent()
    return await agent.run_gds_analysis(query)


@router.get("/commodity/{commodity}")
async def get_commodity_analysis(
    commodity: str,
    timeframe: str = Query("7days", regex="^(today|7days|30days|365days)$"),
):
    """Get complete commodity analysis"""
    from core.services.agent import FinGraphAgent

    agent = FinGraphAgent()

    query = f"What's happening with {commodity} in last {timeframe}"
    return await agent.understand_and_execute(query)


@router.get("/sentiment")
async def get_sentiment_analysis(
    entity: Optional[str] = None,
    timeframe: str = Query("7days"),
):
    """Get sentiment analysis"""
    from core.services.agent import FinGraphAgent

    agent = FinGraphAgent()

    query = f"Show me sentiment for {entity or 'all commodities'}"
    return await agent.understand_and_execute(query)


@router.get("/predict/{entity}")
async def get_prediction(
    entity: str,
    entity_type: str = Query("commodity", regex="^(commodity|stock)$"),
):
    """Get prediction for entity"""
    from core.services.commodity_prediction import CommodityPredictionModel
    from core.services.prediction import PredictionModel

    if entity_type == "commodity":
        model = CommodityPredictionModel()
        return await model.predict(entity)
    else:
        model = PredictionModel()
        return await model.predict(entity)


@router.get("/recommendations")
async def get_recommendations():
    """Get market recommendations"""
    from core.services.commodity_prediction import CommodityPredictionModel
    from core.services.prediction import PredictionModel

    commodity_model = CommodityPredictionModel()
    stock_model = PredictionModel()

    return {
        "commodities": await commodity_model.get_market_summary(),
        "stocks": await stock_model.get_recommendations(),
    }


@router.get("/gds/algorithms")
async def list_gds_algorithms():
    """List available GDS algorithms"""
    from core.services.agent import GDSQueryGenerator

    generator = GDSQueryGenerator()

    return {
        "algorithms": [
            {
                "name": algo,
                "description": info["description"],
                "use_cases": info["use_cases"],
            }
            for algo, info in generator.ALGORITHMS.items()
        ]
    }


@router.get("/data-sources")
async def list_data_sources():
    """List available data sources"""
    from core.services.agent import DataSourceAgent

    agent = DataSourceAgent()

    return {
        "data_sources": agent.sources,
        "commodities": list(agent.sources.keys()),
    }
