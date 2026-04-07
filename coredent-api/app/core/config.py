"""
Application Configuration
Loads settings from environment variables
"""

from typing import List, Any
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "CoreDent API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # SECURITY: Default to False for production
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str = ""  # Required in production, can be empty in dev
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 20  # Allow burst capacity in production
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - Read from environment variable, with Railway defaults
    CORS_ORIGINS: List[str] = []
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v == "insecure-default-key-for-dev-only-change-in-production":
            import warnings
            warnings.warn(
                "SECURITY WARNING: Using default insecure SECRET_KEY. "
                "This must be changed in production for HIPAA compliance.",
                UserWarning
            )
        return v
    
    # Monitoring token for /metrics endpoint (SECURITY FIX)
    MONITORING_TOKEN: str = ""
    
    # Allowed hosts for production (SECURITY FIX: No wildcard)
    ALLOWED_HOSTS: List[str] = []
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: Any) -> Any:
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v if v else []
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Frontend URL for links
    FRONTEND_URL: str = ""
    
    # Email (Optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@coredent.com"
    SMTP_FROM_NAME: str = "CoreDent PMS"
    
    # AWS S3 (Optional)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"
    
    # Encryption (Required for production)
    ENCRYPTION_KEY: str = ""  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    
    # Redis (Optional)
    REDIS_URL: str = ""
    REDIS_CACHE_TTL: int = 3600
    
    # Sentry (Optional)
    SENTRY_DSN: str = ""
    
    # Stripe Payments (Optional - US Market)
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Razorpay Payments (Optional - Indian Market)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    
    # Insurance EDI - DentalXChange (Optional)
    DXC_API_KEY: str = ""
    DXC_API_SECRET: str = ""
    DXC_BASE_URL: str = "https://api.dentalxchange.com/v2"
    
    # QuickBooks Integration (Optional)
    QB_CLIENT_ID: str = ""
    QB_CLIENT_SECRET: str = ""
    QB_REDIRECT_URI: str = ""
    QB_ENVIRONMENT: str = "sandbox"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "doc", "docx"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    # HIPAA Compliance - SECURED: Session timeout 15 minutes per HIPAA
    AUDIT_LOG_ENABLED: bool = True
    SESSION_TIMEOUT_MINUTES: int = 15  # HIPAA requires 15-minute timeout for healthcare
    PASSWORD_MIN_LENGTH: int = 12  # HIPAA recommends 12+ for healthcare systems
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_EXPIRE_DAYS: int = 90  # HIPAA recommends password expiration
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins_default(cls, v: Any) -> Any:
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else []
        if not v:
            # Return Railway defaults if not set
            return [
                "https://respectful-strength-production-ef28.up.railway.app",
                "https://coredentist-production.up.railway.app"
            ]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


def validate_production_config() -> None:
    """Validate required production configuration"""
    if settings.ENVIRONMENT == "production":
        # Check SECRET_KEY
        if settings.SECRET_KEY == "insecure-default-key-for-dev-only-change-in-production":
            raise ValueError("SECURITY: SECRET_KEY must be changed in production")
        
        # Check ENCRYPTION_KEY is set
        if not settings.ENCRYPTION_KEY:
            raise ValueError("SECURITY: ENCRYPTION_KEY must be set in production")
        
        # Check DATABASE_URL is set
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL must be configured in production")


# Create settings instance (must be before validation)
settings = Settings()

# Validate production config on import
validate_production_config()
