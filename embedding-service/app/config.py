from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Embedding service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EMBEDDING_",
        case_sensitive=False,
    )

    # Model settings
    default_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    model_cache_dir: str = "./models"

    # API settings
    host: str = "0.0.0.0"
    port: int = 8001

    # Performance
    batch_size: int = 32
    normalize_embeddings: bool = True

    # CORS
    cors_origins: list[str] = ["*"]


settings = Settings()
