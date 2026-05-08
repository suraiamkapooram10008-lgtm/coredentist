# OAuth2 Implementation Plan

**Priority**: HIGH  
**Estimated Effort**: 2-3 weeks  
**Status**: ⏳ **PENDING**

---

## 🎯 Why OAuth2?

### Business Requirements
1. **iOS App Store Requirement**: Apple requires "Sign in with Apple" for apps with authentication
2. **User Experience**: One-click sign-in is faster and more convenient
3. **Security**: Reduces password fatigue and reuse
4. **Industry Standard**: Expected by modern users

### Technical Benefits
1. **Reduced Support**: Fewer password reset requests
2. **Better Security**: No password storage for OAuth users
3. **Faster Onboarding**: Streamlined registration process
4. **Mobile-Ready**: Essential for mobile app launch

---

## 📋 OAuth2 Providers to Implement

### Phase 1: Essential (Week 1-2)
1. ✅ **Google Sign-In** - Most popular, widely used
2. ✅ **Apple Sign-In** - Required for iOS App Store

### Phase 2: Optional (Week 3)
3. ⏳ **Microsoft/Azure AD** - For enterprise practices
4. ⏳ **Facebook** - Additional option

---

## 🏗️ Architecture Design

### Database Schema Changes

**New Table: `oauth_accounts`**
```sql
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'google', 'apple', 'microsoft'
    provider_user_id VARCHAR(255) NOT NULL,  -- OAuth provider's user ID
    provider_email VARCHAR(255),
    access_token TEXT,  -- Encrypted
    refresh_token TEXT,  -- Encrypted
    token_expires_at TIMESTAMP,
    profile_data JSONB,  -- Store name, picture, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_user_id),
    INDEX idx_oauth_user_id (user_id),
    INDEX idx_oauth_provider (provider, provider_user_id)
);
```

**Update `users` Table**:
```sql
ALTER TABLE users 
ADD COLUMN oauth_only BOOLEAN DEFAULT FALSE,
ADD COLUMN password_hash_nullable VARCHAR(255);  -- Make password optional for OAuth users
```

### API Endpoints

**New OAuth Endpoints**:
```
POST   /api/v1/auth/oauth/google/authorize      # Initiate Google OAuth flow
GET    /api/v1/auth/oauth/google/callback       # Handle Google callback
POST   /api/v1/auth/oauth/apple/authorize       # Initiate Apple OAuth flow
POST   /api/v1/auth/oauth/apple/callback        # Handle Apple callback (POST for Apple)
GET    /api/v1/auth/oauth/accounts              # List user's connected OAuth accounts
DELETE /api/v1/auth/oauth/accounts/{provider}   # Disconnect OAuth account
POST   /api/v1/auth/oauth/link                  # Link OAuth to existing account
```

---

## 🔧 Implementation Steps

### Step 1: Install Dependencies (Day 1)

```bash
cd coredent-api
pip install authlib httpx
```

**Add to `requirements.txt`**:
```
authlib==1.3.0
httpx==0.27.0
```

### Step 2: Create OAuth Models (Day 1)

**File: `app/models/oauth_account.py`**
```python
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.base import Base

class OAuthAccount(Base):
    """OAuth account linking"""
    __tablename__ = "oauth_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'google', 'apple', 'microsoft'
    provider_user_id = Column(String(255), nullable=False)
    provider_email = Column(String(255))
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    token_expires_at = Column(DateTime)
    profile_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")
    
    # Indexes
    __table_args__ = (
        Index('idx_oauth_user_id', 'user_id'),
        Index('idx_oauth_provider', 'provider', 'provider_user_id'),
        {'extend_existing': True}
    )
```

### Step 3: Create OAuth Service (Day 2-3)

