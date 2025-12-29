# Embedding Service

Standalone FastAPI service for generating text embeddings for semantic search.

## Features

- 🚀 Fast embedding generation using sentence-transformers
- 📦 Single and batch embedding endpoints
- 🔄 Dynamic model switching for experimentation
- 🐳 Docker support
- ⚙️ Configurable via environment variables

## Quick Start

### Local Development

```bash
# Install dependencies
cd embedding-service
uv sync

# Run the service
uv run fastapi dev --port=8001
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

**Test Coverage: 90%** (33 tests, all passing)

### Docker

```bash
docker compose up embedding-service
```

## API Endpoints

### Health Check

```http
GET /health
```

### Get Model Information

```http
GET /model-info
```

### Embed Single Text

```http
POST /embed
Content-Type: application/json

{
  "text": "Your text here"
}
```

### Embed Multiple Texts (Batch)

```http
POST /embed-batch
Content-Type: application/json

{
  "texts": ["text 1", "text 2", "text 3"]
}
```

### Switch Model (Experimental)

```http
POST /switch-model
Content-Type: application/json

{
  "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
}
```

## Configuration

See `.env.example` for available configuration options.

## Models

This service can use **any** sentence-transformer model from [Hugging Face](https://huggingface.co/models?library=sentence-transformers).

### Where to Find Models

- **Sentence Transformers**: https://huggingface.co/sentence-transformers
- **BGE Models**: https://huggingface.co/BAAI
- **All compatible models**: https://huggingface.co/models?library=sentence-transformers

### Example Models

Default model:

- `sentence-transformers/all-MiniLM-L6-v2` - 384 dimensions, fast, English

Other popular models:

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` - Multilingual support
- `BAAI/bge-small-en-v1.5` - BGE model, good quality
- `BAAI/bge-m3` - Multilingual BGE model
- `sentence-transformers/all-mpnet-base-v2` - Higher quality, 768 dimensions

Switch models dynamically using the `/switch-model` endpoint.

## Architecture

```
embedding-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── model_manager.py     # Model loading and inference
│   └── models.py            # Pydantic models (request/response)
├── pyproject.toml           # Dependencies
├── Dockerfile
└── README.md
```
