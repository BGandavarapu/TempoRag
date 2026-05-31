import uuid
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from src.ingestion.document import DocType, Domain, TemporalDocument


def load(
    url: str,
    source_id: str,
    published_date: datetime,
    domain: Domain,
    source_authority: float = 0.5,
) -> TemporalDocument:
    response = httpx.get(url, timeout=30, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup.find_all(["nav", "footer", "script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    return TemporalDocument(
        text=text,
        source_id=source_id,
        version_id=str(uuid.uuid4()),
        doc_type=DocType.WEB,
        domain=domain,
        published_date=published_date,
        ingested_at=datetime.now(timezone.utc),
        source_url=url,
        source_authority=source_authority,
    )
