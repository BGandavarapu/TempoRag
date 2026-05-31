from __future__ import annotations
import chromadb
from chromadb import Collection

_CHROMA_PATH = "data/chroma"
_COLLECTION_NAME = "temporal_rag"
_client: chromadb.PersistentClient | None = None
_collection: Collection | None = None


def _get_collection() -> Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=_CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def contains(source_id: str, published_date) -> bool:
    col = _get_collection()
    if col.count() == 0:
        return False
    date_str = published_date.date().isoformat() if hasattr(published_date, "date") else str(published_date)
    result = col.get(
        where={"$and": [{"source_id": {"$eq": source_id}}, {"published_date": {"$eq": date_str}}]},
        limit=1,
    )
    return len(result["ids"]) > 0


def upsert(chunk_id: str, text: str, embedding: list[float], metadata: dict) -> None:
    _get_collection().upsert(
        ids=[chunk_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata],
    )


def query(embedding: list[float], n_results: int = 5, where: dict | None = None) -> dict:
    kwargs: dict = {"query_embeddings": [embedding], "n_results": n_results}
    if where:
        kwargs["where"] = where
    return _get_collection().query(**kwargs)


def get_collection() -> Collection:
    return _get_collection()
