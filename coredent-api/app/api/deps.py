"""
API Dependencies
Reusable dependencies for FastAPI endpoints
"""

from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from typing import Optional, Union
import asyncio
from uuid import UUID

from app.core.database import get_db
from app.core.security import decode_token, verify_csrf_token
from app.models.user import User, UserRole
from app.schemas.auth import TokenData

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Union[AsyncSession, Session] = Depends(get_db),
    request: Request = None,
) -> User:
    """
    Get current authenticated user from JWT token
    Supports both Authorization header and httpOnly cookies
    """
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    # Fallback to httpOnly cookie
    elif request:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Debug logging
    print(f"[DEBUG] Looking up user with ID: {user_id}")
    print(f"[DEBUG] User ID type: {type(user_id)}")
    
    try:
        # For SQLite: UUIDs are stored as TEXT with dashes
        # We need to cast the column to string for comparison
        from sqlalchemy import cast, String
        query_stmt = select(User).where(cast(User.id, String) == user_id)
        
        # Debug: print the query
        print(f"[DEBUG] Query: {query_stmt}")
        
        # Always await the execute call for async sessions
        result = await db.execute(query_stmt)
        user = result.scalar_one_or_none()
        
        print(f"[DEBUG] Query result: {user}")
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        # Check User Status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        
        # CRIT-05 FIX: Verify Practice Status (Tenant Leash)
        # Check if user has a practice and if it's active
        if not user.practice_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not assigned to a practice.",
            )
        
        # Query practice separately to verify it's active
        from app.models.practice import Practice
        from sqlalchemy import cast, String
        # Cast UUID column to string for SQLite comparison
        practice_stmt = select(Practice).where(cast(Practice.id, String) == str(user.practice_id))
        practice_result = await db.execute(practice_stmt)
        practice = practice_result.scalar_one_or_none()
        
        if not practice or not practice.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Practice account is suspended or inactive. Please contact support.",
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control
    Usage: Depends(require_role(UserRole.OWNER, UserRole.ADMIN))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user
    
    return role_checker


async def verify_csrf(
    request: Request,
    x_csrf_token: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
) -> bool:
    """
    Verify CSRF token for state-changing requests
    """
    if not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing",
        )
    # Retrieve CSRF token from cookie (set by the client on login)
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF cookie missing",
        )
    # Verify that header token matches cookie token
    if x_csrf_token != cookie_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
    return True


async def get_current_practice_id(
    current_user: User = Depends(get_current_user),
) -> UUID:
    """Get current user's practice ID"""
    return current_user.practice_id


class Pagination:
    """Pagination parameters"""
    def __init__(
        self,
        page: int = 1,
        limit: int = 10,
    ):
        self.page = max(1, page)
        self.limit = min(100, max(1, limit))
        self.offset = (self.page - 1) * self.limit
