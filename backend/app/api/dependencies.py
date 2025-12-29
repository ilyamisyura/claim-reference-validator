from typing import AsyncGenerator, Optional
import json

from app.core.auth.factory import AuthFactory
from app.db.base_class import async_session
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

security = HTTPBearer(auto_error=False)


async def get_db(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Database session with automatic RLS context from JWT token.

    If a valid JWT token is present in the Authorization header:
    - Sets app.current_user_id for auth.uid()
    - Sets app.current_user_jwt for auth.jwt()

    RLS policies will automatically enforce row-level security.
    """
    async with async_session() as session:
        # Set RLS session variables if user is authenticated
        if credentials:
            try:
                auth = AuthFactory.get_provider()
                payload = await auth.verify_token(credentials.credentials)
                user_id = payload.get("sub")

                if user_id:
                    # Set session variables for RLS
                    await session.execute(
                        text("SET LOCAL app.current_user_id = :user_id"),
                        {"user_id": user_id}
                    )
                    jwt_claims = json.dumps({
                        "sub": user_id,
                        "role": payload.get("role", "student"),
                        "email": payload.get("email", "")
                    })
                    await session.execute(
                        text("SET LOCAL app.current_user_jwt = :jwt"),
                        {"jwt": jwt_claims}
                    )
            except Exception:
                # Invalid token - continue without RLS context
                pass

        yield session
