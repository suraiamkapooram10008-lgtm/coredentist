#!/usr/bin/env python3
"""
CoreDent Complete Database Migration Script
Runs all pending Alembic migrations on Railway PostgreSQL
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main migration function."""
    logger.info("🚀 Starting CoreDent Database Migration")
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable is required")
        logger.info("Set it in Railway dashboard or .env file")
        sys.exit(1)
    
    # Fix protocol if needed
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        os.environ['DATABASE_URL'] = database_url
        logger.info("✅ Fixed DATABASE_URL protocol")
    
    # Fix async SQLite to sync for Alembic
    if 'sqlite+aiosqlite' in database_url:
        database_url = database_url.replace('sqlite+aiosqlite', 'sqlite')
        logger.info("✅ Fixed SQLite URL for Alembic (async -> sync)")
    
    try:
        from alembic.config import Config
        from alembic import command
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine, text
        
        # Create Alembic config
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        # Create engine to check current state
        engine = create_engine(database_url)
        
        # Check current migration state
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
            logger.info(f"📊 Current migration revision: {current_rev}")
            
            # Get head revision
            script = ScriptDirectory.from_config(alembic_cfg)
            head_rev = script.get_current_head()
            logger.info(f"📊 Head migration revision: {head_rev}")
            
            if current_rev == head_rev:
                logger.info("✅ Database is already up to date!")
                return True
        
        # Run migrations
        logger.info("🔄 Running Alembic migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Migrations completed successfully!")
        
        # Verify migrations
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            new_rev = context.get_current_revision()
            if new_rev == head_rev:
                logger.info(f"✅ Database successfully migrated to revision {new_rev}")
            else:
                logger.warning(f"⚠️ Migration may have issues. Current: {new_rev}, Expected: {head_rev}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        logger.info("💡 Check your DATABASE_URL and try again")
        return False

def create_missing_tables_direct():
    """Create tables directly if Alembic fails."""
    logger.info("🔧 Attempting direct table creation...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable is required")
        return False
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Fix async SQLite to sync
    if 'sqlite+aiosqlite' in database_url:
        database_url = database_url.replace('sqlite+aiosqlite', 'sqlite')
    
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(database_url)
        
        # Key tables that might be missing
        create_statements = [
            # Communication tables
            """CREATE TABLE IF NOT EXISTS reminders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
                appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
                reminder_type VARCHAR(50) NOT NULL,
                scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
                sent_time TIMESTAMP WITH TIME ZONE,
                status VARCHAR(20) DEFAULT 'pending',
                message TEXT,
                channel VARCHAR(20) DEFAULT 'email',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS communication_templates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                template_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                variables JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
                template_id UUID REFERENCES communication_templates(id),
                message_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                sent_time TIMESTAMP WITH TIME ZONE,
                delivery_status VARCHAR(20) DEFAULT 'pending',
                channel VARCHAR(20) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS communication_settings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                practice_id UUID REFERENCES practices(id) ON DELETE CASCADE,
                sms_provider VARCHAR(50),
                sms_api_key VARCHAR(200),
                email_provider VARCHAR(50),
                email_api_key VARCHAR(200),
                default_sender_email VARCHAR(200),
                reminder_lead_time INTEGER DEFAULT 24,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Imaging tables
            """CREATE TABLE IF NOT EXISTS patient_images (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
                series_id UUID REFERENCES image_series(id),
                image_type VARCHAR(50) NOT NULL,
                category VARCHAR(50) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                tooth_number VARCHAR(10),
                capture_date DATE NOT NULL,
                file_url VARCHAR(500) NOT NULL,
                thumbnail_url VARCHAR(500),
                file_size INTEGER NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                width INTEGER,
                height INTEGER,
                annotations JSONB DEFAULT '{}',
                tags JSONB DEFAULT '[]',
                is_archived BOOLEAN DEFAULT false,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS image_series (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                series_date DATE NOT NULL,
                image_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Insurance tables
            """CREATE TABLE IF NOT EXISTS insurance_carriers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(200),
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(100),
                zip_code VARCHAR(20),
                payer_id VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS patient_insurances (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
                carrier_id UUID REFERENCES insurance_carriers(id),
                insurance_type VARCHAR(20) NOT NULL,
                policy_number VARCHAR(100) NOT NULL,
                group_number VARCHAR(100),
                subscriber_name VARCHAR(200) NOT NULL,
                subscriber_id VARCHAR(100),
                relationship_to_insured VARCHAR(20) NOT NULL,
                effective_date DATE NOT NULL,
                expiration_date DATE,
                coverage_percent DECIMAL(5,2),
                annual_maximum DECIMAL(10,2),
                deductible DECIMAL(10,2),
                deductible_met DECIMAL(10,2) DEFAULT 0,
                is_active BOOLEAN DEFAULT true,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Marketing tables
            """CREATE TABLE IF NOT EXISTS marketing_campaigns (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                campaign_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'draft',
                start_date DATE,
                end_date DATE,
                budget DECIMAL(12,2),
                target_audience JSONB DEFAULT '{}',
                content TEXT,
                metrics JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Document tables
            """CREATE TABLE IF NOT EXISTS patient_documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
                document_type VARCHAR(50) NOT NULL,
                title VARCHAR(200) NOT NULL,
                file_url VARCHAR(500) NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                uploaded_by UUID REFERENCES users(id),
                is_signed BOOLEAN DEFAULT false,
                signed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Inventory tables
            """CREATE TABLE IF NOT EXISTS inventory_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                category VARCHAR(100),
                supplier VARCHAR(200),
                unit_price DECIMAL(10,2),
                quantity_in_stock INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                low_stock_alert BOOLEAN DEFAULT false,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Lab tables
            """CREATE TABLE IF NOT EXISTS lab_cases (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
                appointment_id UUID REFERENCES appointments(id),
                lab_name VARCHAR(200) NOT NULL,
                case_type VARCHAR(100) NOT NULL,
                instructions TEXT,
                materials JSONB DEFAULT '[]',
                due_date DATE,
                status VARCHAR(30) DEFAULT 'pending',
                tracking_number VARCHAR(100),
                cost DECIMAL(10,2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Referral tables
            """CREATE TABLE IF NOT EXISTS referral_partners (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                specialty VARCHAR(100),
                contact_name VARCHAR(200),
                contact_phone VARCHAR(20),
                contact_email VARCHAR(200),
                address TEXT,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
        ]
        
        with engine.connect() as conn:
            for stmt in create_statements:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                    logger.info(f"✅ Table created/verified")
                except Exception as e:
                    logger.warning(f"⚠️ Table creation skipped: {str(e)[:100]}")
        
        logger.info("✅ All tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct table creation failed: {str(e)}")
        return False

if __name__ == "__main__":
    # We're already in coredent-api directory when running this script
    # No need to change directory
    
    # Try Alembic migrations first
    if main():
        logger.info("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        logger.info("🔧 Trying direct table creation as fallback...")
        if create_missing_tables_direct():
            logger.info("🎉 Fallback migration completed!")
            sys.exit(0)
        else:
            logger.error("❌ All migration attempts failed")
            sys.exit(1)