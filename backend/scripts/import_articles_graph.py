from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ClientError


GRAPHML_NAMESPACE = {"g": "http://graphml.graphdrawing.org/xmlns"}
DEFAULT_GRAPHML_URL = (
    "https://raw.githubusercontent.com/Himan-D/articles-graph/master/"
    "articles_graph.graphml"
)
SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9_]+")


def _safe_graph_name(value: str, fallback: str) -> str:
    cleaned = SAFE_NAME_PATTERN.sub("_", value.strip())
    cleaned = cleaned.strip("_")
    if not cleaned:
        cleaned = fallback
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned


def _load_settings() -> dict[str, str]:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)

    uri = os.getenv("NEO4J_URI", "").strip()
    username = os.getenv("NEO4J_USERNAME", "").strip() or os.getenv("NEO4J_USER", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    database = os.getenv("NEO4J_DATABASE", "neo4j").strip() or "neo4j"

    if not uri or not username or not password:
        raise RuntimeError("Neo4j credentials are incomplete in backend/.env")

    return {
        "uri": uri,
        "username": username,
        "password": password,
        "database": database,
    }


def _download_graphml(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def _parse_graphml(graphml_bytes: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root = ET.fromstring(graphml_bytes)

    key_to_name: dict[str, str] = {}
    for key in root.findall("g:key", GRAPHML_NAMESPACE):
        key_id = key.attrib.get("id")
        attr_name = key.attrib.get("attr.name")
        if key_id and attr_name:
            key_to_name[key_id] = attr_name

    graph = root.find("g:graph", GRAPHML_NAMESPACE)
    if graph is None:
        raise RuntimeError("GraphML payload does not contain a <graph> element")

    nodes: list[dict[str, Any]] = []
    for node in graph.findall("g:node", GRAPHML_NAMESPACE):
        properties = {"graphml_id": node.attrib["id"]}
        for data in node.findall("g:data", GRAPHML_NAMESPACE):
            key_id = data.attrib.get("key")
            attr_name = key_to_name.get(key_id or "")
            if not attr_name:
                continue
            text = (data.text or "").strip()
            if text:
                properties[attr_name] = text

        entity_label = properties.get("label", "Entity")
        nodes.append(
            {
                "graphml_id": properties["graphml_id"],
                "labels": ["Entity", _safe_graph_name(entity_label, "Entity")],
                "properties": properties,
            }
        )

    edges: list[dict[str, Any]] = []
    for edge in graph.findall("g:edge", GRAPHML_NAMESPACE):
        edge_properties: dict[str, Any] = {}
        for data in edge.findall("g:data", GRAPHML_NAMESPACE):
            key_id = data.attrib.get("key")
            attr_name = key_to_name.get(key_id or "")
            if not attr_name:
                continue
            text = (data.text or "").strip()
            if text:
                edge_properties[attr_name] = text

        rel_type = edge_properties.get("type", "RELATED_TO")
        edges.append(
            {
                "source": edge.attrib["source"],
                "target": edge.attrib["target"],
                "type": _safe_graph_name(rel_type, "RELATED_TO").upper(),
                "properties": {
                    **edge_properties,
                    "graphml_edge_id": edge.attrib.get("id", ""),
                },
            }
        )

    return nodes, edges


def _create_constraints(session: Any) -> None:
    session.run(
        """
        CREATE CONSTRAINT entity_graphml_id IF NOT EXISTS
        FOR (n:Entity)
        REQUIRE n.graphml_id IS UNIQUE
        """
    )


def _upsert_nodes(session: Any, nodes: list[dict[str, Any]]) -> None:
    for node in nodes:
        label_string = ":".join(node["labels"])
        session.run(
            f"""
            MERGE (n:{label_string} {{graphml_id: $graphml_id}})
            SET n += $properties
            SET n.import_source = $import_source
            """,
            graphml_id=node["graphml_id"],
            properties=node["properties"],
            import_source="articles_graph.graphml",
        )


def _upsert_edges(session: Any, edges: list[dict[str, Any]]) -> None:
    for edge in edges:
        session.run(
            f"""
            MATCH (source:Entity {{graphml_id: $source}})
            MATCH (target:Entity {{graphml_id: $target}})
            MERGE (source)-[r:{edge['type']}]->(target)
            SET r += $properties
            SET r.import_source = $import_source
            """,
            source=edge["source"],
            target=edge["target"],
            properties=edge["properties"],
            import_source="articles_graph.graphml",
        )


def _count_graph(session: Any) -> dict[str, int]:
    record = session.run(
        """
        MATCH (n:Entity)
        OPTIONAL MATCH ()-[r]->()
        RETURN count(DISTINCT n) AS nodes, count(DISTINCT r) AS relationships
        """
    ).single()
    return {
        "nodes": int(record["nodes"] if record else 0),
        "relationships": int(record["relationships"] if record else 0),
    }


def _resolve_database_name(driver: Any, configured_database: str) -> str:
    if configured_database:
        try:
            with driver.session(database=configured_database) as session:
                session.run("RETURN 1").consume()
            return configured_database
        except ClientError as exc:
            if "DatabaseNotFound" not in getattr(exc, "code", ""):
                raise

    with driver.session() as session:
        databases = session.run("SHOW DATABASES").data()

    for database in databases:
        if database.get("home") and database.get("access") == "read-write":
            return str(database["name"])

    for database in databases:
        if database.get("access") == "read-write" and database.get("type") == "standard":
            return str(database["name"])

    raise RuntimeError("Unable to resolve a writable Neo4j database")


def import_graph(graphml_url: str) -> dict[str, Any]:
    settings = _load_settings()
    nodes, edges = _parse_graphml(_download_graphml(graphml_url))

    driver = GraphDatabase.driver(
        settings["uri"],
        auth=(settings["username"], settings["password"]),
    )
    try:
        database_name = _resolve_database_name(driver, settings["database"])
        with driver.session(database=database_name) as session:
            _create_constraints(session)
            _upsert_nodes(session, nodes)
            _upsert_edges(session, edges)
            counts = _count_graph(session)
    finally:
        driver.close()

    return {
        "graphml_url": graphml_url,
        "database": database_name,
        "imported_nodes": len(nodes),
        "imported_relationships": len(edges),
        "database_counts": counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a GraphML file into Neo4j")
    parser.add_argument("--url", default=DEFAULT_GRAPHML_URL, help="GraphML URL to import")
    args = parser.parse_args()

    result = import_graph(args.url)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()