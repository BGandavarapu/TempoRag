import logging

from src.graph import client
from src.graph.entity_extractor import extract_entities
from src.ingestion.document import TemporalDocument

_log = logging.getLogger(__name__)


def ingest_chunk(doc: TemporalDocument) -> None:
    chunk_id = f"{doc.source_id}_{doc.published_date.date()}_{doc.chunk_index}"
    published_str = doc.published_date.date().isoformat()

    client.execute_query(
        """
        MERGE (c:Chunk {chunk_id: $chunk_id})
        SET c.text = $text,
            c.source_id = $source_id,
            c.version_id = $version_id,
            c.published_date = $published_date,
            c.domain = $domain,
            c.page_num = $page_num,
            c.chunk_index = $chunk_index
        """,
        {
            "chunk_id": chunk_id,
            "text": doc.text,
            "source_id": doc.source_id,
            "version_id": doc.version_id,
            "published_date": published_str,
            "domain": doc.domain.value,
            "page_num": doc.page_num,
            "chunk_index": doc.chunk_index,
        },
    )

    client.execute_query(
        """
        MERGE (s:Source {source_id: $source_id})
        SET s.url = $url,
            s.authority_score = $authority_score,
            s.domain = $domain
        WITH s
        MATCH (c:Chunk {chunk_id: $chunk_id})
        MERGE (c)-[:FROM_SOURCE]->(s)
        """,
        {
            "source_id": doc.source_id,
            "url": doc.source_url or "",
            "authority_score": doc.source_authority,
            "domain": doc.domain.value,
            "chunk_id": chunk_id,
        },
    )

    entities = extract_entities(doc.text)
    for entity in entities:
        client.execute_query(
            """
            MERGE (e:Entity {normalized_name: $normalized_name})
            SET e.name = $name, e.entity_type = $entity_type
            WITH e
            MATCH (c:Chunk {chunk_id: $chunk_id})
            MERGE (c)-[:MENTIONS]->(e)
            """,
            {
                "normalized_name": entity["normalized_name"],
                "name": entity["name"],
                "entity_type": entity["entity_type"],
                "chunk_id": chunk_id,
            },
        )

    client.execute_query(
        """
        MATCH (older:Chunk {source_id: $source_id})
        WHERE older.published_date < $published_date
          AND older.chunk_id <> $chunk_id
        WITH older
        MATCH (newer:Chunk {chunk_id: $chunk_id})
        MERGE (newer)-[:NEXT_VERSION]->(older)
        """,
        {
            "source_id": doc.source_id,
            "published_date": published_str,
            "chunk_id": chunk_id,
        },
    )

    if entities:
        normalized_names = [e["normalized_name"] for e in entities]
        candidates = client.execute_query(
            """
            MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
            WHERE e.normalized_name IN $normalized_names
              AND c.source_id <> $source_id
              AND c.published_date < $published_date
            RETURN DISTINCT c.chunk_id AS chunk_id, c.source_id AS source_id,
                            c.published_date AS published_date
            LIMIT 10
            """,
            {
                "normalized_names": normalized_names,
                "source_id": doc.source_id,
                "published_date": published_str,
            },
        )
        for cand in candidates:
            _log.debug("Conflict candidate: %s -> %s", chunk_id, cand["chunk_id"])
