from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from src.embedding.embedder import embed
from src.embedding.vector_store import query as chroma_query
from src.ingestion.document import ConfidenceObject, Domain
from src.graph.queries import count_source_agreements, get_superseding_chunks
from src.retrieval.reranker import mmr_select, rerank


@dataclass
class RetrievalResult:
    chunks: list[dict]
    confidence: ConfidenceObject


def retrieve(
    query_text: str,
    domain: Domain,
    top_k: int = 5,
    n_candidates: int = 20,
    alpha: float = 0.7,
    lambda_mmr: float = 0.5,
    where: dict | None = None,
    as_of: datetime | None = None,
) -> RetrievalResult:
    """
    Full retrieval pipeline:
      1. Embed query
      2. ANN search in ChromaDB (n_candidates)
      3. Temporal rerank (semantic × freshness)
      4. MMR deduplication
      5. Filter superseded chunks
      6. Build ConfidenceObject
    """
    query_embedding = embed(query_text)

    raw = chroma_query(query_embedding, n_results=n_candidates, where=where)

    ranked = rerank(raw, domain=domain, alpha=alpha, as_of=as_of)

    # Fetch embeddings for MMR — reuse what chromadb already returned via include
    # (chromadb by default returns distances, not embeddings in query results)
    # We re-embed each candidate text since chromadb doesn't return stored vectors.
    candidate_texts = [r["text"] for r in ranked]
    candidate_embeddings = (
        _embed_candidates(candidate_texts) if len(ranked) > top_k else []
    )

    if candidate_embeddings:
        selected = mmr_select(ranked, candidate_embeddings, top_k=top_k, lambda_mmr=lambda_mmr)
    else:
        selected = ranked[:top_k]

    selected = _filter_superseded(selected)

    confidence = _build_confidence(selected, domain, as_of=as_of)
    return RetrievalResult(chunks=selected, confidence=confidence)


def _embed_candidates(texts: list[str]) -> list[list[float]]:
    from src.embedding.embedder import embed_batch
    return embed_batch(texts)


def _filter_superseded(chunks: list[dict]) -> list[dict]:
    """Drop chunks that have a newer superseding chunk already in the result set."""
    chunk_ids_in_result = {c["chunk_id"] for c in chunks}
    kept = []
    for chunk in chunks:
        try:
            superseding = get_superseding_chunks(chunk["chunk_id"])
        except Exception:
            # Neo4j unavailable — skip filter, return chunk as-is
            kept.append(chunk)
            continue
        newer_ids = {r.get("newer", {}).get("chunk_id") for r in superseding if r.get("newer")}
        if newer_ids & chunk_ids_in_result:
            continue
        kept.append(chunk)
    return kept


def _build_confidence(
    chunks: list[dict],
    domain: Domain,
    as_of: datetime | None,
) -> ConfidenceObject:
    if not chunks:
        return ConfidenceObject(
            semantic_score=0.0,
            freshness_score=0.0,
            source_agreement=0.0,
            conflict_type="none",
            recommended_action="refuse",
            sources_used=[],
            oldest_source_date=datetime.min,
            newest_source_date=datetime.min,
        )

    semantic_score = sum(c["semantic_score"] for c in chunks) / len(chunks)
    freshness_avg = sum(c["freshness"] for c in chunks) / len(chunks)

    dates = [_parse_date(c["metadata"].get("published_date")) for c in chunks]
    dates = [d for d in dates if d is not None]
    oldest = min(dates) if dates else datetime.min
    newest = max(dates) if dates else datetime.min

    chunk_ids = [c["chunk_id"] for c in chunks]
    try:
        source_agreement = count_source_agreements(chunk_ids)
    except Exception:
        source_agreement = 1.0

    sources_used = list({c["metadata"].get("source_id", c["chunk_id"]) for c in chunks})

    if freshness_avg < 0.3:
        recommended_action = "warn_stale"
    elif source_agreement < 0.4:
        recommended_action = "surface_conflict"
    else:
        recommended_action = "answer"

    return ConfidenceObject(
        semantic_score=semantic_score,
        freshness_score=freshness_avg,
        source_agreement=source_agreement,
        conflict_type="none",
        recommended_action=recommended_action,
        sources_used=sources_used,
        oldest_source_date=oldest,
        newest_source_date=newest,
    )


def _parse_date(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None
