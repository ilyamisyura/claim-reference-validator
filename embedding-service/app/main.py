import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.model_manager import model_manager
from app.models import (
    EmbedBatchRequest,
    EmbedBatchResponse,
    EmbedRequest,
    EmbedResponse,
    HealthResponse,
    ModelInfo,
    SwitchModelRequest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup: preload model
    logger.info("Starting embedding service...")
    logger.info(f"Preloading model: {settings.default_model}")
    try:
        model_manager.load_model(settings.default_model)
        logger.info("Model preloaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload model: {e}")
        # Don't fail startup - allow lazy loading
    yield
    # Shutdown
    logger.info("Shutting down embedding service...")


app = FastAPI(
    title="Embedding Service",
    description="Semantic embedding generation service for Fastapi-Nuxt Template",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model_loaded=model_manager._model is not None,
        model_name=model_manager._current_model_name,
    )


@app.get("/model-info", response_model=ModelInfo)
async def get_model_info():
    """Get information about the current embedding model."""
    try:
        return ModelInfo(
            model_name=model_manager.model_name,
            dimension=model_manager.get_embedding_dimension(),
            max_seq_length=model_manager.get_max_seq_length(),
            normalize_embeddings=settings.normalize_embeddings,
        )
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get model info: {str(e)}"
        )


@app.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """Generate embedding for a single text."""
    try:
        embedding = model_manager.embed_text(request.text)

        return EmbedResponse(
            embedding=embedding.tolist(),
            model=model_manager.model_name,
            dimension=len(embedding),
        )
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate embedding: {str(e)}"
        )


@app.post("/embed-batch", response_model=EmbedBatchResponse)
async def embed_batch(request: EmbedBatchRequest):
    """Generate embeddings for multiple texts."""
    try:
        embeddings = model_manager.embed_batch(request.texts)

        return EmbedBatchResponse(
            embeddings=[emb.tolist() for emb in embeddings],
            model=model_manager.model_name,
            dimension=embeddings.shape[1],
            count=len(embeddings),
        )
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate embeddings: {str(e)}"
        )


@app.post("/switch-model")
async def switch_model(request: SwitchModelRequest):
    """Switch to a different embedding model (for experimentation)."""
    try:
        logger.info(f"Switching model to: {request.model_name}")
        model_manager.load_model(request.model_name)

        return {
            "message": f"Successfully switched to model: {request.model_name}",
            "dimension": model_manager.get_embedding_dimension(),
        }
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
