from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    chroma_path: Path = Path(".chroma")
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k: int = 5
    min_relevance_score: float = 0.34
    max_history_messages: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")
