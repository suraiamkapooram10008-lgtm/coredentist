"""
Simple Configuration without pydantic-settings JSON parsing issues
"""

import os
from typing import List
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class SimpleSettings:
    """Simple settings class that avoids pydantic-settings JSON parsing"""
    
    def __init__(self):
        # Application
        self.APP_NAME = "CoreDent API"
        self.APP_VERSION = "1.0.0"
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./coredent_dev.db")
        self.DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
        
        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-for-hipaa-compliance")
        self.ALGORITHM = "HS256"
        # Default 15 min per HIPAA best-practice session timeout
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # CORS - Parse comma-separated string
        cors_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://localhost:8082")
        self.CORS_ORIGINS = [origin.strip() for origin in cors_str.split(",") if origin.strip()]
        
        # Allowed hosts - Parse comma-separated string
        hosts_str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
        self.ALLOWED_HOSTS = [host.strip() for host in hosts_str.split(",") if host.strip()]
        
        # Rate limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        
        # Frontend URL
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Email
        self.SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USER = os.getenv("SMTP_USER", "")
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
        self.SMTP_FROM = os.getenv("SMTP_FROM", "noreply@coredent.com")
        self.SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CoreDent PMS")
        
        # AWS
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        
        # Encryption
        self.ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "dev-encryption-key-change-in-production")
        
        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "")
        self.REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))
        
        # Sentry
        self.SENTRY_DSN = os.getenv("SENTRY_DSN", "")
        
        # Stripe Payments (Optional - US Market)
        self.STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
        self.STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        
        # Razorpay Payments (Optional - Indian Market)
        self.RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
        self.RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
        self.RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
        
        # Insurance EDI - DentalXChange (Optional)
        self.DXC_API_KEY = os.getenv("DXC_API_KEY", "")
        self.DXC_API_SECRET = os.getenv("DXC_API_SECRET", "")
        self.DXC_BASE_URL = os.getenv("DXC_BASE_URL", "https://api.dentalxchange.com/v2")
        
        # QuickBooks Integration (Optional)
        self.QB_CLIENT_ID = os.getenv("QB_CLIENT_ID", "")
        self.QB_CLIENT_SECRET = os.getenv("QB_CLIENT_SECRET", "")
        self.QB_REDIRECT_URI = os.getenv("QB_REDIRECT_URI", "")
        self.QB_ENVIRONMENT = os.getenv("QB_ENVIRONMENT", "sandbox")
        
        # File Upload
        self.MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))
        ext_str = os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png,doc,docx")
        self.ALLOWED_EXTENSIONS = [ext.strip() for ext in ext_str.split(",") if ext.strip()]
        
        # Pagination
        self.DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
        self.MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
        
        # HIPAA Compliance
        self.AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
        self.SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "15"))
        self.PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "12"))
        self.PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
        self.PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
        self.PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
        self.PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
        self.PASSWORD_EXPIRE_DAYS = int(os.getenv("PASSWORD_EXPIRE_DAYS", "90"))
        
        # Monitoring
        self.MONITORING_TOKEN = os.getenv("MONITORING_TOKEN", "")

        # Reject common placeholder DSN so operators notice the mistake
        if self.SENTRY_DSN and (
            "your-sentry-dsn" in self.SENTRY_DSN
            or self.SENTRY_DSN.strip().lower() in {"changeme", "todo", "tbd"}
        ):
            # Clear it so main.py treats it as unset rather than initializing
            # Sentry with a DSN that will 100% fail.
            self.SENTRY_DSN = ""

        # Production safety checks
        if self.ENVIRONMENT == "production":
            # Detect insecure/dev defaults explicitly
            insecure_secret = (
                not os.getenv("SECRET_KEY")
                or self.SECRET_KEY.startswith("dev-secret-key")
                or len(self.SECRET_KEY) < 32
            )
            insecure_enc = (
                not os.getenv("ENCRYPTION_KEY")
                or self.ENCRYPTION_KEY.startswith("dev-encryption-key")
            )
            missing = []
            if insecure_enc:
                missing.append("ENCRYPTION_KEY")
            if insecure_secret:
                missing.append("SECRET_KEY")
            if missing:
                raise RuntimeError(
                    f"Production requires secure values for: {', '.join(missing)}. "
                    "Set these env vars to strong, unique production values."
                )

# Create settings instance
settings = SimpleSettings()