"""HTTP client for embedding service."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Exception raised when embedding service fails."""

    pass


class EmbeddingClient:
    """Client for communicating with the embedding service."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize embedding client.

        Args:
            base_url: Base URL of the embedding service (e.g., "http://embedding-service:8001")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> dict[str, Any]:
        """Check if embedding service is healthy."""
        client = await self._get_client()
        try:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Embedding service health check failed: {e}")
            raise EmbeddingServiceError(f"Health check failed: {e}") from e

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about current embedding model."""
        client = await self._get_client()
        try:
            response = await client.get(f"{self.base_url}/model-info")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get model info: {e}")
            raise EmbeddingServiceError(f"Failed to get model info: {e}") from e

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/embed",
                json={"text": text},
            )
            response.raise_for_status()
            result = response.json()
            return result["embedding"]
        except httpx.HTTPError as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingServiceError(f"Failed to generate embedding: {e}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/embed-batch",
                json={"texts": texts},
            )
            response.raise_for_status()
            result = response.json()
            return result["embeddings"]
        except httpx.HTTPError as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingServiceError(
                f"Failed to generate batch embeddings: {e}"
            ) from e


# Global client instance (will be initialized in main.py)
_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    """Get the global embedding client instance."""
    if _embedding_client is None:
        raise RuntimeError(
            "Embedding client not initialized. Call init_embedding_client first."
        )
    return _embedding_client


def init_embedding_client(base_url: str, timeout: float = 30.0) -> EmbeddingClient:
    """Initialize the global embedding client."""
    global _embedding_client
    _embedding_client = EmbeddingClient(base_url, timeout)
    return _embedding_client


async def close_embedding_client():
    """Close the global embedding client."""
    global _embedding_client
    if _embedding_client is not None:
        await _embedding_client.close()
        _embedding_client = None
