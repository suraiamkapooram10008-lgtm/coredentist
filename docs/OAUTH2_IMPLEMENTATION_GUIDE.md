# OAuth2 Implementation Guide - CoreDent SaaS

**Status**: 🔴 NOT STARTED  
**Priority**: HIGH (Required for mobile app)  
**Effort**: 80-120 hours (3-4 weeks)  
**Target Completion**: June 15, 2026

---

## 📋 OVERVIEW

This guide outlines the implementation of OAuth2 authentication for CoreDent, supporting:
- **Google Sign-In** (OAuth 2.0)
- **Apple Sign-In** (OAuth 2.0 with OIDC)

### Why OAuth2?
- **Better UX**: One-click sign-in, no password to remember
- **Mobile App Requirement**: Apple requires "Sign in with Apple" for iOS apps
- **Security**: Reduces password-related security risks
- **Trust**: Users trust Google/Apple authentication

---

## 🎯 REQUIREMENTS

### Functional Requirements
- [ ] Users can sign in with Google
- [ ] Users can sign in with Apple
- [ ] Users can link OAuth accounts to existing email/password accounts
- [ ] Users can unlink OAuth accounts
- [ ] First-time OAuth users create a new account automatically
- [ ] OAuth tokens are securely stored and refreshed
- [ ] Users can have multiple OAuth providers linked

### Non-Functional Requirements
- [ ] OAuth flow completes in <3 seconds
- [ ] Secure token storage (encrypted)
- [ ] PKCE (Proof Key for Code Exchange) for mobile apps
- [ ] Proper error handling and user feedback
- [ ] Audit logging for OAuth events

---

## 🏗️ ARCHITECTURE

### OAuth 2.0 Flow (Authorization Code Flow with PKCE)

```
┌─────────┐                                  ┌──────────────┐
│         │                                  │              │
│  User   │                                  │   CoreDent   │
│         │                                  │   Frontend   │
└────┬────┘                                  └──────┬───────┘
     │                                              │
     │  1. Click "Sign in with Google/Apple"       │
     │◄────────────────────────────────────────────┤
     │                                              │
     │  2. Redirect to OAuth Provider               │
     ├─────────────────────────────────────────────►
     │                                              │
     │  3. User authenticates with provider         │
     │                                              │
     │  4. Provider redirects back with auth code   │
     │◄─────────────────────────────────────────────┤
     │                                              │
     │  5. Frontend sends code to backend           │
     │                                              │
     │                                              ▼
     │                                  ┌──────────────────┐
     │                                  │                  │
     │                                  │   CoreDent API   │
     │                                  │                  │
     │                                  └────────┬─────────┘
     │                                           │
     │  6. Backend exchanges code for tokens     │
     │                                           │
     │                                           ▼
     │                              ┌────────────────────────┐
     │                              │                        │
     │                              │  Google/Apple OAuth    │
     │                              │                        │
     │                              └────────────┬───────────┘
     │                                           │
     │  7. Provider returns access token         │
     │                                           │
     │                                           ▼
     │                              ┌────────────────────────┐
     │                              │                        │
     │  8. Backend fetches user info│   CoreDent Database    │
     │                              │                        │
     │                              └────────────────────────┘
     │                                           │
     │  9. Backend creates/links account         │
     │                                           │
     │  10. Backend returns JWT tokens           │
     │◄──────────────────────────────────────────┤
     │                                           │
     │  11. User is authenticated                │
     │                                           │
```

---

## 📦 BACKEND IMPLEMENTATION

### Step 1: Install Dependencies

```bash
pip install authlib httpx
```

Add to `requirements.txt`:
```
authlib==1.3.0
httpx==0.26.0
```

### Step 2: Database Schema

Create migration: `alembic/versions/20260506_oauth_providers.py`

```python
"""Add OAuth provider tables

Revision ID: oauth_providers
Revises: previous_migration
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # OAuth Provider table
    op.create_table(
        'oauth_providers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),  # 'google', 'apple'
        sa.Column('provider_user_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user')
    )
    
    op.create_index('idx_oauth_user_id', 'oauth_providers', ['user_id'])
    op.create_index('idx_oauth_provider', 'oauth_providers', ['provider'])

def downgrade():
    op.drop_table('oauth_providers')
```

### Step 3: Models

Create `app/models/oauth_provider.py`:

```python
"""OAuth Provider Model"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.base import Base


class OAuthProvider(Base):
    """OAuth provider link for users"""
    
    __tablename__ = "oauth_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'google', 'apple'
    provider_user_id = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="oauth_providers")
    
    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user'),
    )
```

Update `app/models/user.py`:

```python
# Add to User model
oauth_providers = relationship("OAuthProvider", back_populates="user", cascade="all, delete-orphan")
```

### Step 4: Configuration

Add to `app/core/config_simple.py`:

