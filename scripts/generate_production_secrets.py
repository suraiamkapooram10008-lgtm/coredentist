#!/usr/bin/env python3
"""
Production Secrets Generator for CoreDent API
==============================================
Generates cryptographically secure secrets for HIPAA-compliant production deployment.

Usage:
    python scripts/generate_production_secrets.py                # Print to stdout
    python scripts/generate_production_secrets.py --output .env.production  # Write to file

The generated secrets are cryptographically secure and meet HIPAA requirements:
- SECRET_KEY: 48-byte random URL-safe string (exceeds 32-char HIPAA minimum)
- ENCRYPTION_KEY: Fernet-compatible 32-byte key
- Monitoring token: 64-char hex string
"""

import secrets
import string
import sys
import os
from datetime import datetime


def generate_secret_key(length: int = 48) -> str:
    """Generate a cryptographically secure secret key (min 32 chars for HIPAA)."""
    return secrets.token_urlsafe(length)


def generate_fernet_key() -> str:
    """Generate a Fernet-compatible encryption key (44 base64 chars)."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


def generate_password(length: int = 24) -> str:
    """Generate a strong random password with mixed characters."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_monitoring_token() -> str:
    """Generate a random monitoring token (64 hex chars)."""
    return secrets.token_hex(32)


def generate_env_file(output_path: str | None = None) -> str:
    """Generate the .env.production file content."""
    lines = [
        "# ====================================================================",
        "# CoreDent Production Secrets (auto-generated)",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# WARNING: Keep this file secure! NEVER commit to version control.",
        "# ====================================================================",
        "",
        "# === ENVIRONMENT ===",
        "ENVIRONMENT=production",
        "DEBUG=false",
        "APP_NAME=CoreDent API",
        "",
        "# ====================================================================",
        "# SECURITY CRITICAL — These MUST be >= 32 chars for HIPAA compliance",
        "# ====================================================================",
        f"SECRET_KEY={generate_secret_key(48)}",
        f"ENCRYPTION_KEY={generate_fernet_key()}",
        "ACCESS_TOKEN_EXPIRE_MINUTES=15",
        "REFRESH_TOKEN_EXPIRE_DAYS=7",
        "",
        "# ====================================================================",
        "# DATABASE — Configure with actual production credentials",
        "# ====================================================================",
        "# DATABASE_URL=postgresql://user:password@host:5432/coredent",
        "DATABASE_POOL_SIZE=10",
        "DATABASE_MAX_OVERFLOW=20",
        "",
        "# ====================================================================",
        "# CORS & ALLOWED HOSTS — Restrict to your actual domains",
        "# ====================================================================",
        "# CORS_ORIGINS=https://app.coredent.com,https://admin.coredent.com",
        "# ALLOWED_HOSTS=api.coredent.com",
        "",
        "# ====================================================================",
        "# FRONTEND URL",
        "# ====================================================================",
        "# FRONTEND_URL=https://app.coredent.com",
        "",
        "# ====================================================================",
        "# EMAIL (SMTP) — Required for notifications and password resets",
        "# ====================================================================",
        "# SMTP_HOST=smtp.sendgrid.net",
        "# SMTP_PORT=587",
        "# SMTP_USER=apikey",
        f"# SMTP_PASSWORD={generate_password(24)}",
        "# SMTP_FROM=noreply@coredent.com",
        "# SMTP_FROM_NAME=CoreDent",
        "",
        "# ====================================================================",
        "# AWS S3 (optional) — File uploads and backup storage",
        "# ====================================================================",
        "# AWS_ACCESS_KEY_ID=",
        "# AWS_SECRET_ACCESS_KEY=",
        "# AWS_S3_BUCKET=coredent-uploads",
        "# AWS_REGION=us-east-1",
        "",
        "# ====================================================================",
        "# REDIS (optional) — Caching and rate limiting",
        "# ====================================================================",
        f"# REDIS_URL=redis://default:{generate_password(16)}@host:6379/0",
        "# REDIS_CACHE_TTL=3600",
        "",
        "# ====================================================================",
        "# STRIPE (optional) — US payment processing",
        "# ====================================================================",
        "# STRIPE_API_KEY=",
        "# STRIPE_WEBHOOK_SECRET=",
        "",
        "# ====================================================================",
        "# RAZORPAY (optional) — India payment processing",
        "# ====================================================================",
        "# RAZORPAY_KEY_ID=",
        "# RAZORPAY_KEY_SECRET=",
        "# RAZORPAY_WEBHOOK_SECRET=",
        "",
        "# ====================================================================",
        "# SENTRY (optional) — Error tracking",
        "# ====================================================================",
        "# SENTRY_DSN=https://key@sentry.io/project",
        "",
        "# ====================================================================",
        "# MONITORING",
        "# ====================================================================",
        f"MONITORING_TOKEN={generate_monitoring_token()}",
        "",
        "# ====================================================================",
        "# RATE LIMITING",
        "# ====================================================================",
        "RATE_LIMIT_PER_MINUTE=60",
        "",
        "# ====================================================================",
        "# HIPAA COMPLIANCE SETTINGS",
        "# ====================================================================",
        "AUDIT_LOG_ENABLED=true",
        "SESSION_TIMEOUT_MINUTES=15",
        "PASSWORD_MIN_LENGTH=12",
        "PASSWORD_REQUIRE_UPPERCASE=true",
        "PASSWORD_REQUIRE_LOWERCASE=true",
        "PASSWORD_REQUIRE_DIGIT=true",
        "PASSWORD_REQUIRE_SPECIAL=true",
        "PASSWORD_EXPIRE_DAYS=90",
        "",
        "# ====================================================================",
        "# OAUTH / SOCIAL LOGIN (optional)",
        "# ====================================================================",
        "# GOOGLE_OAUTH_CLIENT_ID=",
        "# APPLE_CLIENT_ID=",
        "# APPLE_TEAM_ID=",
        "# APPLE_KEY_ID=",
        "# APPLE_PRIVATE_KEY=",
        "",
        "# ====================================================================",
        "# INSURANCE EDI — DentalXChange (optional)",
        "# ====================================================================",
        "# DXC_API_KEY=",
        "# DXC_API_SECRET=",
        "# DXC_BASE_URL=https://api.dentalxchange.com/v2",
        "",
        "# ====================================================================",
        "# QUICKBOOKS INTEGRATION (optional)",
        "# ====================================================================",
        "# QB_CLIENT_ID=",
        "# QB_CLIENT_SECRET=",
        "# QB_REDIRECT_URI=https://api.coredent.com/api/v1/accounting/qb-callback",
        "# QB_ENVIRONMENT=production",
    ]

    content = "\n".join(lines) + "\n"

    if output_path:
        if os.path.exists(output_path):
            print(f"⚠️  Warning: {output_path} already exists. Overwriting.")
        with open(output_path, "w") as f:
            f.write(content)
        print(f"✅ Production secrets written to {output_path}")
    else:
        print(content)

    return content


def print_security_notes() -> None:
    """Print security recommendations."""
    notes = [
        "",
        "=" * 60,
        "SECURITY NOTES",
        "=" * 60,
        "• SECRET_KEY and ENCRYPTION_KEY are auto-generated and cryptographically secure",
        "• Placeholder values (prefixed with #) need manual configuration",
        "• NEVER commit .env.production to version control",
        "• Store in a secure vault (e.g., HashiCorp Vault, AWS Secrets Manager)",
        "• Rotate secrets every 90 days (HIPAA best practice)",
        "• Validate production config with:",
        "    python -c \"from app.core.config_simple import _validate_production_secrets; _validate_production_secrets()\"",
    ]
    print("\n".join(notes))


def main() -> None:
    """Main entry point."""
    output_file = None

    # Parse arguments
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "--output":
        output_file = args[1]
    elif len(args) == 1 and args[0] in ("-h", "--help"):
        print(__doc__.strip())
        sys.exit(0)

    generate_env_file(output_file)
    print_security_notes()


if __name__ == "__main__":
    main()