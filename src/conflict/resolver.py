import logging
from itertools import combinations

from src.api.query_log import log_conflict
from src.conflict.nli_classifier import classify_pairs
from src.conflict.temporal_resolver import ConflictType, resolve
from src.ingestion.document import TemporalDocument

logger = logging.getLogger(__name__)

_SEVERITY = {
    ConflictType.NONE: 0,
    ConflictType.FLAT: 1,
    ConflictType.TEMPORAL_SUPERSESSION: 2,
}

_MIN_CHUNK_LEN = 200
_MAX_CHUNK_LEN = 1500


def resolve_chunks(chunks: list[TemporalDocument]) -> dict:
    before = len(chunks)
    chunks = [c for c in chunks if _MIN_CHUNK_LEN <= len(c.text.strip()) <= _MAX_CHUNK_LEN]
    filtered = before - len(chunks)
    if filtered:
        logger.info("resolve_chunks: filtered %d chunks (outside %d-%d chars), %d remain",
                    filtered, _MIN_CHUNK_LEN, _MAX_CHUNK_LEN, len(chunks))

    index_pairs = list(combinations(range(len(chunks)), 2))

    if not index_pairs:
        return {
            "conflict_type": ConflictType.NONE,
            "conflicting_pairs": [],
            "all_pairs_results": [],
        }

    text_pairs = [(chunks[i].text, chunks[j].text) for i, j in index_pairs]
    nli_results = classify_pairs(text_pairs)

    worst = ConflictType.NONE
    conflicting_pairs: list[tuple] = []
    all_pairs_results: list[dict] = []

    for (i, j), nli_result in zip(index_pairs, nli_results):
        a, b = chunks[i], chunks[j]
        if b.published_date < a.published_date:
            a, b = b, a

        conflict = resolve(a, b, nli_result)

        all_pairs_results.append(
            {
                "chunk_a": chunks[i],
                "chunk_b": chunks[j],
                "nli_result": nli_result,
                "conflict_type": conflict,
            }
        )

        if _SEVERITY[conflict] > _SEVERITY[worst]:
            worst = conflict

        if conflict != ConflictType.NONE:
            conflicting_pairs.append((chunks[i], chunks[j]))
            try:
                log_conflict(
                    chunk_a_id=f"{a.source_id}_{a.published_date.date()}_{a.chunk_index}",
                    chunk_b_id=f"{b.source_id}_{b.published_date.date()}_{b.chunk_index}",
                    conflict_type=conflict.value,
                    source_a=a.source_id,
                    source_b=b.source_id,
                    date_a=a.published_date.date().isoformat(),
                    date_b=b.published_date.date().isoformat(),
                    date_delta_days=abs((b.published_date - a.published_date).days),
                )
            except Exception:
                logger.warning("resolve_chunks: failed to log conflict to SQLite", exc_info=True)

    return {
        "conflict_type": worst,
        "conflicting_pairs": conflicting_pairs,
        "all_pairs_results": all_pairs_results,
    }
