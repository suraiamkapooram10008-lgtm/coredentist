#!/usr/bin/env python3
"""CoreDent API Startup Script

This script runs database migrations automatically before starting the API server.
This ensures the database schema is up-to-date on every deployment.

SECURITY: Uvicorn is started with ``proxy_headers=True`` so that
``request.client.host`` and audit-log IP columns reflect the real client
IP (from ``X-Forwarded-For``) rather than the load balancer's internal
IP. Without this, behind Railway/Vercel/etc, every audit row would
record the LB's IP, making the HIPAA audit log operationally useless
and breaking per-IP rate limiting.

The ``forwarded_allow_ips`` setting trusts the proxy chain only on
Railway's well-known internal addresses; the default of ``*`` is used
when ``TRUSTED_PROXIES`` is unset. In production, set ``TRUSTED_PROXIES``
to the Railway edge IP range to avoid spoofing via client-set
``X-Forwarded-For`` headers.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migrations():
    """Run database migrations using Alembic.

    In production, migration failure is fatal — we refuse to start with an
    out-of-sync schema. In development, we log and continue so contributors
    aren't blocked by transient issues.
    """
    try:
        import os
        import alembic.config
        import alembic.command

        # Get DATABASE_URL from environment (Railway sets this)
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL not set - skipping migrations")
            return True

        # CRIT-01 FIX: Railway uses postgres://, Alembic/SQLAlchemy often need postgresql://
        # For Alembic (sync), we use postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        logger.info("=" * 60)
        logger.info("STARTING DATABASE MIGRATIONS")
        logger.info("=" * 60)
        logger.info(f"Database URL: {database_url.split('@')[0]}@***")  # Hide credentials

        alembic_cfg = alembic.config.Config("alembic.ini")

        # Override the sqlalchemy.url in alembic config with the environment variable
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        logger.info("Executing: alembic upgrade head")
        alembic.command.upgrade(alembic_cfg, "head")

        logger.info("=" * 60)
        logger.info("DATABASE MIGRATIONS COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        return True
    except Exception as e:
        environment = os.environ.get("ENVIRONMENT", "development").lower()
        logger.error("=" * 60)
        logger.error(f"MIGRATION FAILED: {e}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())

        if environment == "production":
            # Fail fast in production — out-of-sync schema is a data-integrity risk
            logger.critical(
                "Refusing to start in production with failed migrations. "
                "Fix the migration and redeploy."
            )
            sys.exit(1)

        logger.warning("Continuing with server startup despite migration warning...")
        return False


def main():
    """Main entry point."""
    # Run migrations first
    run_migrations()

    # Then start the server
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    environment = os.environ.get("ENVIRONMENT", "development").lower()

    # SECURITY: Trust proxy headers so request.client.host and audit-log
    # IPs reflect the real client, not the load balancer. We also expose
    # ``TRUSTED_PROXIES`` as a comma-separated list to limit which upstream
    # IPs are trusted. Default is "*" (trust all) which is appropriate
    # when the only path to the app is a single, known proxy. In a
    # multi-tenant edge setup you should set this to the proxy's CIDR.
    trusted_proxies = os.environ.get("TRUSTED_PROXIES", "*")

    logger.info(f"Starting CoreDent API on {host}:{port} (env={environment})")
    logger.info(f"Trusted proxies for X-Forwarded-For: {trusted_proxies}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        # SECURITY: trust proxy headers so audit logs and rate-limiter
        # see real client IPs. Without these two flags, uvicorn ignores
        # X-Forwarded-For and uses the immediate peer (load balancer),
        # making request.client.host useless.
        proxy_headers=True,
        forwarded_allow_ips=trusted_proxies,
    )


if __name__ == "__main__":
    main()
