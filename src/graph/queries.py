from src.graph.client import execute_query


def get_chunks_by_source(source_id: str) -> list[dict]:
    return execute_query(
        "MATCH (c:Chunk)-[:FROM_SOURCE]->(s:Source {source_id: $sid}) RETURN c",
        {"sid": source_id},
    )


def get_superseding_chunks(chunk_id: str) -> list[dict]:
    """Return chunks that supersede the given chunk (newer versions)."""
    return execute_query(
        """
        MATCH (newer:Chunk)-[:SUPERSEDES]->(c:Chunk {chunk_id: $cid})
        RETURN newer
        """,
        {"cid": chunk_id},
    )


def get_contradicting_chunks(chunk_id: str) -> list[dict]:
    return execute_query(
        """
        MATCH (c:Chunk {chunk_id: $cid})-[:CONTRADICTS]-(other:Chunk)
        RETURN other
        """,
        {"cid": chunk_id},
    )


def get_confirming_chunks(chunk_id: str) -> list[dict]:
    return execute_query(
        """
        MATCH (c:Chunk {chunk_id: $cid})-[:CONFIRMS]-(other:Chunk)
        RETURN other
        """,
        {"cid": chunk_id},
    )


def get_chunks_by_entity(entity_name: str, limit: int = 10) -> list[dict]:
    return execute_query(
        """
        MATCH (c:Chunk)-[:MENTIONS]->(e:Entity {name: $name})
        RETURN c
        LIMIT $limit
        """,
        {"name": entity_name, "limit": limit},
    )


def get_temporal_neighbors(chunk_id: str) -> list[dict]:
    """Return chunks from the same source that are the next/previous version."""
    return execute_query(
        """
        MATCH (c:Chunk {chunk_id: $cid})-[:NEXT_VERSION]-(neighbor:Chunk)
        RETURN neighbor
        """,
        {"cid": chunk_id},
    )


def get_chunk_metadata(chunk_ids: list[str]) -> list[dict]:
    return execute_query(
        """
        MATCH (c:Chunk)
        WHERE c.chunk_id IN $ids
        RETURN c.chunk_id AS chunk_id, c.source_id AS source_id,
               c.published_date AS published_date, c.domain AS domain,
               c.source_authority AS source_authority
        """,
        {"ids": chunk_ids},
    )


def count_source_agreements(chunk_ids: list[str]) -> float:
    """Return fraction of chunk pairs that CONFIRM each other (0-1)."""
    if len(chunk_ids) < 2:
        return 1.0
    result = execute_query(
        """
        MATCH (a:Chunk)-[:CONFIRMS]-(b:Chunk)
        WHERE a.chunk_id IN $ids AND b.chunk_id IN $ids AND a.chunk_id < b.chunk_id
        RETURN count(*) AS confirms
        """,
        {"ids": chunk_ids},
    )
    confirms = result[0]["confirms"] if result else 0
    pairs = len(chunk_ids) * (len(chunk_ids) - 1) // 2
    return confirms / pairs if pairs > 0 else 1.0
