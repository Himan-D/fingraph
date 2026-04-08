from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class GDSAnalytics:
    """Neo4j Graph Data Science for event analysis and predictions"""

    def __init__(self):
        self.driver = None

    async def init(self):
        """Initialize with Neo4j driver"""
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()
        return self.driver

    async def create_graph_project(self, graph_name: str = "finance_graph"):
        """Create GDS graph projection"""
        if not self.driver:
            await self.init()

        queries = [
            f"""
            CALL gds.graph.project(
                '{graph_name}',
                ['Company', 'Sector', 'Stock', 'Event', 'News'],
                ['AFFECTS', 'RELEVANT_TO', 'TRADED_IN', 'RELATED_TO', 'MENTIONS']
            )
            """
        ]

        results = []
        async with self.driver.session() as session:
            for q in queries:
                try:
                    result = await session.run(q)
                    results.append(await result.data())
                except Exception as e:
                    logger.warning(f"GDS projection failed: {e}")

        return results

    async def pagerank(self, graph_name: str = "finance_graph") -> List[Dict]:
        """Run PageRank to find influential entities"""
        if not self.driver:
            await self.init()

        query = f"""
        CALL gds.pageRank.write('{graph_name}', {{
            writeProperty: 'pagerank',
            maxIterations: 20,
            dampingFactor: 0.85
        }})
        YIELD nodes, iterations, writeProperty
        RETURN nodes, iterations, writeProperty
        """

        async with self.driver.session() as session:
            result = await session.run(query)
            return await result.data()

    async def get_top_influencers(self, limit: int = 20) -> List[Dict]:
        """Get most influential entities by PageRank"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (n)
        WHERE n.pagerank IS NOT NULL
        RETURN labels(n)[0] as type, n.name as name, n.symbol as symbol, n.pagerank as score
        ORDER BY n.pagerank DESC
        LIMIT $limit
        """

        async with self.driver.session() as session:
            result = await session.run(query, limit=limit)
            return await result.data()

    async def community_detection(
        self, graph_name: str = "finance_graph"
    ) -> List[Dict]:
        """Run Louvain community detection"""
        if not self.driver:
            await self.init()

        query = f"""
        CALL gds.louvain.write('{graph_name}', {{
            writeProperty: 'community',
            maxIterations: 10
        }})
        YIELD communityCount, modularity
        RETURN communityCount, modularity
        """

        async with self.driver.session() as session:
            result = await session.run(query)
            return await result.data()

    async def get_communities(self, limit: int = 10) -> List[Dict]:
        """Get communities and their members"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (n)-[:AFFECTS|RELEVANT_TO|RELATED_TO]-(m)
        WHERE n.community IS NOT NULL AND m.community IS NOT NULL
        WITH n.community as community, collect(DISTINCT coalesce(n.symbol, n.name)) as members
        RETURN community, members
        ORDER BY size(members) DESC
        LIMIT $limit
        """

        async with self.driver.session() as session:
            result = await session.run(query, limit=limit)
            return await result.data()

    async def node_similarity(self, graph_name: str = "finance_graph") -> List[Dict]:
        """Find similar entities using node similarity"""
        if not self.driver:
            await self.init()

        query = f"""
        CALL gds.nodeSimilarity.write('{graph_name}', {{
            writeProperty: 'similarity',
            maxIterations: 10,
            similarityCutoff: 0.5
        }})
        YIELD nodesCompared, relationshipsWritten
        RETURN nodesCompared, relationshipsWritten
        """

        async with self.driver.session() as session:
            result = await session.run(query)
            return await result.data()

    async def betweenness_centrality(
        self, graph_name: str = "finance_graph"
    ) -> List[Dict]:
        """Run Betweenness Centrality to find bridge entities"""
        if not self.driver:
            await self.init()

        query = f"""
        CALL gds.betweenness.write('{graph_name}', {{
            writeProperty: 'betweenness',
            samplingSize: 100
        }})
        YIELD nodes, writeProperty
        RETURN nodes, writeProperty
        """

        async with self.driver.session() as session:
            result = await session.run(query)
            return await result.data()

    async def get_key_bridges(self, limit: int = 20) -> List[Dict]:
        """Get entities that bridge different communities"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (n)
        WHERE n.betweenness IS NOT NULL
        RETURN labels(n)[0] as type, n.name as name, n.symbol as symbol, n.betweenness as score
        ORDER BY n.betweenness DESC
        LIMIT $limit
        """

        async with self.driver.session() as session:
            result = await session.run(query, limit=limit)
            return await result.data()

    async def weakly_connected_components(
        self, graph_name: str = "finance_graph"
    ) -> Dict:
        """Find weakly connected components"""
        if not self.driver:
            await self.init()

        query = f"""
        CALL gds.wcc.write('{graph_name}', {{
            writeProperty: 'component'
        }})
        YIELD componentCount, componentDistribution
        RETURN componentCount, componentDistribution
        """

        async with self.driver.session() as session:
            result = await session.run(query)
            return await result.data()

    async def label_propagation(self, graph_name: str = "finance_graph") -> Dict:
        """Run label propagation for event clustering"""
        if not self.driver:
            await self.init()

        query = f"""
        CALL gds.labelPropagation.write('{graph_name}', {{
            writeProperty: 'lp_community',
            maxIterations: 10
        }})
        YIELD communityCount, ranIterations
        RETURN communityCount, ranIterations
        """

        async with self.driver.session() as session:
            result = await session.run(query)
            return await result.data()

    async def event_impact_analysis(self, event_node: str) -> Dict:
        """Analyze impact of an event on related entities"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (e {name: $event})-[:AFFECTS|RELATED_TO]->(affected)
        WITH e, affected,
             CASE WHEN e.sentiment = 'positive' THEN 1.0
                  WHEN e.sentiment = 'negative' THEN -1.0
                  ELSE 0.0 END as impact
        RETURN e.name as event,
               collect({name: affected.name, symbol: affected.symbol, impact: impact}) as affected_entities,
               size(collect(affected)) as impact_count
        """

        async with self.driver.session() as session:
            result = await session.run(query, event=event_node)
            return await result.single()

    async def predict_relationships(self, source: str, target: str) -> Dict:
        """Predict potential relationships using graph ML"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (s {symbol: $source}), (t {symbol: $target})
        MATCH p = shortestPath((s)-[*1..3]-(t))
        WHERE p IS NULL
        RETURN 'potential_connection' as prediction,
               s.symbol as source,
               t.symbol as target,
               'no_existing_path' as reason
        """

        async with self.driver.session() as session:
            result = await session.run(
                query, source=source.upper(), target=target.upper()
            )
            return await result.single() or {"prediction": "unknown"}

    async def sentiment_flow_analysis(self) -> List[Dict]:
        """Analyze how sentiment flows through the network"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (s:Stock)<-[:MENTIONS]-(n:News)
        WHERE n.sentiment IS NOT NULL
        WITH s, collect({headline: n.headline, sentiment: n.sentiment}) as news_flow
        RETURN s.symbol as symbol,
               s.sentiment_score as current_sentiment,
               size(news_flow) as news_count,
               news_flow[-5..] as recent_news
        ORDER BY size(news_flow) DESC
        LIMIT 50
        """

        async with self.driver.session() as session:
            result = await session.run(query)
            return await result.data()

    async def event_correlation(self, symbols: List[str]) -> Dict:
        """Find correlations between events affecting multiple stocks"""
        if not self.driver:
            await self.init()

        query = """
        MATCH (e:Event)-[:AFFECTS]->(s:Stock)
        WHERE s.symbol IN $symbols
        WITH e, collect(DISTINCT s.symbol) as affected_stocks
        WHERE size(affected_stocks) > 1
        RETURN e.name as event,
               affected_stocks,
               size(affected_stocks) as stock_count,
               e.timestamp as time
        ORDER BY e.timestamp DESC
        LIMIT 20
        """

        async with self.driver.session() as session:
            result = await session.run(query, symbols=symbols)
            return {"correlations": await result.data()}

    async def run_full_analytics(self) -> Dict:
        """Run complete GDS analytics pipeline"""
        results = {}

        logger.info("Running PageRank...")
        results["pagerank"] = await self.pagerank()

        logger.info("Running Community Detection...")
        results["communities"] = await self.community_detection()

        logger.info("Running Node Similarity...")
        results["similarity"] = await self.node_similarity()

        logger.info("Running Betweenness Centrality...")
        results["betweenness"] = await self.betweenness_centrality()

        logger.info("Running WCC...")
        results["wcc"] = await self.weakly_connected_components()

        logger.info("GDS analytics complete")

        return results


async def get_gds_analytics() -> GDSAnalytics:
    """Get GDS analytics instance"""
    gds = GDSAnalytics()
    await gds.init()
    return gds


if __name__ == "__main__":
    import asyncio

    async def main():
        gds = await get_gds_analytics()

        results = await gds.run_full_analytics()
        print(f"Analytics complete: {results}")

    asyncio.run(main())
