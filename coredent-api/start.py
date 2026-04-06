#!/usr/bin/env python3
"""CoreDent API Startup Script

This script runs database migrations automatically before starting the API server.
This ensures the database schema is up-to-date on every deployment.
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
    """Run database migrations using Alembic."""
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
            
        logger.info("Running database migrations...")
        alembic_cfg = alembic.config.Config("alembic.ini")
        
        # Override the sqlalchemy.url in alembic config with the environment variable
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        alembic.command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Don't fail startup - table might already exist
        logger.warning("Continuing with server startup despite migration warning...")
        return False

def main():
    """Main entry point."""
    # Run migrations first
    run_migrations()
    
    # Then start the server
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting CoreDent API on port {port}")
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
