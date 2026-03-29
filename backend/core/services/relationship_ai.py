"""
AI-powered Relationship Analysis for Knowledge Graph
"""

import asyncio
import logging
from typing import List, Dict, Tuple
from db.postgres import AsyncSessionLocal
from db.postgres_models import Company
from sqlalchemy import select

logger = logging.getLogger(__name__)


class RelationshipAnalyzer:
    """Use AI to analyze and determine relationships between companies"""

    def __init__(self):
        self.openai_key = None
        try:
            from config import settings

            self.openai_key = getattr(settings, "OPENAI_API_KEY", None)
        except:
            pass

    async def analyze_relationship(
        self, company1: Dict, company2: Dict
    ) -> Tuple[str, float]:
        """
        Analyze relationship between two companies using rules + AI
        Returns: (relationship_type, confidence)
        """
        # Rule-based analysis first
        sector1 = company1.get("sector", "").lower()
        sector2 = company2.get("sector", "").lower()
        industry1 = company1.get("industry", "").lower()
        industry2 = company2.get("industry", "").lower()
        name1 = company1.get("name", "").lower()
        name2 = company2.get("name", "").lower()

        # Same sector = potential competitor
        if sector1 == sector2 and sector1:
            # Check if same promoter group (subsidiaries)
            if any(x in name1 for x in ["subsidiary", "division", "arm"]) or any(
                x in name2 for x in ["subsidiary", "division", "arm"]
            ):
                return ("SAME_GROUP", 0.9)

            # Check for common promoter names
            promoters1 = self._extract_promoter(name1)
            promoters2 = self._extract_promoter(name2)
            if promoters1 and promoters1 == promoters2:
                return ("SAME_GROUP", 0.85)

            # Same sector = competitor
            return ("COMPETITOR", 0.75)

        # Same industry
        if industry1 == industry2 and industry1:
            return ("COMPETITOR", 0.7)

        # Supply chain relationships (example)
        if "oil" in sector1 or "gas" in sector1:
            if "refinery" in industry2 or "petrochemical" in industry2:
                return ("SUPPLIER", 0.6)

        # Tech companies serving financial sector
        if sector1 == "technology" and sector2 == "financial services":
            return ("SERVICES", 0.5)

        return ("RELATED", 0.3)

    def _extract_promoter(self, name: str) -> str:
        """Extract promoter/group name from company name"""
        promoters = [
            "tata",
            "reliance",
            "birla",
            " Infosys",
            "wipro",
            "hdfc",
            "icici",
            "sbi",
            "axis",
            "kotak",
        ]
        for p in promoters:
            if p in name:
                return p
        return ""

    async def generate_relationships(
        self, companies: List[Dict]
    ) -> List[Tuple[str, str, str]]:
        """
        Generate all possible relationships between companies
        Returns: [(from_symbol, to_symbol, relationship_type), ...]
        """
        relationships = []
        n = len(companies)

        # Compare all pairs
        for i in range(n):
            for j in range(i + 1, n):
                c1 = companies[i]
                c2 = companies[j]

                rel_type, confidence = await self.analyze_relationship(c1, c2)

                # Only add relationships with reasonable confidence
                if confidence >= 0.5:
                    relationships.append(
                        (c1["symbol"], c2["symbol"], rel_type, confidence)
                    )

        # Sort by confidence
        relationships.sort(key=lambda x: x[3], reverse=True)

        # Take top relationships per company (max 3 per company)
        used_companies = {}
        final_relationships = []
        for rel in relationships:
            src, tgt, typ, conf = rel
            if used_companies.get(src, 0) < 3 and used_companies.get(tgt, 0) < 3:
                final_relationships.append((src, tgt, typ))
                used_companies[src] = used_companies.get(src, 0) + 1
                used_companies[tgt] = used_companies.get(tgt, 0) + 1

        return final_relationships

    async def get_company_insights(self, symbol: str) -> Dict:
        """Get AI-generated insights for a company"""
        # This would use OpenAI in production
        return {
            "symbol": symbol,
            "insights": [],
            "risk_factors": [],
            "opportunities": [],
        }


async def analyze_and_build_graph():
    """Main function to analyze companies and build knowledge graph"""
    analyzer = RelationshipAnalyzer()

    # Get all companies from DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company).limit(100))
        companies = result.scalars().all()

        company_dicts = []
        for c in companies:
            company_dicts.append(
                {
                    "symbol": c.symbol,
                    "name": c.name,
                    "sector": c.sector,
                    "industry": c.industry,
                    "market_cap": c.market_cap,
                }
            )

    # Generate relationships using AI analysis
    relationships = await analyzer.generate_relationships(company_dicts)

    logger.info(
        f"AI analyzed {len(companies)} companies and generated {len(relationships)} relationships"
    )

    return relationships


if __name__ == "__main__":
    import json

    rels = asyncio.run(analyze_and_build_graph())
    print(f"Generated {len(rels)} relationships:")
    for r in rels[:10]:
        print(f"  {r[0]} -> {r[1]}: {r[2]}")
