from datetime import datetime

from src.conflict.temporal_resolver import ConflictType
from src.ingestion.document import ConfidenceObject, TemporalDocument

_SOURCE_AGREEMENT = {
    ConflictType.NONE: 1.0,
    ConflictType.TEMPORAL_SUPERSESSION: 0.5,
    ConflictType.FLAT: 0.0,
}


def build_confidence_object(
    chunks: list[TemporalDocument],
    semantic_scores: list[float],
    conflict_result: dict,
    decay_scores: list[float],
) -> ConfidenceObject:
    top3 = sorted(semantic_scores, reverse=True)[:3]
    semantic_score = sum(top3) / len(top3) if top3 else 0.0

    total_weight = sum(semantic_scores)
    if total_weight > 0:
        freshness_score = (
            sum(d * s for d, s in zip(decay_scores, semantic_scores)) / total_weight
        )
    else:
        freshness_score = sum(decay_scores) / len(decay_scores) if decay_scores else 0.0

    conflict_type: ConflictType = conflict_result.get("conflict_type", ConflictType.NONE)
    source_agreement = _SOURCE_AGREEMENT[conflict_type]

    if conflict_type == ConflictType.FLAT:
        recommended_action = "surface_conflict"
    elif conflict_type == ConflictType.TEMPORAL_SUPERSESSION:
        recommended_action = "surface_supersession"
    elif freshness_score < 0.1:
        recommended_action = "refuse"
    elif freshness_score < 0.4:
        recommended_action = "warn_stale"
    else:
        recommended_action = "answer"

    sources_used = list(dict.fromkeys(c.source_id for c in chunks))
    oldest = min((c.published_date for c in chunks), default=datetime(1970, 1, 1))
    newest = max((c.published_date for c in chunks), default=datetime(1970, 1, 1))

    return ConfidenceObject(
        semantic_score=semantic_score,
        freshness_score=freshness_score,
        source_agreement=source_agreement,
        conflict_type=conflict_type.value,
        recommended_action=recommended_action,
        sources_used=sources_used,
        oldest_source_date=oldest,
        newest_source_date=newest,
    )
