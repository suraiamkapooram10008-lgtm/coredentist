#!/usr/bin/env python
"""Migration: Make entity_id nullable in audit_logs table

This allows logging of list/search actions where no specific entity is targeted.
"""

import asyncio
from sqlalchemy.schema import CreateTable, DropTable
from sqlalchemy import text

from app.core.database import engine, Base
from app.models.audit import AuditLog


async def upgrade():
    """Make entity_id nullable"""
    conn = await engine.connect()
    trans = await conn.begin()
    
    try:
        # SQLite doesn't support ALTER COLUMN to change NOT NULL
        # Need to recreate the table
        
        # Step 1: Create new table with nullable entity_id
        await conn.execute(text("""
            CREATE TABLE audit_logs_new (
                id UUID NOT NULL,
                user_id UUID,
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id UUID,
                changes JSON,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
        """))
        
        # Step 2: Copy all data
        await conn.execute(text("""
            INSERT INTO audit_logs_new 
            SELECT id, user_id, action, entity_type, entity_id, changes, ip_address, user_agent, created_at
            FROM audit_logs
        """))
        
        # Step 3: Drop old table
        await conn.execute(text("DROP TABLE audit_logs"))
        
        # Step 4: Rename new table
        await conn.execute(text("ALTER TABLE audit_logs_new RENAME TO audit_logs"))
        
        # Step 5: Create indexes
        await conn.execute(text("CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at)"))
        
        await trans.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        await trans.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()


async def downgrade():
    """Make entity_id NOT NULL again"""
    conn = await engine.connect()
    trans = await conn.begin()
    
    try:
        await conn.execute(text("""
            CREATE TABLE audit_logs_new (
                id UUID NOT NULL,
                user_id UUID,
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id UUID NOT NULL,
                changes JSON,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
        """))
        
        # Only copy rows where entity_id is NOT NULL
        await conn.execute(text("""
            INSERT INTO audit_logs_new 
            SELECT id, user_id, action, entity_type, entity_id, changes, ip_address, user_agent, created_at
            FROM audit_logs
            WHERE entity_id IS NOT NULL
        """))
        
        await conn.execute(text("DROP TABLE audit_logs"))
        await conn.execute(text("ALTER TABLE audit_logs_new RENAME TO audit_logs"))
        await conn.execute(text("CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at)"))
        
        await trans.commit()
        print("Downgrade completed successfully!")
        
    except Exception as e:
        await trans.rollback()
        print(f"Downgrade failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
