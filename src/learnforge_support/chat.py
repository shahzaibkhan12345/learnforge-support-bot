from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .config import Settings
from .retrieval import SearchResult


class Retriever(Protocol):
    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]: ...


class Generator(Protocol):
    def answer(self, question: str, context: list[SearchResult], history: list[dict[str, str]]) -> str: ...


class GroqGenerator:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured")
        from groq import Groq

        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    def answer(self, question: str, context: list[SearchResult], history: list[dict[str, str]]) -> str:
        context_text = "\n\n".join(
            f"[{result.chunk.document_id}] {result.chunk.text}" for result in context
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the LearnForge customer support assistant. Answer only from the supplied "
                    "knowledge-base context. Do not invent policy, dates, refunds, or account actions. "
                    "Do not infer thresholds, exceptions, or illustrative examples that are not stated "
                    "in the context. If the policy does not specify a detail, say that it requires Support "
                    "review instead of guessing. "
                    "If the context is insufficient, say so and recommend human support. Cite every factual "
                    "claim with the source ID in ASCII square brackets, for example [POLICY-02]. Never use "
                    "Unicode citation brackets. Keep the answer concise and actionable."
                ),
            },
            *history,
            {"role": "user", "content": f"Knowledge-base context:\n{context_text}\n\nQuestion: {question}"},
        ]
        response = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.0)
        return response.choices[0].message.content or "I could not produce a grounded answer."


@dataclass(frozen=True)
class ChatResponse:
    answer: str
    citations: list[str]
    confidence: float
    escalated: bool
    escalation_reason: str | None


class ChatService:
    def __init__(
        self,
        retriever: Retriever,
        generator: Generator | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.retriever = retriever
        self.generator = generator
        self.sessions: dict[str, list[dict[str, str]]] = {}

    def respond(self, session_id: str, message: str) -> ChatResponse:
        history = self.sessions.setdefault(session_id, [])
        results = self.retriever.search(message, top_k=self.settings.top_k)
        top_score = results[0].relevance_score if results else 0.0
        citations = [result.chunk.document_id for result in results[:3]]

        if not results:
            response = self._escalation("No relevant knowledge-base evidence was retrieved.", top_score, citations)
        elif top_score < self.settings.min_relevance_score:
            response = self._escalation("Retrieved evidence is below the confidence threshold.", top_score, citations)
        elif self.generator is None:
            response = self._escalation("LLM generation is not configured; a support agent should review this request.", top_score, citations)
        else:
            try:
                answer = self.generator.answer(message, results, history)
                response = ChatResponse(
                    answer=answer,
                    citations=citations,
                    confidence=round(top_score, 3),
                    escalated=False,
                    escalation_reason=None,
                )
            except Exception:
                response = self._escalation("The answer provider failed; a support agent should review this request.", top_score, citations)

        history.extend(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response.answer},
            ]
        )
        del history[:-self.settings.max_history_messages]
        return response

    @staticmethod
    def _escalation(reason: str, confidence: float, citations: list[str]) -> ChatResponse:
        return ChatResponse(
            answer="I'm not confident enough to answer this safely. I'm escalating it to LearnForge Support for review.",
            citations=citations,
            confidence=round(confidence, 3),
            escalated=True,
            escalation_reason=reason,
        )
