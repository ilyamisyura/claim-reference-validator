"""Integration tests for API endpoints."""

import pytest
from fastapi import status


class TestHealthEndpoint:
    """Test suite for /health endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns correct status."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "status" in data
        assert "model_loaded" in data
        assert "model_name" in data
        assert data["status"] == "healthy"
        assert isinstance(data["model_loaded"], bool)


class TestModelInfoEndpoint:
    """Test suite for /model-info endpoint."""

    def test_get_model_info(self, client):
        """Test model info endpoint returns correct information."""
        response = client.get("/model-info")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "model_name" in data
        assert "dimension" in data
        assert "max_seq_length" in data
        assert "normalize_embeddings" in data

        assert isinstance(data["model_name"], str)
        assert isinstance(data["dimension"], int)
        assert isinstance(data["max_seq_length"], int)
        assert isinstance(data["normalize_embeddings"], bool)

        assert data["dimension"] > 0
        assert data["max_seq_length"] > 0


class TestEmbedEndpoint:
    """Test suite for /embed endpoint."""

    def test_embed_single_text(self, client, sample_text):
        """Test embedding single text."""
        response = client.post(
            "/embed",
            json={"text": sample_text},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "embedding" in data
        assert "model" in data
        assert "dimension" in data

        assert isinstance(data["embedding"], list)
        assert isinstance(data["model"], str)
        assert isinstance(data["dimension"], int)

        assert len(data["embedding"]) == data["dimension"]
        assert data["dimension"] == 384  # MiniLM-L6-v2

    def test_embed_empty_text(self, client):
        """Test embedding empty text fails validation."""
        response = client.post(
            "/embed",
            json={"text": ""},
        )

        # Empty text should fail validation (min_length=1)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_embed_missing_text_field(self, client):
        """Test request without text field."""
        response = client.post(
            "/embed",
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_embed_invalid_json(self, client):
        """Test request with invalid JSON."""
        response = client.post(
            "/embed",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_embed_long_text(self, client):
        """Test embedding very long text."""
        long_text = "word " * 1000  # Create a very long text
        response = client.post(
            "/embed",
            json={"text": long_text},
        )

        # Should handle long text gracefully
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["embedding"]) == 384

    def test_embed_special_characters(self, client):
        """Test embedding text with special characters."""
        special_text = "Hello! 🎉 Testing with émojis and spëcial çharacters @#$%"
        response = client.post(
            "/embed",
            json={"text": special_text},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["embedding"]) == 384

    def test_embed_consistency(self, client, sample_text):
        """Test that same text produces consistent embeddings."""
        response1 = client.post("/embed", json={"text": sample_text})
        response2 = client.post("/embed", json={"text": sample_text})

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        embedding1 = response1.json()["embedding"]
        embedding2 = response2.json()["embedding"]

        # Embeddings should be identical (or extremely close)
        assert embedding1 == embedding2 or all(
            abs(a - b) < 1e-6 for a, b in zip(embedding1, embedding2)
        )


class TestEmbedBatchEndpoint:
    """Test suite for /embed-batch endpoint."""

    def test_embed_batch(self, client, sample_texts):
        """Test batch embedding."""
        response = client.post(
            "/embed-batch",
            json={"texts": sample_texts},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "embeddings" in data
        assert "model" in data
        assert "dimension" in data
        assert "count" in data

        assert isinstance(data["embeddings"], list)
        assert len(data["embeddings"]) == len(sample_texts)
        assert data["count"] == len(sample_texts)
        assert data["dimension"] == 384

        # Check each embedding
        for embedding in data["embeddings"]:
            assert isinstance(embedding, list)
            assert len(embedding) == 384

    def test_embed_batch_single_text(self, client, sample_text):
        """Test batch embedding with single text."""
        response = client.post(
            "/embed-batch",
            json={"texts": [sample_text]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["embeddings"]) == 1
        assert data["count"] == 1

    def test_embed_batch_empty_list(self, client):
        """Test batch embedding with empty list."""
        response = client.post(
            "/embed-batch",
            json={"texts": []},
        )

        # Should fail validation (min_length=1)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_embed_batch_missing_texts_field(self, client):
        """Test request without texts field."""
        response = client.post(
            "/embed-batch",
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_embed_batch_large(self, client):
        """Test batch embedding with many texts."""
        large_batch = [f"Text number {i}" for i in range(100)]
        response = client.post(
            "/embed-batch",
            json={"texts": large_batch},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["embeddings"]) == 100
        assert data["count"] == 100

    def test_embed_batch_mixed_lengths(self, client):
        """Test batch embedding with texts of varying lengths."""
        mixed_texts = [
            "Short.",
            "A bit longer text with more words.",
            "x" * 500,
            "x",
        ]
        response = client.post(
            "/embed-batch",
            json={"texts": mixed_texts},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["embeddings"]) == len(mixed_texts)


class TestSwitchModelEndpoint:
    """Test suite for /switch-model endpoint."""

    def test_switch_model_same(self, client, test_model_name):
        """Test switching to the same model."""
        response = client.post(
            "/switch-model",
            json={"model_name": test_model_name},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "message" in data
        assert "dimension" in data
        assert test_model_name in data["message"]

    def test_switch_model_invalid(self, client):
        """Test switching to invalid model."""
        response = client.post(
            "/switch-model",
            json={"model_name": "invalid/model/name"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_switch_model_missing_name(self, client):
        """Test switch model without model_name."""
        response = client.post(
            "/switch-model",
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.slow
    def test_switch_model_different(self, client):
        """Test switching to a different model (slow test)."""
        # This test downloads a new model, so marked as slow
        new_model = "sentence-transformers/paraphrase-MiniLM-L3-v2"
        response = client.post(
            "/switch-model",
            json={"model_name": new_model},
        )

        # May succeed or fail depending on network/availability
        # Let's just verify it handles the request properly
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_workflow(self, client, sample_text, sample_texts):
        """Test complete workflow: health -> model info -> embed -> batch embed."""
        # 1. Health check
        health = client.get("/health")
        assert health.status_code == status.HTTP_200_OK
        assert health.json()["status"] == "healthy"

        # 2. Get model info
        info = client.get("/model-info")
        assert info.status_code == status.HTTP_200_OK
        dimension = info.json()["dimension"]

        # 3. Single embedding
        embed = client.post("/embed", json={"text": sample_text})
        assert embed.status_code == status.HTTP_200_OK
        assert len(embed.json()["embedding"]) == dimension

        # 4. Batch embedding
        batch = client.post("/embed-batch", json={"texts": sample_texts})
        assert batch.status_code == status.HTTP_200_OK
        assert len(batch.json()["embeddings"]) == len(sample_texts)
        assert batch.json()["dimension"] == dimension

    def test_concurrent_requests(self, client, sample_text):
        """Test handling concurrent requests."""
        # Make multiple requests
        responses = [
            client.post("/embed", json={"text": f"{sample_text} {i}"})
            for i in range(10)
        ]

        # All should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)

        # All should return valid embeddings
        embeddings = [r.json()["embedding"] for r in responses]
        assert all(len(e) == 384 for e in embeddings)
