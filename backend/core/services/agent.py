import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import json

logger = logging.getLogger(__name__)

COMMODITY_KEYWORDS = {
    "GOLD": ["gold", "gold rate", "gold price", "xau", "precious metal"],
    "SILVER": ["silver", "silver rate", "silver price", "xag", "white metal"],
    "CRUDEOIL": ["crude oil", "crude", "wti", "brent", "石油", "oil"],
    "NATURALGAS": ["natural gas", "lng", "gas"],
    "COPPER": ["copper", "copper price"],
    "ALUMINIUM": ["aluminum", "aluminium"],
}

STOCK_KEYWORDS = {
    "RELIANCE": ["reliance", "reliance industries"],
    "TCS": ["tcs", "tata consultancy"],
    "INFY": ["infosys", "infy"],
    "HDFCBANK": ["hdfc bank", "hdfc"],
    "ICICIBANK": ["icici bank", "icici"],
    "SBIN": ["sbi", "state bank"],
}


class DataSourceAgent:
    """Agent that understands all data sources"""

    def __init__(self):
        self.sources = {
            "commodity_prices": {
                "table": "commodity_prices",
                "fields": [
                    "commodity_id",
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ],
                "key_field": "commodity_id",
            },
            "commodity_news": {
                "table": "commodity_news",
                "fields": [
                    "headline",
                    "source",
                    "commodities",
                    "published_at",
                    "sentiment",
                ],
                "key_field": "commodities",
            },
            "commodity_sentiment": {
                "table": "commodity_sentiment",
                "fields": [
                    "commodity_symbol",
                    "date",
                    "sentiment_score",
                    "mention_count",
                ],
                "key_field": "commodity_symbol",
            },
            "stock_quotes": {
                "table": "stock_quotes",
                "fields": [
                    "company_id",
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ],
                "key_field": "company_id",
            },
            "news_articles": {
                "table": "news_articles",
                "fields": ["headline", "source", "related_symbols", "published_at"],
                "key_field": "related_symbols",
            },
            "social_sentiment": {
                "table": "social_sentiment",
                "fields": ["symbol", "date", "sentiment_score", "mention_count"],
                "key_field": "symbol",
            },
        }

    def detect_data_type(self, query: str) -> str:
        """Detect what data type the user is asking about"""
        query_lower = query.lower()

        for comm, keywords in COMMODITY_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return "commodity"

        for stock, keywords in STOCK_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return "stock"

        if any(kw in query_lower for kw in ["market", "sensex", "nifty", "index"]):
            return "index"

        if any(
            kw in query_lower
            for kw in ["sentiment", "social", "reddit", "twitter", "opinion"]
        ):
            return "sentiment"

        return "general"

    def detect_entity(self, query: str) -> Optional[str]:
        """Detect specific entity"""
        query_lower = query.lower()

        for comm, keywords in COMMODITY_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return comm

        for stock, keywords in STOCK_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return stock

        return None

    def detect_timeframe(self, query: str) -> str:
        """Detect time frame"""
        query_lower = query.lower()

        if "today" in query_lower or "latest" in query_lower:
            return "today"
        elif "week" in query_lower:
            return "7days"
        elif "month" in query_lower:
            return "30days"
        elif "year" in query_lower:
            return "365days"

        return "7days"


