from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


COMPANY_SUFFIX_PATTERN = re.compile(
    r"\b(limited|ltd|inc|corp|corporation|company|co|plc)\b",
    re.IGNORECASE,
)
NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")


def _normalize_name(value: str) -> str:
    lowered = value.strip().lower()
    lowered = COMPANY_SUFFIX_PATTERN.sub(" ", lowered)
    lowered = NON_ALNUM_PATTERN.sub(" ", lowered)
    return " ".join(part for part in lowered.split() if part)


def _load_settings() -> tuple[str, str, str, str]:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    uri = os.getenv("NEO4J_URI", "").strip()
    username = (os.getenv("NEO4J_USERNAME", "") or os.getenv("NEO4J_USER", "")).strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    database = (os.getenv("NEO4J_DATABASE", "") or "neo4j").strip()
    if not uri or not username or not password:
        raise RuntimeError("Neo4j credentials are incomplete in backend/.env")
    return uri, username, password, database


def main() -> None:
    uri, username, password, database = _load_settings()
    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        with driver.session(database=database) as session:
            session.run(
                """
                CREATE INDEX entity_canonical_name IF NOT EXISTS
                FOR (n:Entity)
                ON (n.canonical_name)
                """
            ).consume()
            session.run(
                """
                CREATE INDEX entity_source_graph IF NOT EXISTS
                FOR (n:Entity)
                ON (n.source_graph)
                """
            ).consume()

            company_nodes = session.run(
                """
                MATCH (c:Company)
                RETURN elementId(c) AS element_id,
                       c.symbol AS symbol,
                       coalesce(c.name, c.symbol) AS display_name
                """
            ).data()
            for node in company_nodes:
                session.run(
                    """
                    MATCH (c:Company)
                    WHERE elementId(c) = $element_id
                    SET c:Entity,
                        c.entity_type = 'Company',
                        c.display_name = $display_name,
                        c.canonical_name = $canonical_name,
                        c.source_graph = 'finance_graph'
                    """,
                    element_id=node["element_id"],
                    display_name=node["display_name"],
                    canonical_name=_normalize_name(node["display_name"]),
                ).consume()

            sector_nodes = session.run(
                """
                MATCH (s:Sector)
                RETURN elementId(s) AS element_id,
                       s.name AS display_name
                """
            ).data()
            for node in sector_nodes:
                display_name = node.get("display_name") or ""
                session.run(
                    """
                    MATCH (s:Sector)
                    WHERE elementId(s) = $element_id
                    SET s:Entity,
                        s.entity_type = 'Sector',
                        s.display_name = $display_name,
                        s.canonical_name = $canonical_name,
                        s.source_graph = 'finance_graph'
                    """,
                    element_id=node["element_id"],
                    display_name=display_name,
                    canonical_name=_normalize_name(display_name),
                ).consume()

            article_entities = session.run(
                """
                MATCH (n:Entity)
                WHERE n.import_source = 'articles_graph.graphml'
                RETURN elementId(n) AS element_id,
                       n.label AS graph_label,
                       n.name AS name,
                       n.title AS title,
                       n.graphml_id AS graphml_id
                """
            ).data()
            for node in article_entities:
                display_name = node.get("name") or node.get("title") or node.get("graphml_id") or ""
                entity_type = node.get("graph_label") or "Entity"
                session.run(
                    """
                    MATCH (n:Entity)
                    WHERE elementId(n) = $element_id
                    SET n.entity_type = $entity_type,
                        n.display_name = $display_name,
                        n.canonical_name = $canonical_name,
                        n.source_graph = 'articles_graph'
                    """,
                    element_id=node["element_id"],
                    entity_type=entity_type,
                    display_name=display_name,
                    canonical_name=_normalize_name(display_name),
                ).consume()

            session.run(
                """
                MATCH (article_entity:Entity {source_graph: 'articles_graph'})-[r:RELATED_TO_FINANCE_ENTITY]->(finance_entity:Entity {source_graph: 'finance_graph'})
                DELETE r
                """
            ).consume()
            matches_summary = session.run(
                """
                MATCH (article_entity:Entity {source_graph: 'articles_graph'})
                MATCH (finance_entity:Entity {source_graph: 'finance_graph'})
                WHERE article_entity.canonical_name IS NOT NULL
                  AND article_entity.canonical_name <> ''
                  AND article_entity.canonical_name = finance_entity.canonical_name
                MERGE (article_entity)-[r:RELATED_TO_FINANCE_ENTITY]->(finance_entity)
                SET r.match_type = 'canonical_name',
                    r.created_by = 'harmonize_graph_entities'
                RETURN count(r) AS count
                """
            ).single()

            verification = session.run(
                """
                MATCH (n:Entity)
                RETURN
                    count(CASE WHEN n.source_graph = 'articles_graph' THEN 1 END) AS article_entities,
                    count(CASE WHEN n.source_graph = 'finance_graph' THEN 1 END) AS finance_entities
                """
            ).single()

        print(
            json.dumps(
                {
                    "article_entities": int(verification["article_entities"]),
                    "finance_entities": int(verification["finance_entities"]),
                    "cross_graph_links": int(matches_summary["count"] if matches_summary else 0),
                },
                indent=2,
            )
        )
    finally:
        driver.close()


if __name__ == "__main__":
    main()