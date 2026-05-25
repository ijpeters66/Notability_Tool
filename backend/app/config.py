from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Notability-to-ServiceM8 Agent"
    database_url: str = "sqlite:///./notability_agent.db"
    jwt_secret: str = "change-me-before-deploying"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    upload_dir: Path = Path("uploads")
    max_upload_bytes: int = 30 * 1024 * 1024
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    claude_api_key: str | None = None
    claude_model: str = "claude-3-5-sonnet-latest"
    servicem8_api_key: str | None = None
    servicem8_base_url: str = "https://api.servicem8.com/api_1.0"
    external_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
