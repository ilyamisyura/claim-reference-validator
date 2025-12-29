import logging

from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Initialize engine kwargs
engine_kwargs = {
    "echo": True,
}

# Create engine with appropriate arguments
engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
