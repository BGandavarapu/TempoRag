from __future__ import annotations
from datetime import datetime

from src.decay.scorer import freshness_score, combined_score
from src.ingestion.document import Domain


def rerank(
    results: dict,
    domain: Domain,
    alpha: float = 0.7,
    as_of: datetime | None = None,
) -> list[dict]:
    """
    Takes a raw ChromaDB query result dict and returns a sorted list of dicts,
    each with keys: chunk_id, text, metadata, semantic_score, freshness, score.
    """
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    ranked = []
    for chunk_id, text, dist, meta in zip(ids, documents, distances, metadatas):
        # ChromaDB cosine distance: similarity = 1 - distance
        semantic_sim = max(0.0, 1.0 - dist)

        published_date = _parse_date(meta.get("published_date"))
        if published_date is not None:
            fresh = freshness_score(published_date, domain, as_of=as_of)
        else:
            fresh = 0.5

        score = combined_score(semantic_sim, fresh, alpha=alpha)
        ranked.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "metadata": meta,
                "semantic_score": semantic_sim,
                "freshness": fresh,
                "score": score,
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def _parse_date(date_val) -> datetime | None:
    if date_val is None:
        return None
    if isinstance(date_val, datetime):
        return date_val
    try:
        return datetime.fromisoformat(str(date_val))
    except (ValueError, TypeError):
        return None


def mmr_select(
    ranked: list[dict],
    embeddings: list[list[float]],
    top_k: int = 5,
    lambda_mmr: float = 0.5,
) -> list[dict]:
    """
    Maximal Marginal Relevance selection to reduce redundancy.
    ranked: output from rerank(), same order.
    embeddings: embedding vectors parallel to `ranked`.
    Returns top_k items balancing relevance and diversity.
    """
    if not ranked:
        return []
    top_k = min(top_k, len(ranked))

    selected_indices: list[int] = []
    remaining = list(range(len(ranked)))

    while len(selected_indices) < top_k and remaining:
        best_idx = None
        best_mmr = float("-inf")

        for i in remaining:
            relevance = ranked[i]["score"]
            if not selected_indices:
                redundancy = 0.0
            else:
                redundancy = max(
                    _cosine_sim(embeddings[i], embeddings[j])
                    for j in selected_indices
                )
            mmr_score = lambda_mmr * relevance - (1 - lambda_mmr) * redundancy
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = i

        selected_indices.append(best_idx)
        remaining.remove(best_idx)

    return [ranked[i] for i in selected_indices]


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x ** 2 for x in a) ** 0.5
    mag_b = sum(x ** 2 for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
