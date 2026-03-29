"""
Comprehensive Relationship Analyzer - All types of company relationships
"""

import asyncio
import logging
from typing import List, Dict, Tuple, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class RelationshipAnalyzer:
    """Comprehensive relationship analysis using multiple criteria"""

    # Industry mapping for related companies
    INDUSTRY_KEYWORDS = {
        "IT Services": ["software", "it", "technology", "consulting", "services"],
        "Banking": ["bank", "financial", "nbfc", "housing finance"],
        "Oil & Gas": ["oil", "gas", "petroleum", "refinery", "energy"],
        "Automobile": ["auto", "automobile", "vehicle", "car", "motor"],
        "Pharmaceuticals": ["pharma", "pharmaceutical", "medicine", "drug"],
        "Steel": ["steel", "metal", "iron"],
        "Telecom": ["telecom", "telecommunication", "wireless", "broadband"],
        "Power": ["power", "electricity", "energy", "renewable"],
        "Cement": ["cement", "construction material"],
        "FMCG": ["fmcg", "consumer goods", "food", "beverage"],
    }

    # Promoter groups
    PROMOTER_GROUPS = {
        "Tata": [
            "TCS",
            "TATASTEEL",
            "TATAMOTORS",
            "TITAN",
            "TATACONS",
            "TATAELXSI",
            "TATAPOWER",
        ],
        "Reliance": ["RELIANCE", "RJIO", "RELIANCEPOWER", "ADANIENSOL"],
        "Birla": ["ADANIENT", "ULTRACEMCO", "MINDTREE", "BIRLA_CORP"],
        "HDFC": ["HDFCBANK", "HDFC", "HDFCLIFE", "HDFCAMC"],
        "ICICI": ["ICICIBANK", "ICICIPRULI", "ICICIGI"],
        "SBI": ["SBIN", "SBICARD", "SBILIFE"],
        "Infosys": ["INFY", " Infosys", "TCS"],
        "Bajaj": ["BAJAJFINSV", "BAJFINANCE", "BAJAJ_AUTO", "BAJAJHLDNG"],
    }

    # Supply chain keywords
    SUPPLY_CHAIN = {
        "upstream": ["oil", "gas", "crude", "mining", "coal", "iron ore"],
        "downstream": ["refinery", "petrochemical", "polymers", "retail"],
        "auxiliary": ["logistics", "transport", "packaging"],
    }

    # Competitor keywords
    COMPETITOR_WORDS = ["peer", "competitor", "rival", "similar", "comparable"]

    async def analyze_all_relationships(
        self, companies: List[Dict]
    ) -> List[Tuple[str, str, str, float]]:
        """Analyze and generate all possible relationships"""
        relationships = []
        n = len(companies)

        # Build lookup
        company_sectors = {c["symbol"]: c.get("sector", "").lower() for c in companies}
        company_industries = {
            c["symbol"]: c.get("industry", "").lower() for c in companies
        }
        company_names = {c["symbol"]: c.get("name", "").lower() for c in companies}

        # Compare all pairs
        for i in range(n):
            for j in range(i + 1, n):
                c1 = companies[i]
                c2 = companies[j]
                sym1, sym2 = c1["symbol"], c2["symbol"]

                # 1. Same promoter group
                for group, members in self.PROMOTER_GROUPS.items():
                    if sym1 in members and sym2 in members:
                        relationships.append((sym1, sym2, "SAME_GROUP", 0.95))

                # 2. Same sector
                if company_sectors.get(sym1) == company_sectors.get(sym2):
                    sector = company_sectors.get(sym1)
                    if sector:
                        # Same sector = competitor
                        relationships.append((sym1, sym2, "COMPETITOR", 0.8))

                # 3. Same industry
                if company_industries.get(sym1) == company_industries.get(sym2):
                    industry = company_industries.get(sym1)
                    if industry:
                        relationships.append((sym1, sym2, "SAME_INDUSTRY", 0.85))

                # 4. Check for supply chain relationships
                await self._check_supply_chain(sym1, sym2, company_names, relationships)

                # 5. Check for financial relationships
                await self._check_financial_relationship(
                    sym1, sym2, company_sectors, relationships
                )

                # 6. Check for cross-holding
                await self._check_cross_holding(
                    sym1, sym2, company_names, relationships
                )

        # Remove duplicates and sort by confidence
        unique_rels = {}
        for src, tgt, typ, conf in relationships:
            key = tuple(sorted([src, tgt]))
            if key not in unique_rels:
                unique_rels[key] = (src, tgt, typ, float(conf))

        final = list(unique_rels.values())
        final.sort(key=lambda x: x[3], reverse=True)

        return final

    async def _check_supply_chain(
        self, sym1: str, sym2: str, company_names: Dict, relationships: List
    ):
        """Check for supply chain relationships"""
        name1 = company_names.get(sym1, "").lower()
        name2 = company_names.get(sym2, "").lower()

        # Auto + Auto parts
        if "auto" in name1 or "vehicle" in name1:
            if any(
                x in name2 for x in ["parts", "component", "tire", "battery", "glass"]
            ):
                relationships.append((sym1, sym2, "SUPPLIER", 0.7))

        # Oil + Petrochemical
        if "oil" in name1 or "gas" in name1:
            if "petrochemical" in name2 or "refinery" in name2:
                relationships.append((sym1, sym2, "CUSTOMER", 0.65))

        # IT + BPO
        if "it" in name1 or "software" in name1:
            if "bpo" in name2 or "outsourcing" in name2:
                relationships.append((sym1, sym2, "SERVICE_PROVIDER", 0.6))

    async def _check_financial_relationship(
        self, sym1: str, sym2: str, company_sectors: Dict, relationships: List
    ):
        """Check for financial relationships"""
        # Banking + Insurance
        sector1 = company_sectors.get(sym1, "").lower()
        sector2 = company_sectors.get(sym2, "").lower()

        if "financial" in sector1 and "insurance" in sector2:
            relationships.append((sym1, sym2, "CROSS_SELL", 0.6))
        if "financial" in sector2 and "insurance" in sector1:
            relationships.append((sym1, sym2, "CROSS_SELL", 0.6))

        # Bank + NBFC
        if "banking" in sector1 and "nbfc" in sector2:
            relationships.append((sym1, sym2, "SAME_GROUP", 0.55))

    async def _check_cross_holding(
        self, sym1: str, sym2: str, company_names: Dict, relationships: List
    ):
        """Check for cross-holding possibilities"""
        name1 = company_names.get(sym1, "").lower()
        name2 = company_names.get(sym2, "").lower()

        # Group companies often have cross holdings
        groups = {
            "tata": ["tata", "tata sons"],
            "reliance": ["reliance", "mukesh"],
            "birla": ["aditya birla", "birla"],
            "mahindra": ["mahindra", "anand mahindra"],
        }

        for group, keywords in groups.items():
            if any(k in name1 for k in keywords) and any(k in name2 for k in keywords):
                relationships.append((sym1, sym2, "POSSIBLE_CROSS_HOLDING", 0.4))
                break

    async def generate_knowledge_graph_data(self, companies: List[Dict]) -> Dict:
        """Generate complete knowledge graph with all relationships"""
        relationships = await self.analyze_all_relationships(companies)

        nodes = []
        edges = []
        node_ids = set()

        # Create nodes
        for company in companies:
            nodes.append(
                {
                    "id": company["symbol"],
                    "label": "Company",
                    "data": {
                        "name": company.get("name", ""),
                        "sector": company.get("sector", ""),
                        "industry": company.get("industry", ""),
                        "market_cap": company.get("market_cap", 0),
                    },
                }
            )
            node_ids.add(company["symbol"])

            # Add sector node
            sector = company.get("sector", "")
            if sector and sector not in node_ids:
                nodes.append(
                    {"id": sector, "label": "Sector", "data": {"name": sector}}
                )
                node_ids.add(sector)
                edges.append(
                    {
                        "from": company["symbol"],
                        "to": sector,
                        "type": "BELONGS_TO_SECTOR",
                        "label": "belongs to",
                    }
                )

        # Create edges
        for src, tgt, rel_type, confidence in relationships:
            edges.append(
                {
                    "from": src,
                    "to": tgt,
                    "type": rel_type,
                    "label": rel_type.replace("_", " "),
                    "confidence": confidence,
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_companies": len(companies),
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "relationship_types": list(set(r[2] for r in relationships)),
            },
        }


