from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from src.api.query_log import log_query
from src.ingestion.document import ConfidenceObject, DocType, Domain, TemporalDocument
from src.retrieval.retriever import retrieve
from src.synthesis.synthesizer import synthesize

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    domain: str = "medical"
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    recommended_action: str
    freshness_score: float
    source_agreement: float
    conflict_type: str
    sources_used: list[str]
    semantic_score: float


def _dict_to_doc(chunk: dict) -> TemporalDocument:
    meta = chunk.get("metadata", {})
    published_str = meta.get("published_date", "2000-01-01")
    try:
        published = datetime.fromisoformat(published_str)
    except (ValueError, TypeError):
        published = datetime(2000, 1, 1)
    return TemporalDocument(
        text=chunk.get("text", ""),
        source_id=meta.get("source_id", chunk.get("chunk_id", "")),
        version_id=meta.get("version_id", chunk.get("chunk_id", "")),
        doc_type=DocType.PDF,
        domain=Domain(meta.get("domain", "medical")),
        published_date=published,
        ingested_at=datetime.now(timezone.utc),
        chunk_index=meta.get("chunk_index", 0),
    )


@router.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest) -> QueryResponse:
    try:
        domain = Domain(req.domain)
    except ValueError:
        domain = Domain.MEDICAL

    result = retrieve(req.query, domain=domain, top_k=req.top_k)
    docs = [_dict_to_doc(c) for c in result.chunks]
    conf: ConfidenceObject = result.confidence

    synthesis = synthesize(req.query, docs, conf)

    log_query(
        query=req.query,
        recommended_action=conf.recommended_action,
        freshness_score=conf.freshness_score,
        source_count=len(conf.sources_used),
    )

    return QueryResponse(
        answer=synthesis["answer"],
        recommended_action=conf.recommended_action,
        freshness_score=conf.freshness_score,
        source_agreement=conf.source_agreement,
        conflict_type=conf.conflict_type,
        sources_used=conf.sources_used,
        semantic_score=conf.semantic_score,
    )
