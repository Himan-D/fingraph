from neo4j import AsyncGraphDatabase
from config import settings
from typing import Optional

driver = None


def _get_neo4j_username() -> str:
    return settings.NEO4J_USERNAME or settings.NEO4J_USER


async def init_neo4j():
    global driver
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(_get_neo4j_username(), settings.NEO4J_PASSWORD),
        max_connection_lifetime=3600,
        max_connection_pool_size=50,
    )
    return driver


async def close_neo4j():
    global driver
    if driver:
        await driver.close()


def get_neo4j():
    return driver


async def execute_query(query: str, parameters: dict = None):
    """Execute a Cypher query"""
    async with driver.session(database=settings.NEO4J_DATABASE) as session:
        result = await session.run(query, parameters or {})
        return await result.data()


async def execute_write(query: str, parameters: dict = None):
    """Execute a write Cypher query"""
    async with driver.session(database=settings.NEO4J_DATABASE) as session:
        result = await session.run(query, parameters or {})
        await result.consume()
        return result
