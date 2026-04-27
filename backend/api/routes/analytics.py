from fastapi import APIRouter, Query
from typing import Optional, List

router = APIRouter()


@router.get("/predict/{symbol}")
async def predict_stock(symbol: str):
    """Get prediction for a single stock"""
    from core.services.prediction import PredictionModel

    model = PredictionModel()
    return await model.predict(symbol)


@router.get("/predict/batch")
async def predict_batch(
    symbols: str = Query("", description="Comma-separated symbols"),
):
    """Get predictions for multiple stocks"""
    from core.services.prediction import PredictionModel

    model = PredictionModel()
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return await model.predict_batch(symbol_list)


@router.get("/recommendations")
async def get_recommendations():
    """Get market recommendations"""
    from core.services.prediction import PredictionModel

    model = PredictionModel()
    return await model.get_recommendations()


@router.get("/predict/graph/{symbol}")
async def predict_with_graph(symbol: str):
    """Get graph-enhanced prediction"""
    from core.services.prediction import GraphEnhancedPrediction

    model = GraphEnhancedPrediction()
    return await model.predict_with_graph(symbol)


@router.get("/predict/graph/batch")
async def predict_graph_batch(
    symbols: str = Query("", description="Comma-separated symbols"),
):
    """Get graph-enhanced predictions"""
    from core.services.prediction import GraphEnhancedPrediction

    model = GraphEnhancedPrediction()
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return await model.predict_with_graph(symbol_list)


@router.get("/predict/event/{event}")
async def event_predictions(event: str):
    """Get predictions for stocks affected by an event"""
    from core.services.prediction import GraphEnhancedPrediction

    model = GraphEnhancedPrediction()
    return await model.event_driven_predictions(event)


@router.get("/top-picks")
async def get_top_picks(
    direction: str = Query("bullish", regex="^(bullish|bearish)$"),
    limit: int = Query(10, le=50),
):
    """Get top stock picks"""
    from core.services.prediction import PredictionModel

    model = PredictionModel()
    return await model.get_top_picks(direction, limit)


@router.get("/gds/run")
async def run_gds_analytics():
    """Run full GDS analytics"""
    from core.services.gds_analytics import get_gds_analytics

    gds = await get_gds_analytics()
    return await gds.run_full_analytics()


@router.get("/gds/pagerank")
async def get_pagerank():
    """Get PageRank influencers"""
    from core.services.gds_analytics import get_gds_analytics

    gds = await get_gds_analytics()
    return await gds.get_top_influencers()


@router.get("/gds/communities")
async def get_communities():
    """Get detected communities"""
    from core.services.gds_analytics import get_gds_analytics

    gds = await get_gds_analytics()
    return await gds.get_communities()


@router.get("/gds/bridges")
async def get_bridge_entities():
    """Get key bridge entities"""
    from core.services.gds_analytics import get_gds_analytics

    gds = await get_gds_analytics()
    return await gds.get_key_bridges()


@router.get("/gds/sentiment-flow")
async def get_sentiment_flow():
    """Get sentiment flow analysis"""
    from core.services.gds_analytics import get_gds_analytics

    gds = await get_gds_analytics()
    return await gds.sentiment_flow_analysis()


@router.post("/gds/correlate")
async def correlate_events(
    symbols: List[str] = Query(..., description="List of symbols"),
):
    """Find event correlations between stocks"""
    from core.services.gds_analytics import get_gds_analytics

    gds = await get_gds_analytics()
    return await gds.event_correlation(symbols)


@router.get("/gds/project")
async def create_graph_project():
    """Create GDS graph projection"""
    from core.services.gds_analytics import get_gds_analytics

    gds = await get_gds_analytics()
    return await gds.create_graph_project()


@router.get("/gds/advanced/spectral")
async def get_spectral_analysis():
    """Get spectral graph theory analysis"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.spectral.compute_spectral_properties()


@router.get("/gds/advanced/fiedler")
async def get_fiedler_analysis():
    """Get Fiedler vector analysis for graph partitioning"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.spectral.fiedler_vector_analysis()


@router.get("/gds/advanced/lead-lag")
async def get_lead_lag_analysis(
    commodities: str = Query("GOLD,SILVER,CRUDEOIL,NATURALGAS,COPPER,ALUMINIUM"),
    days: int = Query(30, le=90),
):
    """Get lead-lag relationships between commodities"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    comm_list = [c.strip().upper() for c in commodities.split(",")]
    return await gds.temporal.compute_lead_lag_matrix(comm_list, days)


@router.get("/gds/advanced/regimes/{symbol}")
async def get_regime_detection(symbol: str):
    """Detect market regime changes for a commodity"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.temporal.detect_regime_changes(symbol.upper())


@router.get("/gds/advanced/causal")
async def get_causal_relationships(
    commodities: str = Query("GOLD,SILVER,CRUDEOIL,NATURALGAS,COPPER,ALUMINIUM"),
):
    """Find Granger causality relationships between commodities"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    comm_list = [c.strip().upper() for c in commodities.split(",")]
    return await gds.causal.find_all_causal_relationships(comm_list)


@router.post("/gds/advanced/granger-test")
async def granger_causality_test(
    cause: str = Query(...), effect: str = Query(...), lag: int = Query(5, le=10)
):
    """Test if cause Granger-causes effect"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.causal.granger_causality_test(cause.upper(), effect.upper(), lag)


@router.get("/gds/advanced/volatility/{symbol}")
async def get_volatility_signature(symbol: str):
    """Compute volatility signature for a commodity"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.volatility.compute_volatility_signature(symbol.upper())


@router.get("/gds/advanced/volatility-clusters")
async def get_volatility_clusters(
    commodities: str = Query("GOLD,SILVER,CRUDEOIL,NATURALGAS,COPPER,ALUMINIUM"),
):
    """Cluster commodities by volatility pattern"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    comm_list = [c.strip().upper() for c in commodities.split(",")]
    return await gds.volatility.cluster_by_volatility_pattern(comm_list)


@router.get("/gds/advanced/graphlets/{symbol}")
async def get_graphlet_signature(symbol: str):
    """Compute local graphlet signature for a commodity"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.graphlets.compute_local_graphlet_signature(symbol.upper())


@router.get("/gds/advanced/anomalies")
async def get_structural_anomalies():
    """Find structural anomalies in commodity network"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.graphlets.find_structural_anomalies()


@router.get("/gds/advanced/risk/{symbol}")
async def get_risk_metrics(symbol: str):
    """Compute VaR and CVaR for a commodity"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.risk.compute_conditional_value_at_risk(symbol.upper())


@router.get("/gds/advanced/systemic-risk")
async def get_systemic_risk():
    """Compute systemic risk metrics for all commodities"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.risk.compute_systemic_risk_metrics()


@router.get("/gds/advanced/comprehensive")
async def get_comprehensive_gds():
    """Run all advanced GDS analytics"""
    from core.services.advanced_gds import get_advanced_gds

    gds = await get_advanced_gds()
    return await gds.comprehensive_analysis()


@router.get("/analytics/summary")
async def get_analytics_summary():
    """Get complete analytics summary"""
    from core.services.gds_analytics import get_gds_analytics
    from core.services.prediction import PredictionModel

    gds = await get_gds_analytics()
    prediction = PredictionModel()

    summary = {
        "influencers": await gds.get_top_influencers(10),
        "communities": await gds.get_communities(5),
        "bridges": await gds.get_key_bridges(10),
        "predictions": await prediction.get_top_picks("bullish", 10),
        "recommendations": await prediction.get_recommendations(),
    }

    return summary
