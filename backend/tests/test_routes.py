"""Integration tests for the FinGraph API routes.

These tests use httpx + TestClient without spinning up real DB/Redis,
relying on the graceful fallback paths already built into each route.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Build a TestClient that overrides slow startup tasks."""
    with (
        patch("core.background_tasks.build_knowledge_graph", new_callable=AsyncMock),
        patch("core.background_tasks.scrape_and_store_news", new_callable=AsyncMock),
        patch("core.scheduler.start_scheduler"),
        patch("core.scheduler.stop_scheduler"),
        patch("db.postgres.init_db", new_callable=AsyncMock),
        patch("db.redis_client.init_redis", new_callable=AsyncMock),
        patch("db.redis_client.close_redis", new_callable=AsyncMock),
        patch("core.services.truedata_service.TrueDataService"),
    ):
        from main import app
        yield TestClient(app)


# ─── Health ───────────────────────────────────────────────────────────────────


def test_root(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["version"] == "1.0.0"


def test_health_returns_dict(client: TestClient):
    """Health endpoint must return a dict with status key (may be degraded if no DB)."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "services" in body


# ─── Quotes ───────────────────────────────────────────────────────────────────


def test_indices_fallback(client: TestClient):
    """Indices endpoint falls back to static data when NSE is unavailable."""
    with patch("api.routes.quotes.get_nse_fetcher", return_value=None):
        resp = client.get("/api/v1/quotes/indices")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


def test_movers_fallback_empty_db(client: TestClient):
    """Movers endpoint falls back gracefully with empty DB."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("api.routes.quotes.get_nse_fetcher", return_value=None),
        patch("db.postgres.AsyncSessionLocal", return_value=mock_session),
    ):
        resp = client.get("/api/v1/quotes/movers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "gainers" in data["data"]
    assert "losers" in data["data"]


# ─── Fundamentals ─────────────────────────────────────────────────────────────


def test_known_fundamental_returns_sample(client: TestClient):
    """Returns sample data for known symbols without hitting DB."""
    resp = client.get("/api/v1/fundamentals/RELIANCE")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["pe"] is not None


def test_unknown_fundamental_returns_nulls(client: TestClient):
    """Unknown symbols should return null ratios (not random values)."""
    with patch("db.postgres.AsyncSessionLocal") as mock_cls:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_session

        resp = client.get("/api/v1/fundamentals/XYZUNKNOWN999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["pe"] is None
    assert data["data"]["roe"] is None


# ─── Screener ────────────────────────────────────────────────────────────────


def test_screener_templates(client: TestClient):
    resp = client.get("/api/v1/screen/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) > 0


def test_screener_sectors_list(client: TestClient):
    resp = client.get("/api/v1/screen/sectors")
    assert resp.status_code == 200
    data = resp.json()
    assert "Technology" in data["data"] or len(data["data"]) > 0


# ─── Graph ───────────────────────────────────────────────────────────────────


def test_graph_full_returns_sample(client: TestClient):
    """Full graph endpoint returns SAMPLE_GRAPH_DATA when Neo4j unavailable."""
    resp = client.get("/api/v1/graph/full")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "nodes" in data["data"]


def test_graph_enrichment_run_endpoint(client: TestClient):
    with patch(
        "api.routes.graph.run_enrichment",
        new_callable=AsyncMock,
        return_value={"articles_scanned": 3, "created_sector_edges": 2},
    ):
        resp = client.post(
            "/api/v1/graph/enrichment/run",
            json={"limit": 3, "dry_run": True},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["articles_scanned"] == 3


def test_graph_enrichment_status_endpoint(client: TestClient):
    from api.routes import graph as graph_routes

    class _FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def data(self):
            return self._rows

    class _FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def run(self, query, **kwargs):
            if "RETURN type(r) AS type" in query:
                return _FakeResult([
                    {"type": "AFFECTS_COMPANY", "count": 1},
                    {"type": "RELEVANT_TO_SECTOR", "count": 14},
                ])
            return _FakeResult([
                {
                    "article_id": "article_23",
                    "title": "Sample",
                    "rel_type": "RELEVANT_TO_SECTOR",
                    "target_labels": ["Sector", "Entity"],
                    "target": "Capital Goods",
                    "score": 9.5,
                    "match_reason": "article_content",
                    "source_url": "https://example.com/story",
                }
            ])

    class _FakeDriver:
        def session(self, database=None):
            return _FakeSession()

        def close(self):
            return None

    with (
        patch.object(graph_routes.settings, "NEO4J_URI", "neo4j+s://example"),
        patch.object(graph_routes.settings, "NEO4J_PASSWORD", "secret"),
        patch.object(graph_routes.settings, "NEO4J_DATABASE", "neo4j"),
        patch.object(graph_routes.settings, "NEO4J_USERNAME", "neo4j"),
        patch("api.routes.graph.GraphDatabase.driver", return_value=_FakeDriver()),
    ):
        resp = client.get("/api/v1/graph/enrichment/status?limit=5")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["created_by"] == graph_routes.SCRIPT_NAME
    assert len(payload["data"]["relationship_counts"]) == 2


# ─── SEBI ────────────────────────────────────────────────────────────────────


def test_sebi_filings(client: TestClient):
    resp = client.get("/api/v1/sebi/filings")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_sebi_circuit_breakers(client: TestClient):
    resp = client.get("/api/v1/sebi/circuit-breakers")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) > 0


# ─── Graph service unit tests ─────────────────────────────────────────────────


def test_add_relationship_rejects_unknown_rel_type():
    """add_relationship must reject unknown relationship types (Cypher injection guard)."""
    from core.services.graph_service import Neo4jGraph

    graph = Neo4jGraph()
    # No driver configured — but should still validate the type first
    result = graph.add_relationship("RELIANCE", "TCS", "DROP_DATABASE")
    assert result is False


def test_add_relationship_accepts_valid_rel_type():
    """add_relationship with no driver returns False (no crash for valid type)."""
    from core.services.graph_service import Neo4jGraph

    graph = Neo4jGraph()
    result = graph.add_relationship("RELIANCE", "TCS", "COMPETITOR")
    # No driver → False, but no exception
    assert result is False
