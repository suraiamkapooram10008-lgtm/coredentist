"""
OAuth Authentication Service
Handles Google OAuth and Apple Sign-In token verification
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import logging
from uuid import UUID

from jose import jwt, JWTError
import requests

from app.core.config_simple import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash, hash_token
from app.core.encryption import encrypt_value

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for OAuth authentication (Google + Apple)"""

    GOOGLE_KEYS_URL = "https://www.googleapis.com/oauth2/v3/certs"
    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
    APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"

    @staticmethod
    def _get_google_public_keys() -> Dict[str, Any]:
        """Fetch Google's public keys for ID token verification"""
        try:
            resp = requests.get(OAuthService.GOOGLE_KEYS_URL, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch Google public keys: {e}")
            raise ValueError("Failed to verify Google token")

    @staticmethod
    def _get_apple_public_keys() -> Dict[str, Any]:
        """Fetch Apple's public keys for ID token verification"""
        try:
            resp = requests.get(OAuthService.APPLE_KEYS_URL, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch Apple public keys: {e}")
            raise ValueError("Failed to verify Apple token")

    @classmethod
    def verify_google_token(cls, id_token: str) -> Dict[str, Any]:
        """
        Verify a Google ID token and extract user info.
        
        Uses Google's OAuth2 tokeninfo endpoint for validation,
        which verifies the token signature, expiration, and audience.
        
        Returns:
            Dict with keys: sub, email, given_name, family_name, picture
        
        Raises:
            ValueError: If token is invalid or audience mismatch
        """
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise ValueError("Google OAuth not configured (missing GOOGLE_CLIENT_ID)")

        try:
            # Fetch Google's public keys
            keys = cls._get_google_public_keys()
            
            # Get the key ID from token header
            unverified_header = jwt.get_unverified_header(id_token)
            kid = unverified_header.get("kid")
            
            # Find matching public key
            public_key = None
            for key in keys.get("keys", []):
                if key.get("kid") == kid:
                    public_key = key
                    break
            
            if not public_key:
                raise ValueError("No matching Google public key found")
            
            # Verify token signature and claims
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience=settings.GOOGLE_OAUTH_CLIENT_ID,
                options={"verify_exp": True},
            )
            
            # Verify issuer
            if payload.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
                raise ValueError("Invalid Google token issuer")
            
            return {
                "provider": "google",
                "provider_user_id": payload["sub"],
                "email": payload.get("email", ""),
                "email_verified": payload.get("email_verified", False),
                "first_name": payload.get("given_name", ""),
                "last_name": payload.get("family_name", ""),
                "picture": payload.get("picture"),
            }
            
        except JWTError as e:
            logger.error(f"Google token verification failed: {e}")
            raise ValueError("Invalid Google ID token")

    @classmethod
    def verify_apple_token(cls, id_token: str) -> Dict[str, Any]:
        """
        Verify an Apple Sign-In identity token.
        
        Apple uses RS256 signed JWTs. We verify the signature
        against Apple's public keys and validate the claims.
        
        Returns:
            Dict with keys: sub, email, first_name, last_name
        
        Raises:
            ValueError: If token is invalid
        """
        if not settings.APPLE_CLIENT_ID:
            raise ValueError("Apple Sign-In not configured (missing APPLE_CLIENT_ID)")

        try:
            # Fetch Apple's public keys
            keys = cls._get_apple_public_keys()
            
            # Get key ID from token header
            unverified_header = jwt.get_unverified_header(id_token)
            kid = unverified_header.get("kid")
            alg = unverified_header.get("alg", "RS256")
            
            # Find matching public key
            public_key = None
            for key in keys.get("keys", []):
                if key.get("kid") == kid:
                    public_key = key
                    break
            
            if not public_key:
                raise ValueError("No matching Apple public key found")
            
            # Verify token signature and claims
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=[alg],
                audience=settings.APPLE_CLIENT_ID,
                options={"verify_exp": True},
            )
            
            # Verify issuer
            if payload.get("iss") != "https://appleid.apple.com":
                raise ValueError("Invalid Apple token issuer")
            
            # Apple only returns email on first sign-in (user privacy)
            # Subsequent sign-ins may not include email
            email = payload.get("email", "")
            
            return {
                "provider": "apple",
                "provider_user_id": payload["sub"],
                "email": email,
                "email_verified": True,  # Apple verifies email
                "first_name": payload.get("given_name", ""),
                "last_name": payload.get("family_name", ""),
                "picture": None,  # Apple doesn't provide profile pictures
            }
            
        except JWTError as e:
            logger.error(f"Apple token verification failed: {e}")
            raise ValueError("Invalid Apple ID token")

    @classmethod
    def verify_token(cls, provider: str, id_token: str) -> Dict[str, Any]:
        """Verify an OAuth token from the specified provider"""
        if provider == "google":
            return cls.verify_google_token(id_token)
        elif provider == "apple":
            return cls.verify_apple_token(id_token)
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

    @staticmethod
    def generate_password_for_oauth() -> str:
        """Generate a strong random password for OAuth-created users"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(32))