from dataclasses import replace
from src.chunking.base import Chunker
from src.ingestion.document import TemporalDocument

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _split(text: str, separators: list[str]) -> list[str]:
    if not separators:
        return [text]
    sep = separators[0]
    if sep == "":
        return list(text)
    parts = text.split(sep)
    if len(parts) == 1:
        return _split(text, separators[1:])
    result = []
    for part in parts:
        if part:
            result.append(part)
    return result


def _merge(splits: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for s in splits:
        s_len = len(s)
        if current_len + s_len > chunk_size and current:
            chunks.append(" ".join(current))
            overlap: list[str] = []
            overlap_len = 0
            for piece in reversed(current):
                if overlap_len + len(piece) > chunk_overlap:
                    break
                overlap.insert(0, piece)
                overlap_len += len(piece) + 1
            current = overlap
            current_len = overlap_len
        current.append(s)
        current_len += s_len + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


class RecursiveChunker(Chunker):
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, doc: TemporalDocument) -> list[TemporalDocument]:
        if len(doc.text) <= self.chunk_size:
            return [doc]

        splits = _split(doc.text, _SEPARATORS)
        merged = _merge(splits, self.chunk_size, self.chunk_overlap)

        return [
            replace(doc, text=text, chunk_index=i)
            for i, text in enumerate(merged)
            if text.strip()
        ]
