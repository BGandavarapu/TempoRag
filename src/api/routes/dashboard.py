from datetime import datetime

import chromadb
from fastapi import APIRouter

from src.api.query_log import get_recent_conflicts, get_recent_queries
from src.api.schemas import DashboardSnapshot, DomainStats
from src.decay.scorer import freshness_score
from src.ingestion.document import Domain

router = APIRouter()


def _domain_stats() -> tuple[list[DomainStats], int, float]:
    try:
        col = chromadb.PersistentClient(path="data/chroma").get_collection("temporal_rag")
        results = col.get(include=["metadatas"])
    except Exception:
        return [], 0, 0.0

    now = datetime.now()
    buckets: dict[str, dict] = {}

    for meta in results["metadatas"]:
        if not meta:
            continue
        domain_str = meta.get("domain", "general")
        published_str = meta.get("published_date", "")
        try:
            published = datetime.fromisoformat(published_str)
            domain_enum = Domain(domain_str)
        except (ValueError, TypeError):
            continue

        score = freshness_score(published, domain_enum, as_of=now)
        b = buckets.setdefault(domain_str, {"count": 0, "freshness_sum": 0.0, "stale": 0})
        b["count"] += 1
        b["freshness_sum"] += score
        if score < 0.4:
            b["stale"] += 1

    stats: list[DomainStats] = []
    total = 0
    total_freshness = 0.0

    for domain_str, b in buckets.items():
        n = b["count"]
        avg = b["freshness_sum"] / n
        stats.append(
            DomainStats(
                domain=domain_str,
                chunk_count=n,
                avg_freshness=round(avg, 3),
                stale_count=b["stale"],
            )
        )
        total += n
        total_freshness += b["freshness_sum"]

    overall = round(total_freshness / total, 3) if total else 0.0
    return stats, total, overall


@router.get("/dashboard/snapshot", response_model=DashboardSnapshot)
def get_snapshot() -> DashboardSnapshot:
    domain_stats, total_chunks, avg_freshness = _domain_stats()
    return DashboardSnapshot(
        domains=domain_stats,
        recent_conflicts=get_recent_conflicts(limit=20),
        recent_queries=get_recent_queries(limit=10),
        total_chunks=total_chunks,
        avg_freshness_overall=avg_freshness,
    )