async def build_complete_knowledge_graph():
    """Build complete knowledge graph with all relationships"""
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import Company
    from sqlalchemy import select
    from core.services.graph_service import Neo4jGraph

    analyzer = RelationshipAnalyzer()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company).limit(100))
        companies = result.scalars().all()

        company_dicts = [
            {
                "symbol": c.symbol,
                "name": c.name,
                "sector": c.sector,
                "industry": c.industry,
                "market_cap": c.market_cap,
            }
            for c in companies
        ]

    # Generate knowledge graph
    kg_data = await analyzer.generate_knowledge_graph_data(company_dicts)

    # Store in Neo4j
    graph = Neo4jGraph()
    if graph.driver:
        # Clear existing
        try:
            with graph.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
        except:
            pass

        # Add nodes
        for node in kg_data["nodes"]:
            if node["label"] == "Company":
                graph.add_company_node(
                    node["id"],
                    node["data"].get("name", ""),
                    node["data"].get("sector", ""),
                    node["data"].get("industry", ""),
                    node["data"].get("market_cap", 0),
                )
            else:
                graph.add_sector_node(node["data"].get("name", ""))

        # Add edges
        for edge in kg_data["edges"]:
            if edge["from"] != edge["to"]:
                graph.add_relationship(edge["from"], edge["to"], edge["type"])
                if edge["type"] == "BELONGS_TO_SECTOR":
                    graph.add_sector_relationship(edge["from"], edge["to"])

        graph.close()

    return kg_data


if __name__ == "__main__":
    import json

    result = asyncio.run(build_complete_knowledge_graph())
    print(json.dumps(result, indent=2))
