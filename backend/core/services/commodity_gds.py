from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CommodityGDSAnalytics:
    """GDS analytics for commodity market analysis"""

    def __init__(self):
        self.driver = None

    async def init(self):
        """Initialize with Neo4j driver"""
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()
        return self.driver

    async def create_commodity_graph(self, graph_name: str = "commodity_graph"):
        """Create GDS graph projection for commodities"""
        if not self.driver:
            await self.init()

        query = f"""
        CALL gds.graph.project(
            '{graph_name}',
            ['Commodity', 'Event', 'News', 'Sector'],
            ['AFFECTS', 'RELATED_TO', 'TRADED_IN', 'IMPACTS']
        )
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                return await result.data()
        except Exception as e:
            logger.warning(f"GDS commodity graph creation failed: {e}")
            return []

    async def add_commodity_nodes(self):
        """Add commodity nodes to Neo4j"""
        if not self.driver:
            await self.init()

        commodities = [
            {"symbol": "GOLD", "name": "Gold", "category": "precious"},
            {"symbol": "SILVER", "name": "Silver", "category": "precious"},
            {"symbol": "CRUDEOIL", "name": "Crude Oil", "category": "energy"},
            {"symbol": "NATURALGAS", "name": "Natural Gas", "category": "energy"},
            {"symbol": "COPPER", "name": "Copper", "category": "base"},
            {"symbol": "ALUMINIUM", "name": "Aluminium", "category": "base"},
            {"symbol": "ZINC", "name": "Zinc", "category": "base"},
            {"symbol": "NICKEL", "name": "Nickel", "category": "base"},
        ]

        async with self.driver.session() as session:
            for comm in commodities:
                query = """
                MERGE (c:Commodity {symbol: $symbol})
                SET c.name = $name, c.category = $category
                """
                await session.run(query, **comm)

        logger.info("Added commodity nodes to graph")

    async def add_commodity_relationships(self):
        """Add relationships between commodities based on correlations"""
        if not self.driver:
            await self.init()

        correlations = [
            ("GOLD", "SILVER", "correlated", 0.8),
            ("CRUDEOIL", "NATURALGAS", "correlated", 0.5),
            ("COPPER", "ALUMINIUM", "correlated", 0.6),
            ("CRUDEOIL", "GOLD", "inverse", -0.3),
            ("GOLD", "CRUDEOIL", "affects", 0.4),
        ]

        async with self.driver.session() as session:
            for src, tgt, rel_type, weight in correlations:
                query = f"""
                MATCH (s:Commodity {{symbol: $src}}), (t:Commodity {{symbol: $tgt}})
                MERGE (s)-[r:{rel_type}]->(t)
                SET r.weight = $weight
                """
                await session.run(query, src=src, tgt=tgt, weight=weight)

        logger.info("Added commodity relationships")

    async def add_news_relationships(self):
        """Link news to commodities"""
        if not self.driver:
            await self.init()

        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityNews
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CommodityNews)
                .order_by(CommodityNews.published_at.desc())
                .limit(100)
            )
            news_items = result.scalars().all()

        async with self.driver.session() as session:
            for news in news_items:
                commodities = news.commodities or []
                for comm in commodities:
                    query = """
                    MATCH (n:News {headline: $headline})
                    MATCH (c:Commodity {symbol: $commodity})
                    MERGE (n)-[:AFFECTS]->(c)
                    """
                    try:
                        await session.run(
                            query, headline=news.headline[:100], commodity=comm
                        )
                    except Exception:
                        pass

        logger.info("Added news relationships")

    async def analyze_commodity_network(self) -> Dict:
        """Analyze commodity network"""
        if not self.driver:
            await self.init()

        results = {}

        query = """
        MATCH (c:Commodity)
        OPTIONAL MATCH (c)-[r]-(other)
        RETURN c.symbol as symbol, c.name as name, c.category as category,
               count(DISTINCT other) as connections
        ORDER BY connections DESC
        """

        async with self.driver.session() as session:
            result = await session.run(query)
            results["network"] = await result.data()

        return results

    async def find_commodity_clusters(self) -> List[Dict]:
        """Find commodity clusters"""
        if not self.driver:
            await self.init()

        query = """
        CALL gds.louvain.write('commodity_graph', {
            writeProperty: 'cluster',
            maxIterations: 10
        })
        YIELD communityCount, modularity
        RETURN communityCount, modularity
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                return await result.data()
        except Exception as e:
            logger.warning(f"Cluster analysis failed: {e}")
            return []

    async def get_related_commodities(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Get related commodities"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (c:Commodity {symbol: $symbol})-[r]-(related)
        RETURN related.symbol as symbol, related.name as name,
               type(r) as relationship, r.weight as weight
        ORDER BY r.weight DESC
        LIMIT $limit
        """

        async with self.driver.session() as session:
            result = await session.run(query, symbol=symbol.upper(), limit=limit)
            return await result.data()

    async def analyze_event_impact(self, event: str) -> Dict:
        """Analyze impact of an event on commodities"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (e:Event {name: $event})-[:AFFECTS|IMPACTS]->(c:Commodity)
        RETURN c.symbol as commodity, c.name as name,
               e.sentiment as event_sentiment, e.timestamp as time
        """

        async with self.driver.session() as session:
            result = await session.run(query, event=event)
            data = await result.data()

            if data:
                return {"event": event, "affected_commodities": data}

        return {"event": event, "affected_commodities": []}

    async def predict_commodity_links(self) -> List[Dict]:
        """Predict potential commodity links"""
        if not self.driver:
            await self.driver

        commodities = [
            "GOLD",
            "SILVER",
            "CRUDEOIL",
            "NATURALGAS",
            "COPPER",
            "ALUMINIUM",
        ]

        predictions = []

        async with self.driver.session() as session:
            for i, c1 in enumerate(commodities):
                for c2 in commodities[i + 1 :]:
                    query = """
                    MATCH (c1:Commodity {symbol: $s1}), (c2:Commodity {symbol: $s2})
                    OPTIONAL MATCH path = shortestPath((c1)-[*1..3]-(c2))
                    RETURN c1.symbol as source, c2.symbol as target,
                           case when path IS NULL then 'potential' else 'existing' end as link_status
                    """
                    result = await session.run(query, s1=c1, s2=c2)
                    predictions.extend(await result.data())

        return predictions

    async def commodity_influence_ranking(self) -> List[Dict]:
        """Rank commodities by influence"""
        if not self.driver:
            await self.init()

        query = """
        CALL gds.pageRank.write('commodity_graph', {
            writeProperty: 'pagerank',
            maxIterations: 20
        })
        YIELD nodes
        """

        try:
            async with self.driver.session() as session:
                await session.run(query)

                rank_query = """
                MATCH (c:Commodity)
                WHERE c.pagerank IS NOT NULL
                RETURN c.symbol as symbol, c.name as name, c.pagerank as score
                ORDER BY c.pagerank DESC
                """
                result = await session.run(rank_query)
                return await result.data()
        except Exception as e:
            logger.warning(f"Influence ranking failed: {e}")
            return []

    async def run_full_analytics(self) -> Dict:
        """Run complete commodity GDS analytics"""
        results = {}

        await self.add_commodity_nodes()
        await self.add_commodity_relationships()

        results["network"] = await self.analyze_commodity_network()
        results["influence"] = await self.commodity_influence_ranking()
        results["clusters"] = await self.find_commodity_clusters()

        logger.info("Commodity GDS analytics complete")

        return results


class CommodityEventAnalyzer:
    """Analyze events affecting commodities"""

    def __init__(self):
        self.driver = None

    async def init(self):
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()

    async def analyze_opec_decision(self) -> Dict:
        """Analyze OPEC decision impact"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (e:Event {type: 'OPEC'})
        OPTIONAL MATCH (e)-[:AFFECTS]->(c:Commodity {symbol: 'CRUDEOIL'})
        OPTIONAL MATCH (e)-[:AFFECTS]->(c2:Commodity {symbol: 'NATURALGAS'})
        RETURN e.name as event, e.sentiment as sentiment,
               c.symbol as crude_symbol, c2.symbol as gas_symbol
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                return await result.single() or {}
        except:
            return {}

    async def analyze_fed_rate_decision(self) -> Dict:
        """Analyze Fed rate decision impact on commodities"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (e:Event {type: 'FED_RATE'})
        OPTIONAL MATCH (e)-[:AFFECTS]->(c:Commodity)
        RETURN e.name as event, e.sentiment as sentiment,
               collect(c.symbol) as affected_commodities
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                return await result.single() or {}
        except:
            return {}

    async def analyze_inflation_impact(self) -> Dict:
        """Analyze inflation impact on commodities"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (e:Event {type: 'INFLATION'})
        OPTIONAL MATCH (e)-[:AFFECTS]->(c:Commodity)
        WHERE c.symbol IN ['GOLD', 'SILVER', 'CRUDEOIL']
        RETURN e.name as event, 
               collect({symbol: c.symbol, name: c.name}) as commodities
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                return await result.single() or {}
        except:
            return {}

    async def find_correlated_events(self, commodity: str) -> List[Dict]:
        """Find events correlated with a commodity"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (e:Event)-[:AFFECTS]->(c:Commodity {symbol: $symbol})
        RETURN e.name as event, e.type as type, e.sentiment as sentiment,
               e.timestamp as timestamp
        ORDER BY e.timestamp DESC
        LIMIT 20
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query, symbol=commodity.upper())
                return await result.data()
        except:
            return []


async def get_commodity_analytics() -> CommodityGDSAnalytics:
    """Get commodity GDS analytics instance"""
    gds = CommodityGDSAnalytics()
    await gds.init()
    return gds


if __name__ == "__main__":
    import asyncio

    async def main():
        gds = await get_commodity_analytics()
        results = await gds.run_full_analytics()
        print(f"Analytics complete: {results}")

    asyncio.run(main())
