from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import chromadb

from src.ingestion import pipeline
from src.ingestion.document import Domain
from src.ingestion.loaders import pdf_loader

DEMO_DOCS = [
    {
        "path": "data/sample_docs/who_arv_guidelines_2013.pdf",
        "source_id": "who_arv_guidelines_2013",
        "published_date": datetime(2013, 6, 1),
        "domain": Domain.MEDICAL,
        "source_url": "https://iris.who.int/bitstream/handle/10665/85321/9789241505727_eng.pdf",
        "source_authority": 0.95,
        "page_limit": 150,
    },
    {
        "path": "data/sample_docs/who_arv_guidelines_2016.pdf",
        "source_id": "who_arv_guidelines_2016",
        "published_date": datetime(2016, 1, 1),
        "domain": Domain.MEDICAL,
        "source_url": "https://iris.who.int/bitstream/handle/10665/208825/9789241549684-eng.pdf",
        "source_authority": 0.95,
        "page_limit": 200,
    },
    {
        "path": "data/sample_docs/who_hiv_guidelines_2021.pdf",
        "source_id": "who_hiv_guidelines_2021",
        "published_date": datetime(2021, 1, 1),
        "domain": Domain.MEDICAL,
        "source_url": "https://www.who.int/publications/i/item/9789240031593",
        "source_authority": 0.95,
        "page_limit": 150,
    },
    {
        "path": "data/sample_docs/who_hiv_guidelines_2023.pdf",
        "source_id": "who_hiv_guidelines_2023",
        "published_date": datetime(2023, 7, 1),
        "domain": Domain.MEDICAL,
        "source_url": "https://www.who.int/publications/i/item/9789240086319",
        "source_authority": 0.95,
    },
]


def _already_seeded(chroma_client: chromadb.ClientAPI, source_id: str) -> bool:
    try:
        col = chroma_client.get_collection("temporal_rag")
        results = col.get(where={"source_id": source_id})
        return len(results["ids"]) > 0
    except Exception:
        return False


def main() -> None:
    chroma_client = chromadb.PersistentClient(path="data/chroma")

    for entry in DEMO_DOCS:
        source_id = entry["source_id"]
        published_date = entry["published_date"]
        pdf_path = Path(entry["path"])

        if not pdf_path.exists():
            print(f"SKIP  {source_id} — {pdf_path} not found")
            continue

        if _already_seeded(chroma_client, source_id):
            print(f"SKIP  {source_id} — already seeded")
            continue

        print(f"Seeding {source_id} published {published_date.date()}...", end=" ", flush=True)

        docs = pdf_loader.load(
            path=pdf_path,
            source_id=source_id,
            published_date=published_date,
            domain=entry["domain"],
            source_url=entry.get("source_url"),
            source_authority=entry.get("source_authority", 0.5),
            page_limit=entry.get("page_limit"),
        )

        n_chunks = pipeline.ingest(docs)
        print(f"done ({n_chunks} chunks)")


if __name__ == "__main__":
    main()
