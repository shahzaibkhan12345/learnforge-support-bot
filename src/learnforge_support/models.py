from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    """A searchable knowledge-base record and its citation metadata."""

    chunk_id: str
    text: str
    source: str
    document_type: str
    document_id: str
    title: str
    chunk_index: int
    last_updated: str | None
    effective_date: str | None
    contains_stale_reference: bool

    def metadata(self) -> dict[str, str | int | bool]:
        return {
            "source": self.source,
            "document_type": self.document_type,
            "document_id": self.document_id,
            "title": self.title,
            "chunk_index": self.chunk_index,
            "last_updated": self.last_updated or "",
            "effective_date": self.effective_date or "",
            "contains_stale_reference": self.contains_stale_reference,
        }