```python
# OAuth Configuration
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")

APPLE_CLIENT_ID: str = os.getenv("APPLE_CLIENT_ID", "")
APPLE_TEAM_ID: str = os.getenv("APPLE_TEAM_ID", "")
APPLE_KEY_ID: str = os.getenv("APPLE_KEY_ID", "")
APPLE_PRIVATE_KEY: str = os.getenv("APPLE_PRIVATE_KEY", "")
APPLE_REDIRECT_URI: str = os.getenv("APPLE_REDIRECT_URI", "http://localhost:3000/auth/apple/callback")
```

### Step 5: OAuth Service

Create `app/services/oauth_service.py`:

```python
"""OAuth Service - Handle OAuth authentication"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from authlib.integrations.httpx_client import OAuth2Client
import httpx

from app.core.config_simple import settings
from app.core.encryption import encrypt_data, decrypt_data
from app.models.user import User
from app.models.oauth_provider import OAuthProvider
from app.core.security import create_access_token, create_refresh_token


class OAuthService:
    """Service for OAuth authentication"""
    
    @staticmethod
    async def google_auth_url(state: str) -> str:
        """Generate Google OAuth authorization URL"""
        
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    @staticmethod
    async def google_exchange_code(code: str) -> Dict[str, Any]:
        """Exchange Google authorization code for tokens"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to exchange code: {response.text}")
            
            return response.json()
    
    @staticmethod
    async def google_get_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from Google"""
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.text}")
            
            return response.json()
    
    @staticmethod
    def create_or_link_oauth_user(
        db: Session,
        provider: str,
        provider_user_id: str,
        email: str,
        name: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: int,
        practice_id: Optional[int] = None
    ) -> tuple[User, bool]:
        """
        Create new user or link OAuth provider to existing user
        Returns: (user, is_new_user)
        """
        
        # Check if OAuth provider already linked
        oauth_provider = db.query(OAuthProvider).filter(
            OAuthProvider.provider == provider,
            OAuthProvider.provider_user_id == provider_user_id
        ).first()
        
        if oauth_provider:
            # Update tokens
            oauth_provider.access_token_encrypted = encrypt_data(access_token)
            if refresh_token:
                oauth_provider.refresh_token_encrypted = encrypt_data(refresh_token)
            oauth_provider.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            oauth_provider.updated_at = datetime.utcnow()
            db.commit()
            
            return oauth_provider.user, False
        
        # Check if user exists with this email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                full_name=name,
                is_active=True,
                email_verified=True,  # OAuth emails are pre-verified
                practice_id=practice_id
            )
            db.add(user)
            db.flush()
            is_new_user = True
        else:
            is_new_user = False
        
        # Link OAuth provider
        oauth_provider = OAuthProvider(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            access_token_encrypted=encrypt_data(access_token),
            refresh_token_encrypted=encrypt_data(refresh_token) if refresh_token else None,
            token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in)
        )
        db.add(oauth_provider)
        db.commit()
        db.refresh(user)
        
        return user, is_new_user
```

### Step 6: API Endpoints

Create `app/api/v1/endpoints/oauth.py`:

```python
"""OAuth Authentication Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.services.oauth_service import OAuthService
from app.core.security import create_access_token, create_refresh_token
from app.core.audit import log_audit_event
from app.models.user import User


router = APIRouter()


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str


class OAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool


@router.get("/google/authorize")
async def google_authorize():
    """Get Google OAuth authorization URL"""
    
    import secrets
    state = secrets.token_urlsafe(32)
    
    auth_url = await OAuthService.google_auth_url(state)
    
    return {
        "auth_url": auth_url,
        "state": state
    }


@router.post("/google/callback", response_model=OAuthResponse)
async def google_callback(
    request: OAuthCallbackRequest,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    
    try:
        # Exchange code for tokens
        tokens = await OAuthService.google_exchange_code(request.code)
        
        # Get user info
        user_info = await OAuthService.google_get_user_info(tokens["access_token"])
        
        # Create or link user
        user, is_new_user = OAuthService.create_or_link_oauth_user(
            db=db,
            provider="google",
            provider_user_id=user_info["id"],
            email=user_info["email"],
            name=user_info.get("name", user_info["email"]),
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_in=tokens["expires_in"]
        )
        
        # Create JWT tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Audit log
        log_audit_event(
            db=db,
            user_id=user.id,
            action="oauth_login",
            entity_type="user",
            entity_id=user.id,
            details={"provider": "google", "is_new_user": is_new_user}
        )
        
        return OAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            is_new_user=is_new_user
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.delete("/unlink/{provider}")
async def unlink_oauth_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlink OAuth provider from user account"""
    
    from app.models.oauth_provider import OAuthProvider
    
    oauth_provider = db.query(OAuthProvider).filter(
        OAuthProvider.user_id == current_user.id,
        OAuthProvider.provider == provider
    ).first()
    
    if not oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth provider not linked"
        )
    
    # Check if user has password (can't unlink if no other auth method)
    if not current_user.hashed_password:
        other_providers = db.query(OAuthProvider).filter(
            OAuthProvider.user_id == current_user.id,
            OAuthProvider.id != oauth_provider.id
        ).count()
        
        if other_providers == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unlink last authentication method. Set a password first."
            )
    
    db.delete(oauth_provider)
    db.commit()
    
    # Audit log
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="oauth_unlink",
        entity_type="user",
        entity_id=current_user.id,
        details={"provider": provider}
    )
    
    return {"message": f"{provider.capitalize()} account unlinked successfully"}
```

