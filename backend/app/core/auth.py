import logging
from typing import Dict, Optional

import jwt
from jwt import InvalidAudienceError, PyJWTError

# from supabase import Client, create_client
from app.core.config import settings
from app.models.user import UserRole

logger = logging.getLogger(__name__)


def _client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)


def get_user(user_id: str) -> Optional[Dict]:
    """Get user with fresh role data from Supabase."""
    try:
        c = _client()
        resp = c.auth.admin.get_user_by_id(user_id)
        if resp and resp.user:
            return {
                "id": resp.user.id,
                "email": resp.user.email,
                "role": resp.user.app_metadata.get("role", "USER"),
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        return None


def verify_token(token: str) -> dict:
    """Verifies a Supabase access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=settings.JWT_AUDIENCES,
            options={"require": ["exp", "iat", "aud", "sub"]},
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
        )
        return payload
    except InvalidAudienceError as e:
        raise ValueError("Invalid token audience") from e
    except PyJWTError as e:
        raise ValueError(str(e)) from e


def set_user_role(user_id: str, role: UserRole) -> Optional[Dict]:
    """Store role in Supabase app_metadata only."""
    try:
        c = _client()
        logger.info(f"Setting role for user {user_id} to {role}")
        resp = c.auth.admin.update_user_by_id(
            user_id,
            {"app_metadata": {"role": role.value}},
        )
        if resp and resp.user:
            return {
                "id": resp.user.id,
                "email": resp.user.email,
                "role": resp.user.app_metadata.get("role", "USER"),
            }
        return None
    except Exception as e:
        raise ValueError(f"Error updating user role: {str(e)}") from e


def sign_in_with_email(user_email: str, password: str) -> Optional[Dict]:
    try:
        c = _client()
        resp = c.auth.sign_in_with_password({"email": user_email, "password": password})
        if resp.session and resp.user:
            return {
                "access_token": resp.session.access_token,
                "user": {"id": resp.user.id, "email": resp.user.email},
            }
        return None
    except Exception as e:
        raise ValueError("Login failed") from e


def sign_up_with_email(user_email: str, password: str) -> Optional[Dict]:
    try:
        c = _client()
        resp = c.auth.sign_up({"email": user_email, "password": password})
        if resp.user:
            return {"id": resp.user.id, "email": resp.user.email}
        return None
    except Exception as e:
        raise ValueError(f"Sign up failed: {str(e)}") from e
