import os

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "password123"),
            ),
            max_connection_pool_size=10,
        )
    return _driver


def _reset_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def execute_query(cypher: str, params: dict | None = None) -> list[dict]:
    for attempt in range(2):
        try:
            with _get_driver().session() as session:
                result = session.run(cypher, params or {})
                return [dict(record) for record in result]
        except ServiceUnavailable:
            if attempt == 1:
                raise
            _reset_driver()
    return []
