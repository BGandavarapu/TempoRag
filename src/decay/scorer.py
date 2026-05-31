import math
from datetime import datetime, timezone

from src.decay.half_lives import get_half_life
from src.ingestion.document import Domain


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def freshness_score(
    published_date: datetime,
    domain: Domain,
    as_of: datetime = None,
) -> float:
    if as_of is None:
        as_of = _utcnow()
    age_days = (as_of - published_date).total_seconds() / 86400
    if age_days <= 0:
        return 1.0
    score = math.exp(-math.log(2) * age_days / get_half_life(domain))
    return max(0.0, min(1.0, score))


def combined_score(
    semantic_sim: float,
    freshness: float,
    alpha: float = 0.7,
) -> float:
    return alpha * semantic_sim + (1 - alpha) * freshness