**File: `app/services/oauth_service.py`**
```python
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.httpx_client import AsyncOAuth2Client
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings
from app.core.encryption import encrypt_data, decrypt_data
from app.models.oauth_account import OAuthAccount
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

class OAuthService:
    """OAuth authentication service"""
    
    def __init__(self):
        self.oauth = OAuth()
        self._configure_providers()
    
    def _configure_providers(self):
        """Configure OAuth providers"""
        # Google OAuth
        self.oauth.register(
            name='google',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
        
        # Apple OAuth
        self.oauth.register(
            name='apple',
            client_id=settings.APPLE_CLIENT_ID,
            client_secret=settings.APPLE_CLIENT_SECRET,
            authorize_url='https://appleid.apple.com/auth/authorize',
            authorize_params={'response_mode': 'form_post'},
            access_token_url='https://appleid.apple.com/auth/token',
            client_kwargs={'scope': 'name email'}
        )
    
    async def get_authorization_url(self, provider: str, redirect_uri: str) -> Dict[str, str]:
        """Get OAuth authorization URL"""
        client = self.oauth.create_client(provider)
        authorization_url, state = await client.create_authorization_url(
            redirect_uri=redirect_uri
        )
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    
    async def handle_callback(
        self,
        provider: str,
        code: str,
        redirect_uri: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Handle OAuth callback and create/login user"""
        # Exchange code for token
        client = self.oauth.create_client(provider)
        token = await client.fetch_token(
            authorization_response=redirect_uri,
            code=code
        )
        
        # Get user info from provider
        user_info = await self._get_user_info(provider, token['access_token'])
        
        # Find or create user
        user = await self._find_or_create_user(db, provider, user_info, token)
        
        return {
            "user": user,
            "token": token
        }
    
    async def _get_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Get user info from OAuth provider"""
        if provider == 'google':
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                return response.json()
        
        elif provider == 'apple':
            # Apple returns user info in ID token
            # Decode JWT token to get user info
            pass
        
        return {}
    
    async def _find_or_create_user(
        self,
        db: AsyncSession,
        provider: str,
        user_info: Dict[str, Any],
        token: Dict[str, Any]
    ) -> User:
        """Find existing user or create new one"""
        provider_user_id = user_info.get('id') or user_info.get('sub')
        email = user_info.get('email')
        
        # Check if OAuth account exists
        oauth_account = await db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id
            )
        )
        oauth_account = oauth_account.scalar_one_or_none()
        
        if oauth_account:
            # Update tokens
            oauth_account.access_token = encrypt_data(token['access_token'])
            if 'refresh_token' in token:
                oauth_account.refresh_token = encrypt_data(token['refresh_token'])
            await db.commit()
            return oauth_account.user
        
        # Check if user exists with this email
        user = await db.execute(
            select(User).where(User.email == email)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                oauth_only=True,
                is_email_verified=True,  # OAuth emails are verified
                is_active=True
            )
            db.add(user)
            await db.flush()
        
        # Create OAuth account link
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=email,
            access_token=encrypt_data(token['access_token']),
            refresh_token=encrypt_data(token.get('refresh_token', '')),
            profile_data=user_info
        )
        db.add(oauth_account)
        await db.commit()
        
        return user
```

### Step 4: Create OAuth Endpoints (Day 4-5)

**File: `app/api/v1/endpoints/oauth.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.services.oauth_service import OAuthService
from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth import TokenResponse

router = APIRouter()
oauth_service = OAuthService()

@router.get("/google/authorize")
async def google_authorize(request: Request):
    """Initiate Google OAuth flow"""
    redirect_uri = str(request.url_for('google_callback'))
    result = await oauth_service.get_authorization_url('google', redirect_uri)
    return result

@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google OAuth callback"""
    redirect_uri = str(request.url_for('google_callback'))
    result = await oauth_service.handle_callback('google', code, redirect_uri, db)
    
    user = result['user']
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/apple/authorize")
async def apple_authorize(request: Request):
    """Initiate Apple OAuth flow"""
    redirect_uri = str(request.url_for('apple_callback'))
    result = await oauth_service.get_authorization_url('apple', redirect_uri)
    return result

@router.post("/apple/callback")
async def apple_callback(
    code: str,
    state: str,
    user: Optional[str] = None,  # Apple sends user data on first auth
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle Apple OAuth callback (POST)"""
    redirect_uri = str(request.url_for('apple_callback'))
    result = await oauth_service.handle_callback('apple', code, redirect_uri, db)
    
    user = result['user']
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
```

### Step 5: Update Frontend (Day 6-8)

