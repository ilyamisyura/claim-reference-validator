from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    """Request for single text embedding."""

    text: str = Field(..., description="Text to embed", min_length=1)


class EmbedBatchRequest(BaseModel):
    """Request for batch text embedding."""

    texts: list[str] = Field(..., description="List of texts to embed", min_length=1)


class EmbedResponse(BaseModel):
    """Response containing embedding vector."""

    embedding: list[float] = Field(..., description="Embedding vector")
    model: str = Field(..., description="Model used for embedding")
    dimension: int = Field(..., description="Embedding dimension")


class EmbedBatchResponse(BaseModel):
    """Response containing batch embedding vectors."""

    embeddings: list[list[float]] = Field(..., description="List of embedding vectors")
    model: str = Field(..., description="Model used for embedding")
    dimension: int = Field(..., description="Embedding dimension")
    count: int = Field(..., description="Number of embeddings")


class ModelInfo(BaseModel):
    """Information about current model."""

    model_name: str = Field(..., description="Name/path of the model")
    dimension: int = Field(..., description="Embedding dimension")
    max_seq_length: int = Field(..., description="Maximum sequence length")
    normalize_embeddings: bool = Field(..., description="Whether embeddings are normalized")


class SwitchModelRequest(BaseModel):
    """Request to switch embedding model."""

    model_name: str = Field(..., description="Name/path of new model")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_name: str | None = Field(None, description="Current model name")