---

## 🎨 FRONTEND IMPLEMENTATION

### Step 1: Install Dependencies

```bash
cd coredent-style-main
npm install @react-oauth/google
```

### Step 2: Google Sign-In Button

Create `src/components/auth/GoogleSignInButton.tsx`:

```typescript
import { useGoogleLogin } from '@react-oauth/google';
import { Button } from '@/components/ui/button';
import { FcGoogle } from 'react-icons/fc';

interface GoogleSignInButtonProps {
  onSuccess: (code: string) => void;
  onError: (error: any) => void;
}

export function GoogleSignInButton({ onSuccess, onError }: GoogleSignInButtonProps) {
  const login = useGoogleLogin({
    onSuccess: (codeResponse) => onSuccess(codeResponse.code),
    onError: (error) => onError(error),
    flow: 'auth-code',
  });

  return (
    <Button
      type="button"
      variant="outline"
      className="w-full"
      onClick={() => login()}
    >
      <FcGoogle className="mr-2 h-5 w-5" />
      Continue with Google
    </Button>
  );
}
```

### Step 3: Update Login Page

Update `src/pages/Login.tsx`:

```typescript
import { GoogleSignInButton } from '@/components/auth/GoogleSignInButton';
import { useAuth } from '@/hooks/useAuth';

export function Login() {
  const { loginWithGoogle } = useAuth();

  const handleGoogleSuccess = async (code: string) => {
    try {
      await loginWithGoogle(code);
      // Redirect to dashboard
    } catch (error) {
      console.error('Google sign-in failed:', error);
    }
  };

  return (
    <div>
      {/* Existing email/password form */}
      
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>

      <GoogleSignInButton
        onSuccess={handleGoogleSuccess}
        onError={(error) => console.error(error)}
      />
    </div>
  );
}
```

---

## 🍎 APPLE SIGN-IN IMPLEMENTATION

### Backend

Add to `app/services/oauth_service.py`:

```python
@staticmethod
async def apple_auth_url(state: str) -> str:
    """Generate Apple OAuth authorization URL"""
    
    params = {
        "client_id": settings.APPLE_CLIENT_ID,
        "redirect_uri": settings.APPLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "name email",
        "response_mode": "form_post",
        "state": state
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"https://appleid.apple.com/auth/authorize?{query_string}"
```

### Frontend

```bash
npm install react-apple-signin-auth
```

---

## 🧪 TESTING

### Unit Tests

Create `tests/test_oauth_service.py`:

```python
import pytest
from app.services.oauth_service import OAuthService

@pytest.mark.asyncio
async def test_google_auth_url():
    url = await OAuthService.google_auth_url("test_state")
    assert "accounts.google.com" in url
    assert "test_state" in url

# Add more tests...
```

---

## 📋 CHECKLIST

### Backend
- [ ] Install dependencies (authlib, httpx)
- [ ] Create database migration
- [ ] Create OAuthProvider model
- [ ] Update User model
- [ ] Add OAuth configuration
- [ ] Implement OAuthService
- [ ] Create OAuth endpoints
- [ ] Add tests
- [ ] Update API documentation

### Frontend
- [ ] Install dependencies (@react-oauth/google)
- [ ] Create GoogleSignInButton component
- [ ] Create AppleSignInButton component
- [ ] Update Login page
- [ ] Update AuthContext
- [ ] Add OAuth API calls
- [ ] Add tests
- [ ] Update documentation

### Configuration
- [ ] Set up Google OAuth credentials
- [ ] Set up Apple Sign-In credentials
- [ ] Configure redirect URIs
- [ ] Update environment variables
- [ ] Test in development
- [ ] Test in staging
- [ ] Deploy to production

---

## 🚀 DEPLOYMENT

### Environment Variables

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback

# Apple Sign-In
APPLE_CLIENT_ID=com.yourdomain.coredent
APPLE_TEAM_ID=YOUR_TEAM_ID
APPLE_KEY_ID=YOUR_KEY_ID
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
APPLE_REDIRECT_URI=https://yourdomain.com/auth/apple/callback
```

---

## 📚 RESOURCES

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Apple Sign-In Documentation](https://developer.apple.com/sign-in-with-apple/)
- [Authlib Documentation](https://docs.authlib.org/)
- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749)

---

**Status**: 🔴 READY TO IMPLEMENT  
**Next Steps**: Start with Google OAuth, then Apple Sign-In  
**Timeline**: 3-4 weeks for complete implementation

