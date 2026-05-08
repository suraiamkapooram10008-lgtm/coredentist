"""
Security Utilities
JWT tokens, password hashing, CSRF protection
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
# L-1 FIX: Migrated from unmaintained python-jose to PyJWT
import jwt
from jwt.exceptions import PyJWTError as JWTError
from passlib.context import CryptContext
import secrets
import re

from app.core.config_simple import settings

# Password hashing context - HIPAA compliant with 14 rounds (minimum recommended for healthcare)
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=14, deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets HIPAA-compliant requirements
    Returns: (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, ""


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token (Explicit Algorithm Check)"""
    try:
        # Expert Hardening: Enforce explicit algorithm to prevent 'none' or 'RS256'/Switching attacks
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_csrf_token() -> str:
    """Generate a secure CSRF token"""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """Verify CSRF token"""
    return secrets.compare_digest(token, expected_token)


def generate_password_reset_token() -> str:
    """Generate a secure password reset token"""
    return secrets.token_urlsafe(32)


# Token hashing context - 8 rounds (faster than passwords but still secure)
# Using bcrypt instead of SHA-256 for defense-in-depth against rainbow table attacks
token_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=8, deprecated="auto")


def hash_token(token: str) -> str:
    """
    Hash a token for secure storage (SECURITY FIX - CRIT-03)
    
    Changed from SHA-256 to bcrypt (8 rounds) for better security:
    - bcrypt is intentionally slow, making brute-force attacks impractical
    - Even if tokens are cryptographically random, bcrypt protects against:
      * Rainbow table attacks
      * Future quantum computing attacks on fast hashes
    - 8 rounds chosen as balance: ~25ms per hash (acceptable) vs security
    
    Args:
        token: The token to hash
        
    Returns:
        bcrypt hash of the token
    """
    return token_context.hash(token)


def verify_token_hash(token: str, hashed_token: str) -> bool:
    """
    Verify a token against its bcrypt hash
    
    Args:
        token: The token to verify
        hashed_token: The bcrypt hash to verify against
        
    Returns:
        True if token matches hash, False otherwise
    """
    try:
        return token_context.verify(token, hashed_token)
    except Exception:
        return False


def generate_invitation_token() -> str:
    """Generate a secure staff invitation token"""
    return secrets.token_urlsafe(32)
