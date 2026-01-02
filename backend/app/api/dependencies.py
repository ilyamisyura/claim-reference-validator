from typing import AsyncGenerator, Optional

from app.db.base_class import async_session
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer(auto_error=False)


async def get_db(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async DB session. Authentication is optional and not used
    for RLS in this simplified setup.
    """
    async with async_session() as session:
        yield session