class GDSQueryGenerator:
    """Generates GDS queries based on user intent"""

    ALGORITHMS = {
        "pagerank": {
            "description": "Find most influential entities",
            "use_cases": [
                "influential",
                "important",
                "impact",
                "key players",
                "leaders",
            ],
            "cypher": "CALL gds.pageRank.write('$graph', {writeProperty: 'pagerank', maxIterations: 20})",
        },
        "betweenness": {
            "description": "Find bridge entities connecting communities",
            "use_cases": ["bridge", "connect", "link", "broker", "gateway"],
            "cypher": "CALL gds.betweenness.write('$graph', {writeProperty: 'betweenness'})",
        },
        "louvain": {
            "description": "Detect communities/clusters",
            "use_cases": ["community", "cluster", "group", "segment", "similar"],
            "cypher": "CALL gds.louvain.write('$graph', {writeProperty: 'community', maxIterations: 10})",
        },
        "similarity": {
            "description": "Find similar entities",
            "use_cases": ["similar", "like", "same as", "related to", "compared to"],
            "cypher": "CALL gds.nodeSimilarity.write('$graph', {writeProperty: 'similarity', maxIterations: 10})",
        },
        "wcc": {
            "description": "Find connected components",
            "use_cases": ["connected", "network", "group"],
            "cypher": "CALL gds.wcc.write('$graph', {writeProperty: 'component'})",
        },
    }

    def detect_algorithm(self, query: str) -> List[str]:
        """Detect which GDS algorithm user wants"""
        query_lower = query.lower()

        detected = []
        for algo, info in self.ALGORITHMS.items():
            if any(uc in query_lower for uc in info["use_cases"]):
                detected.append(algo)

        if not detected:
            detected = ["pagerank", "louvain"]

        return detected

    def generate_queries(self, algorithm: str, entity: str = None) -> List[Dict]:
        """Generate Cypher queries for the algorithm"""
        queries = []

        if algorithm == "pagerank":
            queries.append(
                {
                    "name": "page_rank",
                    "cypher": "CALL gds.pageRank.write('finance_graph', {writeProperty: 'pagerank', maxIterations: 20})",
                    "description": "Calculate PageRank for all entities",
                }
            )
            queries.append(
                {
                    "name": "top_influencers",
                    "cypher": "MATCH (n) WHERE n.pagerank IS NOT NULL RETURN labels(n)[0] as type, n.name as name, n.pagerank as score ORDER BY n.pagerank DESC LIMIT 20",
                    "description": "Get top influential entities",
                }
            )

        elif algorithm == "betweenness":
            queries.append(
                {
                    "name": "betweenness_centrality",
                    "cypher": "CALL gds.betweenness.write('finance_graph', {writeProperty: 'betweenness'})",
                    "description": "Calculate betweenness centrality",
                }
            )
            queries.append(
                {
                    "name": "key_bridges",
                    "cypher": "MATCH (n) WHERE n.betweenness IS NOT NULL RETURN n.name as name, n.betweenness as score ORDER BY n.betweenness DESC LIMIT 10",
                    "description": "Get key bridge entities",
                }
            )

        elif algorithm == "louvain":
            queries.append(
                {
                    "name": "community_detection",
                    "cypher": "CALL gds.louvain.write('finance_graph', {writeProperty: 'community', maxIterations: 10})",
                    "description": "Detect communities",
                }
            )
            queries.append(
                {
                    "name": "communities",
                    "cypher": "MATCH (n)-[:AFFECTS|RELEVANT_TO|RELATED_TO]-(m) WHERE n.community IS NOT NULL WITH n.community as community, collect(DISTINCT n.name) as members RETURN community, members ORDER BY size(members) DESC LIMIT 10",
                    "description": "Get detected communities",
                }
            )

        elif algorithm == "similarity":
            queries.append(
                {
                    "name": "node_similarity",
                    "cypher": "CALL gds.nodeSimilarity.write('finance_graph', {writeProperty: 'similarity', maxIterations: 10})",
                    "description": "Calculate node similarity",
                }
            )

        elif algorithm == "wcc":
            queries.append(
                {
                    "name": "weakly_connected",
                    "cypher": "CALL gds.wcc.write('finance_graph', {writeProperty: 'component'})",
                    "description": "Find connected components",
                }
            )

        return queries


class QueryExecutor:
    """Executes queries against databases"""

    async def execute_neo4j(self, cypher: str, params: dict = None) -> List[Dict]:
        """Execute Neo4j query"""
        from db.neo4j_client import get_neo4j

        driver = get_neo4j()
        if not driver:
            return [{"error": "Neo4j not connected"}]

        try:
            async with driver.session() as session:
                result = await session.run(cypher, params or {})
                return await result.data()
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return [{"error": str(e)}]

    async def execute_postgres(self, query: str) -> List[Dict]:
        """Execute PostgreSQL query"""
        from sqlalchemy import text
        from db.postgres import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text(query))
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Postgres query error: {e}")
            return [{"error": str(e)}]


