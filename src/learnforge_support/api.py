from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .chat import ChatService, GroqGenerator
from .config import Settings
from .retrieval import KnowledgeBase


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)


class ChatResult(BaseModel):
    answer: str
    citations: list[str]
    confidence: float
    escalated: bool
    escalation_reason: str | None = None


def create_app(service: ChatService | None = None) -> FastAPI:
    settings = Settings()
    active_service = service
    app = FastAPI(title="LearnForge Support Assistant", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResult)
    def chat(request: ChatRequest) -> ChatResult:
        nonlocal active_service
        if active_service is None:
            knowledge_base = KnowledgeBase(settings)
            generator = GroqGenerator(settings) if settings.groq_api_key else None
            active_service = ChatService(knowledge_base, generator, settings)
        return ChatResult(**active_service.respond(request.session_id, request.message).__dict__)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("learnforge_support.api:app", host="127.0.0.1", port=8000, reload=True)
