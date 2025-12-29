import logging
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages embedding model loading and inference."""

    def __init__(self):
        self._model: Optional[SentenceTransformer] = None
        self._current_model_name: Optional[str] = None

    def load_model(self, model_name: str) -> None:
        """Load or reload embedding model."""
        logger.info(f"Loading embedding model: {model_name}")

        try:
            self._model = SentenceTransformer(
                model_name,
                cache_folder=settings.model_cache_dir,
            )
            self._current_model_name = model_name
            logger.info(
                f"Model loaded successfully. Dimension: {self._model.get_sentence_embedding_dimension()}"
            )
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    @property
    def model(self) -> SentenceTransformer:
        """Get current model, loading default if needed."""
        if self._model is None:
            self.load_model(settings.default_model)

        assert self._model is not None
        return self._model

    @property
    def model_name(self) -> str:
        """Get current model name."""
        if self._current_model_name is None:
            # Trigger lazy loading
            _ = self.model
        assert self._current_model_name is not None
        return self._current_model_name

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension of current model."""
        return self.model.get_sentence_embedding_dimension()

    def get_max_seq_length(self) -> int:
        """Get maximum sequence length of current model."""
        return self.model.max_seq_length

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as numpy array
        """
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=settings.normalize_embeddings,
            show_progress_bar=False,
        )
        return embedding

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed

        Returns:
            Array of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=settings.normalize_embeddings,
            batch_size=settings.batch_size,
            show_progress_bar=False,
        )
        return embeddings


# Global model manager instance
model_manager = ModelManager()
