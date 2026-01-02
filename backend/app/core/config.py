from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fastapi-Nuxt Template"
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"
    )
    EMBEDDING_SERVICE_URL: str = "http://localhost:8001"
    LM_STUDIO_URL: str = "http://localhost:1234/v1"  # OpenAI-compatible endpoint
    LM_STUDIO_MODEL: str = "local-model"  # Default model name

    class Config:
        env_file = ".env"


settings = Settings()
