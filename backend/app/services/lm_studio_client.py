"""HTTP client for LM Studio API (OpenAI-compatible)."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LMStudioError(Exception):
    """Exception raised when LM Studio service fails."""

    pass


class LMStudioClient:
    """Client for communicating with LM Studio (OpenAI-compatible API)."""

    def __init__(self, base_url: str, model: str = "local-model", timeout: float = 120.0):
        """
        Initialize LM Studio client.

        Args:
            base_url: Base URL of LM Studio (e.g., "http://localhost:1234/v1")
            model: Model name to use
            timeout: Request timeout in seconds (default 120s for generation)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
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

    async def health_check(self) -> bool:
        """Check if LM Studio service is healthy."""
        client = await self._get_client()
        try:
            response = await client.get(f"{self.base_url}/models")
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"LM Studio health check failed: {e}")
            return False

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate chat completion using LM Studio.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})

        Returns:
            Generated text response

        Raises:
            LMStudioError: If generation fails
        """
        client = await self._get_client()

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            if "choices" not in result or len(result["choices"]) == 0:
                raise LMStudioError("No completion returned from LM Studio")

            return result["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            logger.error(f"Failed to generate completion: {e}")
            raise LMStudioError(f"Failed to generate completion: {e}") from e
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid response format from LM Studio: {e}")
            raise LMStudioError(f"Invalid response format: {e}") from e


# Global client instance (will be initialized in main.py)
_lm_studio_client: LMStudioClient | None = None


def get_lm_studio_client() -> LMStudioClient:
    """Get the global LM Studio client instance."""
    if _lm_studio_client is None:
        raise RuntimeError(
            "LM Studio client not initialized. Call init_lm_studio_client first."
        )
    return _lm_studio_client


def init_lm_studio_client(base_url: str, model: str = "local-model", timeout: float = 120.0) -> LMStudioClient:
    """Initialize the global LM Studio client."""
    global _lm_studio_client
    _lm_studio_client = LMStudioClient(base_url, model, timeout)
    return _lm_studio_client


async def close_lm_studio_client():
    """Close the global LM Studio client."""
    global _lm_studio_client
    if _lm_studio_client is not None:
        await _lm_studio_client.close()
        _lm_studio_client = None
