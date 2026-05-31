import logging
import math
from dataclasses import replace

from src.ingestion.document import TemporalDocument
from src.chunking.recursive_chunker import RecursiveChunker
from src.embedding import embedder
from src.embedding import vector_store
from src.graph import builder

logger = logging.getLogger(__name__)

_chunker = RecursiveChunker(chunk_size=512, chunk_overlap=50)
_BATCH_SIZE = 32


def ingest(docs: list[TemporalDocument]) -> int:
    if not docs:
        return 0

    first = docs[0]
    if vector_store.contains(first.source_id, first.published_date):
        logger.info("already ingested, skipping: source_id=%s date=%s", first.source_id, first.published_date.date())
        return 0

    chunks: list[TemporalDocument] = []
    for doc in docs:
        chunks.extend(_chunker.chunk(doc))

    chunks = [replace(chunk, chunk_index=i) for i, chunk in enumerate(chunks)]

    total_batches = math.ceil(len(chunks) / _BATCH_SIZE)
    for batch_num, batch_start in enumerate(range(0, len(chunks), _BATCH_SIZE), start=1):
        batch = chunks[batch_start : batch_start + _BATCH_SIZE]
        embeddings = embedder.embed_batch([c.text for c in batch])

        for chunk, embedding in zip(batch, embeddings):
            chunk_id = f"{chunk.source_id}_{chunk.published_date.date()}_{chunk.chunk_index}"
            metadata = {
                "source_id": chunk.source_id,
                "version_id": chunk.version_id,
                "published_date": chunk.published_date.date().isoformat(),
                "domain": chunk.domain.value,
                "chunk_index": chunk.chunk_index,
            }
            vector_store.upsert(chunk_id, chunk.text, embedding, metadata)
            builder.ingest_chunk(chunk)

        print(f"  batch {batch_num}/{total_batches} — {len(batch)} chunks embedded and stored")

    logger.info("ingested %d chunks from source_id=%s", len(chunks), first.source_id)
    return len(chunks)
