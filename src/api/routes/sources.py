from collections import defaultdict

import chromadb
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SourceInfo(BaseModel):
    source_id: str
    chunk_count: int
    published_date: str
    domain: str
    source_authority: float


@router.get("/sources", response_model=list[SourceInfo])
def list_sources() -> list[SourceInfo]:
    try:
        col = chromadb.PersistentClient(path="data/chroma").get_collection("temporal_rag")
        result = col.get(include=["metadatas"])
    except Exception:
        return []

    buckets: dict[str, dict] = defaultdict(lambda: {
        "count": 0, "published_date": "", "domain": "general", "source_authority": 0.5
    })
    for meta in result["metadatas"]:
        if not meta:
            continue
        sid = meta.get("source_id", "unknown")
        b = buckets[sid]
        b["count"] += 1
        if not b["published_date"]:
            b["published_date"] = meta.get("published_date", "")
            b["domain"] = meta.get("domain", "general")

    return [
        SourceInfo(
            source_id=sid,
            chunk_count=b["count"],
            published_date=b["published_date"],
            domain=b["domain"],
            source_authority=b.get("source_authority", 0.95),
        )
        for sid, b in sorted(buckets.items())
    ]
