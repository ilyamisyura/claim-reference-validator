"""Unit tests for ModelManager."""

import pytest
import numpy as np

from app.model_manager import ModelManager
from app.config import settings


class TestModelManager:
    """Test suite for ModelManager class."""

    def test_model_lazy_loading(self):
        """Test that model is loaded lazily on first access."""
        manager = ModelManager()
        assert manager._model is None
        assert manager._current_model_name is None

        # Access model property triggers lazy loading
        _ = manager.model
        assert manager._model is not None
        assert manager._current_model_name == settings.default_model

    def test_load_model(self, test_model_name):
        """Test explicit model loading."""
        manager = ModelManager()
        manager.load_model(test_model_name)

        assert manager._model is not None
        assert manager._current_model_name == test_model_name
        assert manager.model_name == test_model_name

    def test_load_invalid_model(self):
        """Test loading an invalid model raises error."""
        manager = ModelManager()
        with pytest.raises(Exception):
            manager.load_model("invalid/model/path")

    def test_get_embedding_dimension(self, model_manager):
        """Test getting embedding dimension."""
        dimension = model_manager.get_embedding_dimension()
        assert isinstance(dimension, int)
        assert dimension == 384  # MiniLM-L6-v2 produces 384d embeddings

    def test_get_max_seq_length(self, model_manager):
        """Test getting max sequence length."""
        max_length = model_manager.get_max_seq_length()
        assert isinstance(max_length, int)
        assert max_length > 0

    def test_embed_text(self, model_manager, sample_text):
        """Test single text embedding."""
        embedding = model_manager.embed_text(sample_text)

        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == 384
        assert embedding.dtype == np.float32

        # Check if normalized (L2 norm should be ~1.0)
        if settings.normalize_embeddings:
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 0.01

    def test_embed_text_empty_string(self, model_manager):
        """Test embedding empty string."""
        embedding = model_manager.embed_text("")
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == 384

    def test_embed_batch(self, model_manager, sample_texts):
        """Test batch text embedding."""
        embeddings = model_manager.embed_batch(sample_texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (len(sample_texts), 384)
        assert embeddings.dtype == np.float32

        # Check each embedding is normalized
        if settings.normalize_embeddings:
            for embedding in embeddings:
                norm = np.linalg.norm(embedding)
                assert abs(norm - 1.0) < 0.01

    def test_embed_batch_single_text(self, model_manager, sample_text):
        """Test batch embedding with single text."""
        embeddings = model_manager.embed_batch([sample_text])

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (1, 384)

    def test_embedding_consistency(self, model_manager, sample_text):
        """Test that same text produces same embedding."""
        embedding1 = model_manager.embed_text(sample_text)
        embedding2 = model_manager.embed_text(sample_text)

        np.testing.assert_array_almost_equal(embedding1, embedding2)

    def test_different_texts_different_embeddings(self, model_manager):
        """Test that different texts produce different embeddings."""
        text1 = "Machine learning is fascinating."
        text2 = "The weather is nice today."

        embedding1 = model_manager.embed_text(text1)
        embedding2 = model_manager.embed_text(text2)

        # Embeddings should be different
        assert not np.allclose(embedding1, embedding2)

        # But similar texts should have higher cosine similarity
        text3 = "Artificial intelligence is interesting."
        embedding3 = model_manager.embed_text(text3)

        # Cosine similarity
        sim_1_3 = np.dot(embedding1, embedding3)
        sim_1_2 = np.dot(embedding1, embedding2)

        # text1 and text3 are more similar than text1 and text2
        assert sim_1_3 > sim_1_2

    def test_model_reload(self, model_manager, test_model_name):
        """Test reloading the same model."""
        original_model = model_manager._model

        # Reload same model
        model_manager.load_model(test_model_name)

        # Should create a new model instance
        assert model_manager._model is not original_model
        assert model_manager.model_name == test_model_name
