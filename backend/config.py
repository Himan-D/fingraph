from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fingraph"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fingraph"

    # Neo4j
    NEO4J_URI: str = "neo4j+s://c8d361db.databases.neo4j.io"
    NEO4J_USER: str = "c8d361db"
    NEO4J_PASSWORD: str = "d-Qc50YuBRO8OTGWvy8bFdT_xvkaLXg2G5F4ytIDOPw"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_USERNAME: str = "c8d361db"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # TrueData
    TRUEDATA_URL: str = "wss://marketdata.truedata.in"
    TRUEDATA_USERNAME: str = ""
    TRUEDATA_PASSWORD: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Crawl4AI
    CRAWL4AI_URL: str = "http://localhost:11202"

    # App
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
