"""
Neo4j Knowledge Graph Setup
Creates constraints and initial data
"""

from neo4j import GraphDatabase
from config import settings


def setup_neo4j():
    """Setup Neo4j constraints and indexes"""
    driver = GraphDatabase.driver(
        settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

    with driver.session() as session:
        # Create constraints
        session.run("""
            CREATE CONSTRAINT company_symbol IF NOT EXISTS
            FOR (c:Company) REQUIRE c.symbol IS UNIQUE
        """)

        session.run("""
            CREATE CONSTRAINT promoter_name IF NOT EXISTS
            FOR (p:Promoter) REQUIRE p.name IS UNIQUE
        """)

        session.run("""
            CREATE CONSTRAINT kmp_din IF NOT EXISTS
            FOR (k:KMP) REQUIRE k.din IS UNIQUE
        """)

        session.run("""
            CREATE CONSTRAINT index_name IF NOT EXISTS
            FOR (i:Index) REQUIRE i.name IS UNIQUE
        """)

        # Create indexes
        session.run("""
            CREATE INDEX company_sector IF NOT EXISTS
            FOR (c:Company) ON (c.sector)
        """)

        session.run("""
            CREATE INDEX promoter_company IF NOT EXISTS
            FOR (p:Promoter)-[r:PROMOTER_OF]->(c:Company)
            ON r.holding
        """)

        print("Neo4j constraints and indexes created successfully!")

    driver.close()


def create_sample_data():
    """Create sample knowledge graph data"""
    driver = GraphDatabase.driver(
        settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

    with driver.session() as session:
        # Create sample companies
        session.run("""
            MERGE (c:Company {symbol: 'RELIANCE'})
            SET c.name = 'Reliance Industries Ltd',
                c.sector = 'Energy',
                c.industry = 'Oil & Gas',
                c.market_cap = 1850000
        """)

        session.run("""
            MERGE (c:Company {symbol: 'TCS'})
            SET c.name = 'Tata Consultancy Services',
                c.sector = 'Technology',
                c.industry = 'IT Services',
                c.market_cap = 1450000
        """)

        session.run("""
            MERGE (c:Company {symbol: 'HDFCBANK'})
            SET c.name = 'HDFC Bank Ltd',
                c.sector = 'Financial Services',
                c.industry = 'Banking',
                c.market_cap = 1250000
        """)

        # Create sample relationships
        session.run("""
            MATCH (c:Company {symbol: 'RELIANCE'})
            MERGE (p:Promoter {name: 'Mukesh Ambani'})
            MERGE (p)-[:PROMOTER_OF {holding: 49.4}]->(c)
        """)

        session.run("""
            MATCH (c:Company {symbol: 'TCS'})
            MERGE (p:Promoter {name: 'Tata Sons'})
            MERGE (p)-[:PROMOTER_OF {holding: 72.3}]->(c)
        """)

        # Create sector relationship
        session.run("""
            MATCH (c:Company)
            MERGE (s:Sector {name: c.sector})
            MERGE (c)-[:BELONGS_TO_SECTOR]->(s)
        """)

        # Create index membership
        session.run("""
            MERGE (idx:Index {name: 'NIFTY50'})
            WITH idx
            MATCH (c:Company)
            WHERE c.symbol IN ['RELIANCE', 'TCS', 'HDFCBANK']
            MERGE (c)-[:PART_OF_INDEX {weight: 1.0}]->(idx)
        """)

        print("Sample knowledge graph data created!")

    driver.close()


if __name__ == "__main__":
    setup_neo4j()
    create_sample_data()
