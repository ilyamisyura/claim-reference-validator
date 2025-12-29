"""Pytest configuration and fixtures for backend tests."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.services.embedding_client import EmbeddingClient


# Database fixtures
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Assumes migrations have been run on postgres-test database.
    """
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:54323/postgres",
        poolclass=StaticPool,
    )

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()

    # Cleanup - truncate all tables for next test
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("TRUNCATE TABLE entities CASCADE"))
        await conn.execute(sqlalchemy.text("TRUNCATE TABLE users CASCADE"))
        await conn.execute(sqlalchemy.text("TRUNCATE TABLE edges CASCADE"))

    await engine.dispose()
