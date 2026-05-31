from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DocType(str, Enum):
    PDF = "pdf"
    WEB = "web"
    CSV = "csv"
    JSON = "json"


class Domain(str, Enum):
    MEDICAL = "medical"
    LEGAL = "legal"
    FINANCIAL = "financial"
    SCIENTIFIC = "scientific"
    NEWS = "news"
    GENERAL = "general"


@dataclass
class TemporalDocument:
    text: str
    source_id: str
    version_id: str
    doc_type: DocType
    domain: Domain
    published_date: datetime
    ingested_at: datetime
    source_url: Optional[str] = None
    source_authority: float = 0.5
    page_num: Optional[int] = None
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class ConfidenceObject:
    semantic_score: float
    freshness_score: float
    source_agreement: float
    conflict_type: str
    recommended_action: str
    sources_used: list[str]
    oldest_source_date: datetime
    newest_source_date: datetime