**File: `coredent-style-main/src/services/oauthApi.ts`**
```typescript
export const initiateGoogleOAuth = async (): Promise<{ authorization_url: string; state: string }> => {
  const response = await api.get('/auth/oauth/google/authorize');
  return response.data;
};

export const initiateAppleOAuth = async (): Promise<{ authorization_url: string; state: string }> => {
  const response = await api.post('/auth/oauth/apple/authorize');
  return response.data;
};
```

**File: `coredent-style-main/src/components/auth/OAuthButtons.tsx`**
```typescript
import { Button } from '@/components/ui/button';
import { FcGoogle } from 'react-icons/fc';
import { FaApple } from 'react-icons/fa';

export const OAuthButtons = () => {
  const handleGoogleLogin = async () => {
    const { authorization_url } = await initiateGoogleOAuth();
    window.location.href = authorization_url;
  };
  
  const handleAppleLogin = async () => {
    const { authorization_url } = await initiateAppleOAuth();
    window.location.href = authorization_url;
  };
  
  return (
    <div className="space-y-2">
      <Button
        variant="outline"
        className="w-full"
        onClick={handleGoogleLogin}
      >
        <FcGoogle className="mr-2 h-5 w-5" />
        Continue with Google
      </Button>
      
      <Button
        variant="outline"
        className="w-full bg-black text-white hover:bg-gray-800"
        onClick={handleAppleLogin}
      >
        <FaApple className="mr-2 h-5 w-5" />
        Continue with Apple
      </Button>
    </div>
  );
};
```

### Step 6: Configuration (Day 9)

**Add to `.env.example`**:
```bash
# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret
OAUTH_REDIRECT_URI=https://app.coredent.com/auth/callback
```

### Step 7: Testing (Day 10-12)

**Create `tests/test_oauth.py`**:
```python
import pytest
from httpx import AsyncClient

class TestOAuthEndpoints:
    @pytest.mark.asyncio
    async def test_google_authorize(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/oauth/google/authorize")
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
    
    @pytest.mark.asyncio
    async def test_google_callback_success(self, client: AsyncClient, db_session):
        # Mock OAuth callback
        response = await client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "test_code", "state": "test_state"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
```

### Step 8: Documentation (Day 13-14)

Create user-facing documentation:
- How to set up Google OAuth
- How to set up Apple OAuth
- How to link/unlink OAuth accounts
- Troubleshooting guide

---

## 🔒 Security Considerations

1. **State Parameter**: Prevent CSRF attacks
2. **Token Encryption**: Encrypt OAuth tokens at rest
3. **Scope Limitation**: Request minimum necessary scopes
4. **Token Refresh**: Implement token refresh logic
5. **Account Linking**: Verify email before linking accounts
6. **Audit Logging**: Log all OAuth events

---

## 📊 Success Metrics

- [ ] Google OAuth working end-to-end
- [ ] Apple OAuth working end-to-end
- [ ] Users can link multiple OAuth accounts
- [ ] Users can unlink OAuth accounts
- [ ] Existing users can add OAuth to their account
- [ ] New users can sign up with OAuth
- [ ] All OAuth events logged in audit log
- [ ] 90%+ test coverage for OAuth code

---

## 🚀 Deployment Checklist

- [ ] Create Google OAuth app in Google Cloud Console
- [ ] Create Apple OAuth app in Apple Developer Portal
- [ ] Configure redirect URIs in OAuth apps
- [ ] Add OAuth credentials to production environment
- [ ] Run database migration to add oauth_accounts table
- [ ] Deploy backend with OAuth endpoints
- [ ] Deploy frontend with OAuth buttons
- [ ] Test OAuth flow in staging
- [ ] Monitor OAuth success/failure rates

---

## 📚 Resources

- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Apple Sign In Documentation](https://developer.apple.com/sign-in-with-apple/)
- [Authlib Documentation](https://docs.authlib.org/)
- [FastAPI OAuth Guide](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)

---

**Status**: ⏳ **PENDING**  
**Priority**: HIGH  
**Estimated Completion**: 2-3 weeks  
**Blocker For**: Mobile app launch

