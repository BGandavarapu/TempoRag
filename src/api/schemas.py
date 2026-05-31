from pydantic import BaseModel


class DomainStats(BaseModel):
    domain: str
    chunk_count: int
    avg_freshness: float
    stale_count: int


class ConflictEntry(BaseModel):
    chunk_a_id: str
    chunk_b_id: str
    conflict_type: str
    source_a: str
    source_b: str
    date_a: str
    date_b: str
    date_delta_days: int


class QueryEntry(BaseModel):
    query: str
    recommended_action: str
    freshness_score: float
    source_count: int
    timestamp: str


class DashboardSnapshot(BaseModel):
    domains: list[DomainStats]
    recent_conflicts: list[ConflictEntry]
    recent_queries: list[QueryEntry]
    total_chunks: int
    avg_freshness_overall: float
