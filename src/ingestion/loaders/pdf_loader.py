import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import fitz
import pdfplumber

from src.ingestion.document import DocType, Domain, TemporalDocument


def load(
    path: str | Path,
    source_id: str,
    published_date: datetime,
    domain: Domain,
    source_url: Optional[str] = None,
    source_authority: float = 0.5,
    page_limit: Optional[int] = None,
) -> list[TemporalDocument]:
    path = Path(path)
    ingested_at = datetime.now(timezone.utc)
    docs = []

    with fitz.open(str(path)) as fitz_doc:
        n_pages = len(fitz_doc)
        if page_limit is not None:
            n_pages = min(n_pages, page_limit)

        for page_num in range(n_pages):
            text = fitz_doc[page_num].get_text("text").strip()

            # One pdfplumber context per page — opened, used, and closed immediately
            # so extract_tables() cache and page objects are freed after each iteration.
            with pdfplumber.open(str(path)) as p:
                tables = p.pages[page_num].extract_tables()

            if tables:
                text = f"{text}\n\n{_tables_to_markdown(tables)}".strip()

            if not text:
                continue

            docs.append(
                TemporalDocument(
                    text=text,
                    source_id=source_id,
                    version_id=str(uuid.uuid4()),
                    doc_type=DocType.PDF,
                    domain=domain,
                    published_date=published_date,
                    ingested_at=ingested_at,
                    source_url=source_url,
                    source_authority=source_authority,
                    page_num=page_num,
                    chunk_index=page_num,
                )
            )

    return docs


def _tables_to_markdown(tables: list[list[list]]) -> str:
    parts = []
    for table in tables:
        if not table:
            continue
        header, *rows = table
        lines = [
            "| " + " | ".join(str(c or "") for c in header) + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]
        for row in rows:
            lines.append("| " + " | ".join(str(c or "") for c in row) + " |")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)
