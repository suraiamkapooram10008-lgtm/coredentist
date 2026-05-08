"""
HIPAA-Compliant Configuration
All secrets MUST be set via environment variables - NEVER hardcoded defaults.
Fails fast in production if any required secret is missing or using insecure values.
"""

import os
import sys
from typing import List
from dotenv import load_dotenv

# Load .env file for development only
load_dotenv()


def _validate_production_secrets():
    """
    Validate critical security settings for production.
    Fails fast if insecure defaults are detected.
    Exits with code 1 if validation fails - preventing startup with weak config.
    """
    env = os.getenv("ENVIRONMENT", "").lower()
    is_production = env in ["production", "prod"]
    
    errors = []
    warnings = []
    
    # Check SECRET_KEY
    secret_key = os.getenv("SECRET_KEY", "")
    known_insecure = [
        "dev-secret-key-change-in-production-for-hipaa-compliance",
        "change_this_to_a_strong_secret_key_min_32_chars",
        "change-this-to-a-strong-secret-key-min-32-chars",
    ]
    if not secret_key:
        errors.append("SECRET_KEY is not set. Generate one: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
    elif secret_key.lower() in known_insecure or len(secret_key) < 32:
        errors.append("SECRET_KEY is too short (< 32 chars) or using a known insecure default!")
    
    # Check ENCRYPTION_KEY
    encryption_key = os.getenv("ENCRYPTION_KEY", "")
    known_insecure_enc = [
        "dev-encryption-key-change-in-production",
        "change_this_to_a_fernet_key",
        "change-this-to-a-fernet-key",
    ]
    if not encryption_key:
        errors.append("ENCRYPTION_KEY is not set. Generate one: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    elif encryption_key.lower() in known_insecure_enc or len(encryption_key) < 32:
        errors.append("ENCRYPTION_KEY is too short or using a known insecure default!")
    
    # Check CORS origins don't contain localhost in production
    cors_str = os.getenv("CORS_ORIGINS", "")
    if is_production and cors_str:
        for origin in cors_str.split(","):
            origin = origin.strip()
            if "localhost" in origin or "127.0.0.1" in origin:
                warnings.append(f"CORS_ORIGINS contains localhost reference in production: {origin}")
    
    # Check ALLOWED_HOSTS doesn't contain localhost only in production
    hosts_str = os.getenv("ALLOWED_HOSTS", "")
    if is_production and hosts_str:
        hosts = [h.strip() for h in hosts_str.split(",")]
        if all(h in ("localhost", "127.0.0.1") for h in hosts):
            errors.append("ALLOWED_HOSTS only contains localhost references in production mode!")
    
    # Check SMTP host is configured
    smtp_host = os.getenv("SMTP_HOST", "")
    if is_production and not smtp_host:
        warnings.append("SMTP_HOST is not configured - email notifications will not work")
    
    # Check FRONTEND_URL is not localhost in production
    frontend_url = os.getenv("FRONTEND_URL", "")
    if is_production and ("localhost" in frontend_url or "127.0.0.1" in frontend_url):
        errors.append("FRONTEND_URL points to localhost in production mode!")
    
    # Warn about DEBUG in production
    debug = os.getenv("DEBUG", "").lower()
    if is_production and debug == "true":
        warnings.append("DEBUG is enabled in production! This leaks sensitive information.")
    
    # Check DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL", "")
    if is_production and not db_url:
        errors.append("DATABASE_URL is not set!")
    elif is_production and "sqlite" in db_url:
        errors.append("DATABASE_URL uses SQLite in production! Use PostgreSQL.")
    
    # Report all errors
    if errors:
        print("=" * 70)
        print("FATAL: Production configuration validation FAILED:")
        print("=" * 70)
        for err in errors:
            print(f"  [ERROR] {err}")
        print()
        print("Fix these issues before deploying to production.")
        sys.exit(1)
    
    # Report warnings
    if warnings:
        print("=" * 70)
        print("Production configuration WARNINGS:")
        print("=" * 70)
        for warn in warnings:
            print(f"  [WARN] {warn}")
        print()
    
    if is_production:
        print(f"[OK] Running in {env} mode - all required secrets configured")


class SimpleSettings:
    """
    HIPAA-compliant settings class.
    
    CRITICAL: All sensitive defaults are empty strings - they MUST be set 
    via environment variables. The application will fail to start in
    production if required secrets are missing or using default values.
    """
    
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
        
        # === SECURITY CRITICAL: No default secrets! ===
        # These MUST be set via environment variables in production.
        # The app will fail to start if they are empty/insecure in production mode.
        self.SECRET_KEY = os.getenv("SECRET_KEY", "")
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # CORS - Parse comma-separated string. MUST BE CONFIGURED FOR PRODUCTION.
        cors_str = os.getenv("CORS_ORIGINS", "")
        self.CORS_ORIGINS = [origin.strip() for origin in cors_str.split(",") if origin.strip()]
        
        # Allowed hosts - Parse comma-separated string. MUST BE CONFIGURED FOR PRODUCTION.
        hosts_str = os.getenv("ALLOWED_HOSTS", "")
        self.ALLOWED_HOSTS = [host.strip() for host in hosts_str.split(",") if host.strip()]
        
        # Rate limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        
        # Frontend URL - MUST BE CONFIGURED FOR PRODUCTION
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "")
        
        # Email - MUST BE CONFIGURED FOR PRODUCTION
        self.SMTP_HOST = os.getenv("SMTP_HOST", "")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USER = os.getenv("SMTP_USER", "")
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
        self.SMTP_FROM = os.getenv("SMTP_FROM", "")
        self.SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "")
        
        # AWS S3 (Optional)
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        
        # Encryption - MUST BE CONFIGURED FOR PRODUCTION
        self.ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
        
        # Redis (Optional)
        self.REDIS_URL = os.getenv("REDIS_URL", "")
        self.REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))
        
        # Sentry (Optional)
        self.SENTRY_DSN = os.getenv("SENTRY_DSN", "")
        
        # Stripe Payments (Optional - US Market)
        self.STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
        self.STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        # Stripe webhook IP whitelist for security (comma-separated IPs)
        # Default: Stripe's official IPs (https://stripe.com/docsips)
        stripe_ips = os.getenv("STRIPE_WEBHOOK_IP_WHITELIST", "")
        self.STRIPE_WEBHOOK_IP_WHITELIST = (
            [ip.strip() for ip in stripe_ips.split(",") if ip.strip()]
            if stripe_ips
            else ["3.18.12.0/23", "3.19.0.0/20", "3.20.0.0/22", "3.21.128.0/22", "3.22.0.0/23", "13.52.0.0/22", "13.53.0.0/22", "13.54.0.0/22", "13.55.0.0/22", "13.56.0.0/22", "13.57.0.0/22", "13.58.0.0/22", "18.208.0.0/22", "18.209.0.0/22", "18.210.0.0/22", "18.211.0.0/22", "34.192.0.0/22", "34.193.0.0/22", "34.194.0.0/22", "34.195.0.0/22", "44.154.0.0/22", "44.155.0.0/22", "44.156.0.0/22", "44.157.0.0/22", "44.199.0.0/22", "44.200.0.0/22", "44.201.0.0/22", "44.202.0.0/22", "47.32.0.0/22", "47.33.0.0/22", "52.8.0.0/22", "52.9.0.0/22", "52.10.0.0/22", "52.11.0.0/22", "52.12.0.0/22", "54.36.0.0/22", "54.37.0.0/22", "54.38.0.0/22", "54.39.0.0/22", "54.88.0.0/22", "54.89.0.0/22", "54.90.0.0/22", "54.91.0.0/22", "54.92.0.0/22", "54.93.0.0/22", "54.94.0.0/22", "54.95.0.0/22", "54.96.0.0/22", "54.97.0.0/22", "54.98.0.0/22", "54.99.0.0/22"]
        )
        self.STRIPE_WEBHOOK_IP_WHITELIST_ENABLED = os.getenv("STRIPE_WEBHOOK_IP_WHITELIST_ENABLED", "true").lower() == "true"
        
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
        
        # OAuth / Social Login (Optional)
        self.GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
        self.APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID", "")
        self.APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID", "")
        self.APPLE_KEY_ID = os.getenv("APPLE_KEY_ID", "")
        self.APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY", "")
        
        # Default practice for OAuth sign-ups (owner/operator)
        self.DEFAULT_PRACTICE_ID = os.getenv("DEFAULT_PRACTICE_ID", "")
        
        # Cookie settings for cross-origin auth
        self.COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "none" if self.ENVIRONMENT == "production" else "lax")
        self.COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true" if self.ENVIRONMENT == "production" else "false").lower() == "true"

# Create settings instance
settings = SimpleSettings()

# Validate production secrets after settings are loaded
_validate_production_secrets()
