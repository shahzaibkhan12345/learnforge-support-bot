from dataclasses import dataclass

from learnforge_support.chat import ChatService
from learnforge_support.config import Settings
from learnforge_support.models import DocumentChunk
from learnforge_support.retrieval import SearchResult


@dataclass
class FakeRetriever:
    results: list[SearchResult]
    queries: list[str] | None = None

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        if self.queries is not None:
            self.queries.append(query)
        return self.results


class FakeGenerator:
    def __init__(self) -> None:
        self.history_lengths: list[int] = []
        self.histories: list[list[dict[str, str]]] = []

    def answer(self, question: str, context: list[SearchResult], history: list[dict[str, str]]) -> str:
        self.history_lengths.append(len(history))
        self.histories.append(list(history))
        return f"Grounded answer [FAQ-01] for: {question}"


def result(score: float) -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            chunk_id="faq-01",
            text="Course access guidance.",
            source="faqs.md",
            document_type="faq",
            document_id="FAQ-01",
            title="Course access",
            chunk_index=0,
            last_updated=None,
            effective_date=None,
            contains_stale_reference=False,
        ),
        relevance_score=score,
    )


def test_low_confidence_query_escalates_without_calling_generator() -> None:
    generator = FakeGenerator()
    service = ChatService(
        FakeRetriever([result(0.12)]),
        generator,
        Settings(min_relevance_score=0.34),
    )

    response = service.respond("session-1", "Can you change my grade?")

    assert response.escalated is True
    assert response.citations == ["FAQ-01"]
    assert generator.history_lengths == []


def test_session_history_is_forwarded_on_follow_up() -> None:
    generator = FakeGenerator()
    retriever = FakeRetriever([result(0.9)], queries=[])
    service = ChatService(retriever, generator, Settings())

    first = service.respond("session-1", "How do I access my course?")
    second = service.respond("session-1", "What if it is still missing?")

    assert first.escalated is False
    assert second.escalated is False
    assert generator.history_lengths == [0, 2]
    assert generator.histories[1] == [
        {"role": "user", "content": "How do I access my course?"},
        {"role": "assistant", "content": "Grounded answer [FAQ-01] for: How do I access my course?"},
    ]
    assert retriever.queries == [
        "How do I access my course?",
        "How do I access my course? What if it is still missing?",
    ]
