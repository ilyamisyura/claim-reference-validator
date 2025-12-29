import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.base_class import engine
from app.services.embedding_client import init_embedding_client, close_embedding_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    retries = 5
    retry_delay = 5

    # Connect to database
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                print(f"Database connection established on attempt {attempt + 1}")
                break
        except Exception as e:
            if attempt == retries - 1:
                print(f"Failed to connect after {retries} attempts: {e}")
                raise
            print(f"Failed to connect, retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)

    print(f"Initializing embedding service client: {settings.EMBEDDING_SERVICE_URL}")
    init_embedding_client(settings.EMBEDDING_SERVICE_URL)
    print("Embedding service client initialized")

    yield

    await close_embedding_client()
    await engine.dispose()


logger = logging.getLogger(__name__)
logger.info("=== Application starting ===")

app = FastAPI(lifespan=lifespan, title="Fastapi-Nuxt Template")
bearer_scheme = HTTPBearer()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["internal"], operation_id="health_check")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
