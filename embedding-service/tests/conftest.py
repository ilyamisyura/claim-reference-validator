"""Pytest configuration and fixtures for embedding service tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.model_manager import ModelManager


@pytest.fixture(scope="session")
def test_model_name():
    """Use the default small model for tests."""
    return "sentence-transformers/all-MiniLM-L6-v2"


@pytest.fixture(scope="session")
def model_manager(test_model_name):
    """Create a model manager instance for testing."""
    manager = ModelManager()
    manager.load_model(test_model_name)
    return manager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_text():
    """Sample text for embedding tests."""
    return "This is a test sentence for embedding generation."


@pytest.fixture
def sample_texts():
    """Multiple sample texts for batch embedding tests."""
    return [
        "First test sentence.",
        "Second test sentence with more words.",
        "Third sentence for testing batch embeddings.",
    ]
