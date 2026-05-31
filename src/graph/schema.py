from src.graph import client


def create_constraints() -> None:
    client.execute_query(
        "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE"
    )
    client.execute_query(
        "CREATE CONSTRAINT entity_normalized_name IF NOT EXISTS "
        "FOR (e:Entity) REQUIRE e.normalized_name IS UNIQUE"
    )
    client.execute_query(
        "CREATE CONSTRAINT source_source_id IF NOT EXISTS "
        "FOR (s:Source) REQUIRE s.source_id IS UNIQUE"
    )


def create_indexes() -> None:
    client.execute_query(
        "CREATE INDEX chunk_published_date IF NOT EXISTS "
        "FOR (c:Chunk) ON (c.published_date)"
    )
    client.execute_query(
        "CREATE INDEX chunk_domain IF NOT EXISTS FOR (c:Chunk) ON (c.domain)"
    )
