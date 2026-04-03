from config import Settings


def test_neo4j_defaults_are_safe(monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_USER", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

    settings = Settings(_env_file=None)

    assert settings.NEO4J_URI == ""
    assert settings.NEO4J_PASSWORD == ""
    assert settings.NEO4J_USER == "neo4j"
