from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from .config import Settings
from .ingestion import load_corpus
from .models import DocumentChunk


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    relevance_score: float


class KnowledgeBase:
    """Persistent Chroma-backed index for the LearnForge corpus."""

    collection_name = "learnforge-knowledge"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.client = chromadb.PersistentClient(path=str(self.settings.chroma_path))
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.settings.embedding_model
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "LearnForge support knowledge base"},
        )

    def rebuild(self, data_dir: Path) -> int:
        chunks = load_corpus(data_dir)
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "LearnForge support knowledge base"},
        )
        if chunks:
            self.collection.upsert(
                ids=[chunk.chunk_id for chunk in chunks],
                documents=[chunk.text for chunk in chunks],
                metadatas=[chunk.metadata() for chunk in chunks],
            )
        return len(chunks)

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        limit = top_k or self.settings.top_k
        if self.collection.count() == 0:
            return []

        response: dict[str, Any] = self.collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )
        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]
        results: list[SearchResult] = []

        for document, metadata, distance in zip(documents, metadatas, distances):
            chunk = DocumentChunk(
                chunk_id=str(metadata.get("document_id", "unknown")).lower(),
                text=str(document),
                source=str(metadata.get("source", "unknown")),
                document_type=str(metadata.get("document_type", "unknown")),
                document_id=str(metadata.get("document_id", "unknown")),
                title=str(metadata.get("title", "Untitled")),
                chunk_index=int(metadata.get("chunk_index", 0)),
                last_updated=str(metadata.get("last_updated", "")) or None,
                effective_date=str(metadata.get("effective_date", "")) or None,
                contains_stale_reference=bool(metadata.get("contains_stale_reference", False)),
            )
            results.append(SearchResult(chunk=chunk, relevance_score=max(0.0, 1.0 - float(distance))))

        return self._prefer_current_policy(results)

    @staticmethod
    def _prefer_current_policy(results: list[SearchResult]) -> list[SearchResult]:
        """Keep evidence visible, but rank current policy records before stale references."""
        return sorted(
            results,
            key=lambda result: (
                result.chunk.document_type == "policy" and not result.chunk.contains_stale_reference,
                result.relevance_score,
            ),
            reverse=True,
        )
