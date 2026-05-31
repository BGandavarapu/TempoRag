from abc import ABC, abstractmethod
from src.ingestion.document import TemporalDocument


class Chunker(ABC):
    @abstractmethod
    def chunk(self, doc: TemporalDocument) -> list[TemporalDocument]:
        ...
