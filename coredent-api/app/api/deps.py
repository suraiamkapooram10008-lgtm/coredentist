"""
API Dependencies
Reusable dependencies for FastAPI endpoints
"""

import logging
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, Union
from uuid import UUID

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.security import decode_token, verify_csrf_token
from app.models.user import User, UserRole

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Union[AsyncSession, Session] = Depends(get_db),
    request: Request = None,
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    try:
        try:
            uuid_obj = UUID(user_id)
            query_stmt = select(User).where(User.id == uuid_obj)
        except (ValueError, TypeError):
            from sqlalchemy import cast, String
            query_stmt = select(User).where(cast(User.id, String) == user_id)
        result = await db.execute(query_stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        if not user.practice_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not assigned to a practice.")
        from app.models.practice import Practice
        practice_stmt = select(Practice).where(Practice.id == user.practice_id)
        practice_result = await db.execute(practice_stmt)
        practice = practice_result.scalar_one_or_none()
        if not practice or not practice.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Practice account is suspended or inactive.")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_role(*allowed_roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for this action.")
        return current_user
    return role_checker


async def verify_csrf_no_auth(request: Request, x_csrf_token: Optional[str] = Header(None)) -> bool:
    """Verify CSRF token for endpoints where user may not be authenticated"""
    if not x_csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF cookie missing")
    if not verify_csrf_token(x_csrf_token, cookie_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
    return True


async def verify_csrf(request: Request, x_csrf_token: Optional[str] = Header(None), current_user: User = Depends(get_current_user)) -> bool:
    """Verify CSRF token for state-changing requests"""
    if not x_csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF cookie missing")
    if not verify_csrf_token(x_csrf_token, cookie_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
    return True


async def get_current_practice_id(current_user: User = Depends(get_current_user)) -> UUID:
    return current_user.practice_id


get_current_practice = get_current_practice_id


class Pagination:
    def __init__(self, page: int = 1, limit: int = 10):
        self.page = max(1, page)
        self.limit = min(100, max(1, limit))
        self.offset = (self.page - 1) * self.limit