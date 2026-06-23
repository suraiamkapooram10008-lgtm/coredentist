"""
Application configuration.

This module reads from environment variables and enforces strict
production-safety checks.  The principle: **fail closed at import time**.
If a required production setting is missing or is a known-bad default, the
process refuses to start rather than running insecurely.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised at import time when a required production setting is missing
    or unsafe."""


# Sentinel dev-defaults that we *must never* see in production.
_BAD_SECRET_PREFIXES = (
    "dev-secret-key",
    "change-me",
    "your-secret",
    "todo",
    "tbd",
)
_BAD_ENCRYPTION_PREFIXES = (
    "dev-encryption-key",
    "change-me",
    "todo",
    "tbd",
)


class SimpleSettings:
    def __init__(self):
        # Application
        self.APP_NAME = "CoreDent API"
        self.APP_VERSION = "1.0.0"
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

        # Database
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./coredent_dev.db"
        )
        self.DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

        # Security
        self.SECRET_KEY = os.getenv(
            "SECRET_KEY", "dev-secret-key-change-in-production-for-hipaa-compliance"
        )
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
        )
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        # CORS
        cors_str = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://localhost:8082",
        )
        self.CORS_ORIGINS = [o.strip() for o in cors_str.split(",") if o.strip()]

        # Allowed hosts
        hosts_str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
        self.ALLOWED_HOSTS = [h.strip() for h in hosts_str.split(",") if h.strip()]

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
        self.AWS_S3_BUCKET_NAME = (
            os.getenv("AWS_S3_BUCKET_NAME", "") or self.AWS_S3_BUCKET
        )
        self.AWS_CLOUDFRONT_DOMAIN = os.getenv("AWS_CLOUDFRONT_DOMAIN", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

        # Encryption (single key, retained for backward compat; keyring prefers
        # ENCRYPTION_KEYS for rotation).
        self.ENCRYPTION_KEY = os.getenv(
            "ENCRYPTION_KEY", "dev-encryption-key-change-in-production"
        )
        self.ENCRYPTION_KEYS = os.getenv("ENCRYPTION_KEYS", "")
        self.SEARCH_INDEX_KEY = os.getenv("SEARCH_INDEX_KEY", "")

        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "")
        self.REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))

        # Sentry
        self.SENTRY_DSN = os.getenv("SENTRY_DSN", "")

        # Stripe
        self.STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
        self.STRIPE_SECRET_KEY = (
            os.getenv("STRIPE_SECRET_KEY", "") or self.STRIPE_API_KEY
        )
        self.STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        self.STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.STRIPE_WEBHOOK_IP_WHITELIST_ENABLED = (
            os.getenv("STRIPE_WEBHOOK_IP_WHITELIST_ENABLED", "true").lower() == "true"
        )
        self.STRIPE_WEBHOOK_HMAC_SECRET = os.getenv("STRIPE_WEBHOOK_HMAC_SECRET", "")

        # CAPTCHA
        self.RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")
        self.RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
        self.HCAPTCHA_SECRET_KEY = os.getenv("HCAPTCHA_SECRET_KEY", "")
        self.HCAPTCHA_SITE_KEY = os.getenv("HCAPTCHA_SITE_KEY", "")

        # Celery
        self.CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "") or self.REDIS_URL
        self.CELERY_RESULT_BACKEND = (
            os.getenv("CELERY_RESULT_BACKEND", "") or self.REDIS_URL
        )

        # Razorpay
        self.RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
        self.RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
        self.RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

        # Insurance EDI
        self.DXC_API_KEY = os.getenv("DXC_API_KEY", "")
        self.DXC_API_SECRET = os.getenv("DXC_API_SECRET", "")
        self.DXC_BASE_URL = os.getenv(
            "DXC_BASE_URL", "https://api.dentalxchange.com/v2"
        )

        # QuickBooks
        self.QB_CLIENT_ID = os.getenv("QB_CLIENT_ID", "")
        self.QB_CLIENT_SECRET = os.getenv("QB_CLIENT_SECRET", "")
        self.QB_REDIRECT_URI = os.getenv("QB_REDIRECT_URI", "")
        self.QB_ENVIRONMENT = os.getenv("QB_ENVIRONMENT", "sandbox")

        # File upload
        self.MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))
        ext_str = os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png,doc,docx")
        self.ALLOWED_EXTENSIONS = [e.strip() for e in ext_str.split(",") if e.strip()]

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

        # Sentry DSN placeholder rejection
        if self.SENTRY_DSN and (
            "your-sentry-dsn" in self.SENTRY_DSN
            or self.SENTRY_DSN.strip().lower() in {"changeme", "todo", "tbd"}
        ):
            self.SENTRY_DSN = ""

        # Production safety net.  Every one of these would let the system run
        # but cause silent failures; we fail boot loudly instead.
        if self.ENVIRONMENT == "production":
            errors = []
            if not os.getenv("SECRET_KEY") or self.SECRET_KEY.startswith(_BAD_SECRET_PREFIXES):
                errors.append(
                    "SECRET_KEY is missing or uses a known-bad default "
                    "(must be set to a strong, unique production value)."
                )
            elif len(self.SECRET_KEY) < 32:
                errors.append("SECRET_KEY must be at least 32 characters.")

            # Encryption keys
            multi = self.ENCRYPTION_KEYS.strip()
            legacy = (self.ENCRYPTION_KEY or "").strip()
            if not multi and (not legacy or legacy.startswith(_BAD_ENCRYPTION_PREFIXES)):
                errors.append(
                    "ENCRYPTION_KEYS (or legacy ENCRYPTION_KEY) is required in "
                    "production. Generate one with: "
                    'python -c "from app.core.encryption import generate_key; '
                    'print(generate_key())"'
                )

            if not self.SENTRY_DSN:
                errors.append(
                    "SENTRY_DSN is required in production. Set the DSN from "
                    "your Sentry project dashboard; otherwise you will have "
                    "NO visibility into production errors."
                )

            if not self.STRIPE_WEBHOOK_SECRET:
                errors.append(
                    "STRIPE_WEBHOOK_SECRET is required in production. Stripe "
                    "webhooks will not be verified and the app will refuse to "
                    "process payment events until this is set."
                )

            if not self.REDIS_URL:
                errors.append(
                    "REDIS_URL is required in production. The in-process "
                    "rate limiter does not work across multiple workers and "
                    "is unsafe for a multi-replica deployment."
                )

            if not self.SMTP_USER or self.SMTP_HOST == "localhost":
                errors.append(
                    "SMTP is not configured. Password resets, email "
                    "verification, and appointment reminders will fail. "
                    "Configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD before "
                    "going to production."
                )

            if not self.AWS_S3_BUCKET:
                errors.append(
                    "AWS_S3_BUCKET is not set. File and image uploads will "
                    "fail. Configure an S3 bucket (or compatible store) "
                    "before going to production."
                )

            if not self.ALLOWED_HOSTS or self.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]:
                errors.append(
                    "ALLOWED_HOSTS is set to development defaults. Configure "
                    "your production domain(s) to protect against Host "
                    "header attacks."
                )

            if self.CORS_ORIGINS and any("localhost" in o for o in self.CORS_ORIGINS):
                errors.append(
                    "CORS_ORIGINS contains a localhost origin. Remove it "
                    "before going to production."
                )

            if errors:
                raise ConfigError(
                    "Refusing to start in production:\n  - "
                    + "\n  - ".join(errors)
                    + "\nSee docs/PRODUCTION_REQUIRED_ENV.md for the full list."
                )


settings = SimpleSettings()
