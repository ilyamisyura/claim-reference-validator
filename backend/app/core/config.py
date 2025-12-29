from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fastapi-Nuxt Template"
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"
    )
    EMBEDDING_SERVICE_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"


settings = Settings()
