from fastapi.testclient import TestClient

from learnforge_support.api import create_app
from learnforge_support.chat import ChatService
from learnforge_support.config import Settings
from learnforge_support.models import DocumentChunk
from learnforge_support.retrieval import SearchResult


class FakeRetriever:
    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        return [
            SearchResult(
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
                relevance_score=0.9,
            )
        ]


class FakeGenerator:
    def answer(self, question: str, context: list[SearchResult], history: list[dict[str, str]]) -> str:
        return "Use My Learning to access the course [FAQ-01]."


def test_chat_endpoint_returns_citations_and_health() -> None:
    service = ChatService(FakeRetriever(), FakeGenerator(), Settings())
    client = TestClient(create_app(service))

    assert client.get("/health").json() == {"status": "ok"}
    response = client.post("/chat", json={"session_id": "demo", "message": "Where is my course?"})

    assert response.status_code == 200
    assert response.json()["citations"] == ["FAQ-01"]
    assert response.json()["escalated"] is False