class FinGraphAgent:
    """Main AI Agent for FinGraph - understands and queries all data"""

    def __init__(self):
        self.data_source = DataSourceAgent()
        self.gds_generator = GDSQueryGenerator()
        self.executor = QueryExecutor()

    async def understand_and_execute(self, query: str) -> Dict:
        """Understand user query and execute appropriate data fetch"""

        response = {
            "query": query,
            "understanding": {},
            "data": {},
            "gds_results": {},
            "predictions": {},
            "insights": [],
        }

        data_type = self.data_source.detect_data_type(query)
        entity = self.data_source.detect_entity(query)
        timeframe = self.data_source.detect_timeframe(query)
        algorithms = self.gds_generator.detect_algorithm(query)

        response["understanding"] = {
            "data_type": data_type,
            "entity": entity,
            "timeframe": timeframe,
            "requested_algorithms": algorithms,
        }

        if data_type == "commodity" and entity:
            response["data"] = await self._get_commodity_data(entity, timeframe)
            response["predictions"] = await self._get_commodity_predictions(entity)
            response["insights"] = await self._generate_commodity_insights(
                entity, response["data"]
            )

        elif data_type == "stock" and entity:
            response["data"] = await self._get_stock_data(entity, timeframe)
            response["insights"] = await self._generate_stock_insights(
                entity, response["data"]
            )

        elif data_type == "sentiment":
            response["data"] = await self._get_sentiment_data(entity, timeframe)
            response["insights"] = self._generate_sentiment_insights(response["data"])

        for algo in algorithms:
            cypher_queries = self.gds_generator.generate_queries(algo, entity)
            for cq in cypher_queries:
                try:
                    result = await self.executor.execute_neo4j(cq["cypher"])
                    response["gds_results"][cq["name"]] = result
                except Exception as e:
                    response["gds_results"][cq["name"]] = {"error": str(e)}

        return response

    async def _get_commodity_data(self, commodity: str, timeframe: str) -> Dict:
        """Get commodity data"""
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Commodity, CommodityPrice, CommodityNews
        from sqlalchemy import select, func, cast, String
        from datetime import timedelta

        days = 7 if timeframe == "7days" else 30 if timeframe == "30days" else 1
        result_data = {"prices": [], "news": [], "sentiment": None}

        async with AsyncSessionLocal() as session:
            comm_result = await session.execute(
                select(Commodity).where(Commodity.symbol == commodity)
            )
            comm = comm_result.scalar_one_or_none()

            if comm:
                from datetime import datetime

                price_query = (
                    select(CommodityPrice)
                    .where(
                        CommodityPrice.commodity_id == comm.id,
                        CommodityPrice.timestamp
                        >= datetime.now() - timedelta(days=days),
                    )
                    .order_by(CommodityPrice.timestamp.desc())
                    .limit(20)
                )

                pr_result = await session.execute(price_query)
                prices = pr_result.scalars().all()

                result_data["prices"] = [
                    {
                        "timestamp": p.timestamp.isoformat(),
                        "close": p.close,
                        "volume": p.volume,
                    }
                    for p in prices
                ]

                news_query = (
                    select(CommodityNews)
                    .where(
                        cast(CommodityNews.commodities, String).like(f"%{commodity}%")
                    )
                    .order_by(CommodityNews.published_at.desc())
                    .limit(10)
                )

                nr_result = await session.execute(news_query)
                news = nr_result.scalars().all()

                result_data["news"] = [
                    {"headline": n.headline[:100], "source": n.source} for n in news
                ]

        return result_data

    async def _get_stock_data(self, symbol: str, timeframe: str) -> Dict:
        """Get stock data"""
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "message": "Stock data endpoint ready",
        }

    async def _get_sentiment_data(self, entity: str, timeframe: str) -> Dict:
        """Get sentiment data"""
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommoditySentiment, SocialSentiment
        from sqlalchemy import select
        from datetime import timedelta

        days = 7 if timeframe == "7days" else 30
        result = {"commodity_sentiment": [], "stock_sentiment": []}

        async with AsyncSessionLocal() as session:
            if entity:
                cs_query = (
                    select(CommoditySentiment)
                    .where(CommoditySentiment.commodity_symbol == entity)
                    .order_by(CommoditySentiment.date.desc())
                    .limit(10)
                )
            else:
                cs_query = (
                    select(CommoditySentiment)
                    .order_by(CommoditySentiment.date.desc())
                    .limit(20)
                )

            cs_result = await session.execute(cs_query)
            result["commodity_sentiment"] = [
                {
                    "symbol": c.commodity_symbol,
                    "score": c.sentiment_score,
                    "mentions": c.mention_count,
                }
                for c in cs_result.scalars().all()
            ]

        return result

    async def _get_commodity_predictions(self, commodity: str) -> Dict:
        """Get commodity predictions"""
        from core.services.commodity_prediction import CommodityPredictionModel

        try:
            model = CommodityPredictionModel()
            prediction = await model.predict(commodity)
            return prediction
        except Exception as e:
            return {"error": str(e)}

    async def _generate_commodity_insights(
        self, commodity: str, data: Dict
    ) -> List[str]:
        """Generate insights for commodity"""
        insights = []

        prices = data.get("prices", [])
        if prices:
            latest = prices[0]
            if len(prices) > 1:
                change = (
                    (latest.get("close", 0) - prices[1].get("close", 1))
                    / prices[1].get("close", 1)
                ) * 100
                direction = "up" if change > 0 else "down"
                insights.append(
                    f"{commodity} is trending {direction} {abs(change):.2f}%"
                )

        news = data.get("news", [])
        if news:
            insights.append(f"Found {len(news)} recent news articles about {commodity}")

        return insights

    async def _generate_stock_insights(self, symbol: str, data: Dict) -> List[str]:
        """Generate insights for stock"""
        return [f"Stock data for {symbol} ready"]

    def _generate_sentiment_insights(self, data: Dict) -> List[str]:
        """Generate insights from sentiment data"""
        insights = []

        comm_sent = data.get("commodity_sentiment", [])
        if comm_sent:
            avg_score = sum(s.get("score", 0) for s in comm_sent) / len(comm_sent)
            direction = (
                "positive"
                if avg_score > 10
                else "negative"
                if avg_score < -10
                else "neutral"
            )
            insights.append(f"Overall sentiment: {direction} ({avg_score:.1f})")

        return insights

    async def run_gds_analysis(self, query: str) -> Dict:
        """Run GDS analysis based on query"""
        algorithms = self.gds_generator.detect_algorithm(query)
        results = {}

        for algo in algorithms:
            queries = self.gds_generator.generate_queries(algo)

            for q in queries:
                try:
                    result = await self.executor.execute_neo4j(q["cypher"])
                    results[q["name"]] = result
                except Exception as e:
                    results[q["name"]] = {"error": str(e)}

        return {
            "requested_algorithms": algorithms,
            "results": results,
        }

    async def get_market_overview(self) -> Dict:
        """Get complete market overview"""
        from core.services.commodity_prediction import CommodityPredictionModel
        from core.services.gds_analytics import GDSAnalytics

        overview = {
            "commodity_predictions": [],
            "market_sentiment": {},
            "graph_analytics": {},
        }

        model = CommodityPredictionModel()
        try:
            summary = await model.get_market_summary()
            overview["market_sentiment"] = summary
        except Exception as e:
            overview["market_sentiment"] = {"error": str(e)}

        try:
            gds = GDSAnalytics()
            await gds.init()
            overview["graph_analytics"] = {
                "influencers": await gds.get_top_influencers(10),
                "communities": await gds.get_communities(5),
            }
        except Exception as e:
            overview["graph_analytics"] = {"error": str(e)}

        return overview


async def process_agent_query(query: str) -> Dict:
    """Process user query through the agent"""
    agent = FinGraphAgent()
    return await agent.understand_and_execute(query)


async def get_agent_market_overview() -> Dict:
    """Get market overview through agent"""
    agent = FinGraphAgent()
    return await agent.get_market_overview()


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== Testing FinGraph Agent ===\n")

        agent = FinGraphAgent()

        test_queries = [
            "What's happening with gold?",
            "Show me commodity sentiment",
            "Find influential companies in the network",
            "What are the key communities?",
        ]

        for q in test_queries:
            print(f"Query: {q}")
            result = await agent.understand_and_execute(q)
            print(f"  Data Type: {result['understanding'].get('data_type')}")
            print(f"  Entity: {result['understanding'].get('entity')}")
            print(
                f"  Algorithms: {result['understanding'].get('requested_algorithms')}"
            )
            print()

    asyncio.run(test())
