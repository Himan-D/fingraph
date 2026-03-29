"""
Neo4j Knowledge Graph Service
"""

from neo4j import GraphDatabase
from typing import Dict, Any, List, Optional
import logging
from config import settings

logger = logging.getLogger(__name__)

# Sample knowledge graph data for visualization
SAMPLE_GRAPH_DATA = {
    "companies": {
        "RELIANCE": {
            "name": "Reliance Industries Ltd",
            "sector": "Energy",
            "industry": "Oil & Gas",
            "market_cap": 2012500,
            "promoter": "Mukesh Ambani",
            "promoter_holding": 49.4,
        },
        "TCS": {
            "name": "Tata Consultancy Services Ltd",
            "sector": "Technology",
            "industry": "IT Services",
            "market_cap": 1525000,
            "promoter": "Tata Sons",
            "promoter_holding": 72.3,
        },
        "HDFCBANK": {
            "name": "HDFC Bank Ltd",
            "sector": "Financial Services",
            "industry": "Banking",
            "market_cap": 1250000,
            "promoter": "HDFC Group",
            "promoter_holding": 26.5,
        },
        "INFY": {
            "name": "Infosys Ltd",
            "sector": "Technology",
            "industry": "IT Services",
            "market_cap": 765000,
            "promoter": "Narayana Murthy Family",
            "promoter_holding": 14.2,
        },
        "ICICIBANK": {
            "name": "ICICI Bank Ltd",
            "sector": "Financial Services",
            "industry": "Banking",
            "market_cap": 685000,
            "promoter": "ICICI Group",
            "promoter_holding": 25.8,
        },
        "SBIN": {
            "name": "State Bank of India",
            "sector": "Financial Services",
            "industry": "Banking",
            "market_cap": 625000,
            "promoter": "Government of India",
            "promoter_holding": 57.5,
        },
        "JIO": {
            "name": "Reliance Jio Infocomm Ltd",
            "sector": "Telecommunication",
            "industry": "Telecom Services",
            "market_cap": 950000,
            "promoter": "Reliance Industries",
            "promoter_holding": 100.0,
        },
        "TATAMOTORS": {
            "name": "Tata Motors Ltd",
            "sector": "Automobile",
            "industry": "Automobiles",
            "market_cap": 285000,
            "promoter": "Tata Group",
            "promoter_holding": 46.5,
        },
        "TATASTEEL": {
            "name": "Tata Steel Ltd",
            "sector": "Metals",
            "industry": "Steel",
            "market_cap": 185000,
            "promoter": "Tata Group",
            "promoter_holding": 32.5,
        },
        "HCLTECH": {
            "name": "HCL Technologies Ltd",
            "sector": "Technology",
            "industry": "IT Services",
            "market_cap": 425000,
            "promoter": "Shiv Nadar",
            "promoter_holding": 35.2,
        },
    },
    "promoters": {
        "Mukesh Ambani": ["RELIANCE", "JIO"],
        "Tata Sons": ["TCS", "TATAMOTORS", "TATASTEEL"],
        "Tata Group": ["TCS", "TATAMOTORS", "TATASTEEL"],
        "HDFC Group": ["HDFCBANK"],
        "ICICI Group": ["ICICIBANK"],
        "Government of India": ["SBIN"],
        "Narayana Murthy Family": ["INFY"],
        "Shiv Nadar": ["HCLTECH"],
    },
    "relationships": [
        # Promoter relationships
        {
            "from": "Mukesh Ambani",
            "to": "RELIANCE",
            "type": "PROMOTER_OF",
            "holding": 49.4,
        },
        {"from": "Mukesh Ambani", "to": "JIO", "type": "PROMOTER_OF", "holding": 100.0},
        {"from": "Tata Sons", "to": "TCS", "type": "PROMOTER_OF", "holding": 72.3},
        {
            "from": "Tata Sons",
            "to": "TATAMOTORS",
            "type": "PROMOTER_OF",
            "holding": 46.5,
        },
        {
            "from": "Tata Sons",
            "to": "TATASTEEL",
            "type": "PROMOTER_OF",
            "holding": 32.5,
        },
        # Subsidiary relationships
        {"from": "RELIANCE", "to": "JIO", "type": "SUBSIDIARY_OF", "holding": 100.0},
        # Sector relationships
        {"from": "RELIANCE", "to": "Energy", "type": "BELONGS_TO_SECTOR"},
        {"from": "JIO", "to": "Telecommunication", "type": "BELONGS_TO_SECTOR"},
        {"from": "TCS", "to": "Technology", "type": "BELONGS_TO_SECTOR"},
        {"from": "INFY", "to": "Technology", "type": "BELONGS_TO_SECTOR"},
        {"from": "HCLTECH", "to": "Technology", "type": "BELONGS_TO_SECTOR"},
        {"from": "HDFCBANK", "to": "Financial Services", "type": "BELONGS_TO_SECTOR"},
        {"from": "ICICIBANK", "to": "Financial Services", "type": "BELONGS_TO_SECTOR"},
        {"from": "SBIN", "to": "Financial Services", "type": "BELONGS_TO_SECTOR"},
        {"from": "TATAMOTORS", "to": "Automobile", "type": "BELONGS_TO_SECTOR"},
        {"from": "TATASTEEL", "to": "Metals", "type": "BELONGS_TO_SECTOR"},
        # Index relationships
        {"from": "RELIANCE", "to": "NIFTY50", "type": "PART_OF_INDEX", "weight": 7.5},
        {"from": "TCS", "to": "NIFTY50", "type": "PART_OF_INDEX", "weight": 4.5},
        {"from": "HDFCBANK", "to": "NIFTY50", "type": "PART_OF_INDEX", "weight": 2.8},
        {"from": "INFY", "to": "NIFTY50", "type": "PART_OF_INDEX", "weight": 2.2},
        {"from": "ICICIBANK", "to": "NIFTY50", "type": "PART_OF_INDEX", "weight": 1.5},
        {"from": "SBIN", "to": "NIFTY50", "type": "PART_OF_INDEX", "weight": 1.2},
        # Bank Nifty
        {
            "from": "HDFCBANK",
            "to": "BANKNIFTY",
            "type": "PART_OF_INDEX",
            "weight": 12.5,
        },
        {
            "from": "ICICIBANK",
            "to": "BANKNIFTY",
            "type": "PART_OF_INDEX",
            "weight": 10.2,
        },
        {"from": "SBIN", "to": "BANKNIFTY", "type": "PART_OF_INDEX", "weight": 8.5},
        # Nifty IT
        {"from": "TCS", "to": "NIFTYIT", "type": "PART_OF_INDEX", "weight": 28.5},
        {"from": "INFY", "to": "NIFTYIT", "type": "PART_OF_INDEX", "weight": 22.5},
        {"from": "HCLTECH", "to": "NIFTYIT", "type": "PART_OF_INDEX", "weight": 12.5},
        # Industry relationships
        {"from": "TCS", "to": "INFY", "type": "COMPETES_WITH"},
        {"from": "TCS", "to": "HCLTECH", "type": "COMPETES_WITH"},
        {"from": "INFY", "to": "HCLTECH", "type": "COMPETES_WITH"},
        {"from": "HDFCBANK", "to": "ICICIBANK", "type": "COMPETES_WITH"},
        {"from": "HDFCBANK", "to": "SBIN", "type": "COMPETES_WITH"},
        {"from": "ICICIBANK", "to": "SBIN", "type": "COMPETES_WITH"},
        {"from": "RELIANCE", "to": "TATASTEEL", "type": "COMPETES_WITH"},
    ],
    "sectors": {
        "Technology": {"companies": ["TCS", "INFY", "HCLTECH"], "index": "NIFTYIT"},
        "Financial Services": {
            "companies": ["HDFCBANK", "ICICIBANK", "SBIN"],
            "index": "BANKNIFTY",
        },
        "Energy": {"companies": ["RELIANCE"], "index": "NIFTYENERGY"},
        "Telecommunication": {"companies": ["JIO"], "index": "NIFTY50"},
        "Automobile": {"companies": ["TATAMOTORS"], "index": "NIFTYAUTO"},
        "Metals": {"companies": ["TATASTEEL"], "index": "NIFTYMETAL"},
    },
    "indices": {
        "NIFTY50": {"name": "Nifty 50", "value": 22450},
        "BANKNIFTY": {"name": "Bank Nifty", "value": 48250},
        "NIFTYIT": {"name": "Nifty IT", "value": 35250},
    },
    "kmp": {
        "N Chandrasekaran": {
            "designation": "Chairman",
            "company": "TCS",
            "din": "00121863",
        },
        "C P Gurnani": {
            "designation": "CEO & MD",
            "company": "HCLTECH",
            "din": "00173747",
        },
    },
}


class Neo4jGraph:
    """Neo4j Knowledge Graph Service"""

    def __init__(self):
        self.driver = None
        self._connect()

    def _connect(self):
        """Connect to Neo4j"""
        try:
            if settings.NEO4J_URI and settings.NEO4J_PASSWORD:
                self.driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
                logger.info("Connected to Neo4j")
            else:
                logger.warning("Neo4j credentials not configured, using sample data")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}, using sample data")

    def close(self):
        """Close connection"""
        if self.driver:
            self.driver.close()

    def add_company_node(
        self,
        symbol: str,
        name: str,
        sector: str,
        industry: str = "",
        market_cap: float = 0,
    ):
        """Add a company node to Neo4j"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MERGE (c:Company {symbol: $symbol})
                    SET c.name = $name,
                        c.sector = $sector,
                        c.industry = $industry,
                        c.market_cap = $market_cap
                    """,
                    symbol=symbol,
                    name=name,
                    sector=sector,
                    industry=industry,
                    market_cap=market_cap,
                )
                return True
        except Exception as e:
            logger.warning(f"Failed to add company {symbol}: {e}")
            return False

    def add_sector_node(self, sector: str):
        """Add a sector node"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("MERGE (s:Sector {name: $sector})", sector=sector)
                return True
        except Exception as e:
            logger.warning(f"Failed to add sector {sector}: {e}")
            return False

    def add_relationship(self, from_symbol: str, to_symbol: str, rel_type: str):
        """Add relationship between companies"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (a:Company {symbol: $from_symbol})
                    MATCH (b:Company {symbol: $to_symbol})
                    MERGE (a)-[r:COMPETITOR]->(b)
                    """,
                    from_symbol=from_symbol,
                    to_symbol=to_symbol,
                )
                return True
        except Exception as e:
            logger.warning(
                f"Failed to add relationship {from_symbol}->{to_symbol}: {e}"
            )
            return False
        try:
            with self.driver.session() as session:
                session.run(
                    f"""
                    MATCH (a:Company {{symbol: $from_symbol}})
                    MATCH (b:Company {{symbol: $to_symbol}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    """,
                    from_symbol=from_symbol,
                    to_symbol=to_symbol,
                )
                return True
        except Exception as e:
            logger.warning(
                f"Failed to add relationship {from_symbol}->{to_symbol}: {e}"
            )
            return False
        try:
            with self.driver.session() as session:
                session.run(
                    f"""
                    MATCH (a:Company {{symbol: $from}})
                    MATCH (b:Company {{symbol: $to}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    """,
                    from_=from_symbol,
                    to=to_symbol,
                )
                return True
        except Exception as e:
            logger.warning(
                f"Failed to add relationship {from_symbol}->{to_symbol}: {e}"
            )
            return False

    def add_sector_relationship(self, company_symbol: str, sector_name: str):
        """Add BELONGS_TO_SECTOR relationship"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (c:Company {symbol: $symbol})
                    MATCH (s:Sector {name: $sector})
                    MERGE (c)-[:BELONGS_TO_SECTOR]->(s)
                    """,
                    symbol=company_symbol,
                    sector=sector_name,
                )
                return True
        except Exception as e:
            logger.warning(f"Failed to add sector relationship: {e}")
            return False

    def get_all_nodes(self):
        """Get all nodes from Neo4j"""
        if not self.driver:
            return {"nodes": [], "edges": []}
        try:
            with self.driver.session() as session:
                companies = session.run("MATCH (c:Company) RETURN c").data()
                sectors = session.run("MATCH (s:Sector) RETURN s").data()
                relationships = session.run(
                    "MATCH (a)-[r]->(b) RETURN a.symbol as from, type(r) as type, b.symbol as to"
                ).data()

                nodes = []
                for c in companies:
                    nodes.append(
                        {"id": c["c"]["symbol"], "label": "Company", "data": c["c"]}
                    )
                for s in sectors:
                    nodes.append(
                        {"id": s["s"]["name"], "label": "Sector", "data": s["s"]}
                    )

                edges = []
                for r in relationships:
                    edges.append({"from": r["from"], "to": r["to"], "type": r["type"]})

                return {"nodes": nodes, "edges": edges}
        except Exception as e:
            logger.warning(f"Failed to get nodes: {e}")
            return {"nodes": [], "edges": []}

    async def get_company_graph(self, symbol: str) -> Dict:
        """Get graph data for a company"""
        symbol = symbol.upper()

        # Get company info
        company = SAMPLE_GRAPH_DATA["companies"].get(symbol, {})

        if not company:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []

        # Add company node
        nodes.append(
            {
                "id": symbol,
                "label": "Company",
                "data": company,
            }
        )

        # Add promoter
        if company.get("promoter"):
            promoter_id = company["promoter"].replace(" ", "_")
            nodes.append(
                {
                    "id": promoter_id,
                    "label": "Promoter",
                    "data": {"name": company["promoter"]},
                }
            )
            edges.append(
                {
                    "from": promoter_id,
                    "to": symbol,
                    "type": "PROMOTER_OF",
                    "label": f"Promoter ({company.get('promoter_holding', 0)}%)",
                }
            )

        # Add sector
        sector = company.get("sector", "Other")
        nodes.append(
            {
                "id": sector,
                "label": "Sector",
                "data": {"name": sector},
            }
        )
        edges.append(
            {
                "from": symbol,
                "to": sector,
                "type": "BELONGS_TO_SECTOR",
                "label": "Belongs to",
            }
        )

        # Add index membership
        for rel in SAMPLE_GRAPH_DATA["relationships"]:
            if rel["from"] == symbol and rel["type"] == "PART_OF_INDEX":
                idx = rel["to"]
                nodes.append(
                    {
                        "id": idx,
                        "label": "Index",
                        "data": SAMPLE_GRAPH_DATA["indices"].get(idx, {"name": idx}),
                    }
                )
                edges.append(
                    {
                        "from": symbol,
                        "to": idx,
                        "type": "PART_OF_INDEX",
                        "label": f"Index Weight: {rel.get('weight', 0)}%",
                    }
                )

        # Add competitors
        for rel in SAMPLE_GRAPH_DATA["relationships"]:
            if rel["from"] == symbol and rel["type"] == "COMPETES_WITH":
                comp = rel["to"]
                comp_data = SAMPLE_GRAPH_DATA["companies"].get(comp, {"name": comp})
                nodes.append(
                    {
                        "id": comp,
                        "label": "Company",
                        "data": comp_data,
                    }
                )
                edges.append(
                    {
                        "from": symbol,
                        "to": comp,
                        "type": "COMPETES_WITH",
                        "label": "Competitor",
                    }
                )

        # Add subsidiaries
        for rel in SAMPLE_GRAPH_DATA["relationships"]:
            if rel["from"] == symbol and rel["type"] == "SUBSIDIARY_OF":
                sub = rel["to"]
                sub_data = SAMPLE_GRAPH_DATA["companies"].get(sub, {"name": sub})
                nodes.append(
                    {
                        "id": sub,
                        "label": "Subsidiary",
                        "data": sub_data,
                    }
                )
                edges.append(
                    {
                        "from": symbol,
                        "to": sub,
                        "type": "SUBSIDIARY_OF",
                        "label": f"Owns {rel.get('holding', 100)}%",
                    }
                )

        return {"nodes": nodes, "edges": edges}

    async def get_promoter_network(self, promoter_name: str) -> Dict:
        """Get all companies for a promoter"""
        companies = SAMPLE_GRAPH_DATA["promoters"].get(promoter_name, [])

        nodes = []
        edges = []

        # Add promoter node
        nodes.append(
            {
                "id": promoter_name.replace(" ", "_"),
                "label": "Promoter",
                "data": {"name": promoter_name},
            }
        )

        for symbol in companies:
            company = SAMPLE_GRAPH_DATA["companies"].get(symbol, {"name": symbol})
            nodes.append(
                {
                    "id": symbol,
                    "label": "Company",
                    "data": company,
                }
            )
            edges.append(
                {
                    "from": promoter_name.replace(" ", "_"),
                    "to": symbol,
                    "type": "PROMOTER_OF",
                    "label": f"Promoter ({company.get('promoter_holding', 0)}%)",
                }
            )

        return {"nodes": nodes, "edges": edges}

    async def get_sector_graph(self, sector: str) -> Dict:
        """Get graph for entire sector"""
        sector_data = SAMPLE_GRAPH_DATA["sectors"].get(sector, {})
        companies = sector_data.get("companies", [])

        nodes = []
        edges = []

        # Add sector node
        nodes.append(
            {
                "id": sector,
                "label": "Sector",
                "data": {"name": sector},
            }
        )

        for symbol in companies:
            company = SAMPLE_GRAPH_DATA["companies"].get(symbol, {"name": symbol})
            nodes.append(
                {
                    "id": symbol,
                    "label": "Company",
                    "data": company,
                }
            )
            edges.append(
                {
                    "from": symbol,
                    "to": sector,
                    "type": "BELONGS_TO_SECTOR",
                    "label": "Belongs to",
                }
            )

            # Add relationships between companies
            for rel in SAMPLE_GRAPH_DATA["relationships"]:
                if rel["from"] == symbol and rel["type"] == "COMPETES_WITH":
                    comp = rel["to"]
                    if comp in companies:
                        edges.append(
                            {
                                "from": symbol,
                                "to": comp,
                                "type": "COMPETES_WITH",
                                "label": "Competitor",
                            }
                        )

        return {"nodes": nodes, "edges": edges}

    async def get_full_graph(self) -> Dict:
        """Get complete knowledge graph"""
        nodes = []
        edges = []

        # Add all companies
        for symbol, company in SAMPLE_GRAPH_DATA["companies"].items():
            nodes.append(
                {
                    "id": symbol,
                    "label": "Company",
                    "data": company,
                }
            )

        # Add all sectors
        for sector in SAMPLE_GRAPH_DATA["sectors"].keys():
            if not any(n["id"] == sector for n in nodes):
                nodes.append(
                    {
                        "id": sector,
                        "label": "Sector",
                        "data": {"name": sector},
                    }
                )

        # Add all indices
        for idx, data in SAMPLE_GRAPH_DATA["indices"].items():
            nodes.append(
                {
                    "id": idx,
                    "label": "Index",
                    "data": data,
                }
            )

        # Add all relationships
        for rel in SAMPLE_GRAPH_DATA["relationships"]:
            edges.append(
                {
                    "from": rel["from"],
                    "to": rel["to"],
                    "type": rel["type"],
                    "label": rel.get("label", rel["type"]),
                }
            )

        return {"nodes": nodes, "edges": edges}

    async def search(self, query: str) -> List[Dict]:
        """Search entities"""
        results = []
        query = query.upper()

        # Search companies
        for symbol, data in SAMPLE_GRAPH_DATA["companies"].items():
            if query in symbol or query in data.get("name", "").upper():
                results.append({"type": "company", "id": symbol, "data": data})

        # Search sectors
        for sector in SAMPLE_GRAPH_DATA["sectors"].keys():
            if query in sector.upper():
                results.append(
                    {"type": "sector", "id": sector, "data": {"name": sector}}
                )

        return results


# Singleton instance
_graph_service = None


def get_graph_service() -> Neo4jGraph:
    global _graph_service
    if _graph_service is None:
        _graph_service = Neo4jGraph()
    return _graph_service
