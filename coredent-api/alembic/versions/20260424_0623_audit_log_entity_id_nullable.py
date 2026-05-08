"""audit log entity_id nullable for list actions

Revision ID: 20260424_0623
Revises: 20260413_1410
Create Date: 2026-04-24 06:23:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = '20260424_0623'
down_revision = '20260413_1410'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support ALTER COLUMN to change NOT NULL
    # Recreate table with nullable entity_id
    op.execute("""
        CREATE TABLE audit_logs_new (
            id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36),
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(36),
            changes JSON,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
    """)
    
    op.execute("""
        INSERT INTO audit_logs_new 
        SELECT id, user_id, action, entity_type, entity_id, changes, ip_address, user_agent, created_at
        FROM audit_logs
    """)
    
    op.drop_table('audit_logs')
    op.execute('ALTER TABLE audit_logs_new RENAME TO audit_logs')
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade():
    op.execute("""
        CREATE TABLE audit_logs_new (
            id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36),
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(36) NOT NULL,
            changes JSON,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
    """)
    
    op.execute("""
        INSERT INTO audit_logs_new 
        SELECT id, user_id, action, entity_type, entity_id, changes, ip_address, user_agent, created_at
        FROM audit_logs
        WHERE entity_id IS NOT NULL
    """)
    
    op.drop_table('audit_logs')
    op.execute('ALTER TABLE audit_logs_new RENAME TO audit_logs')
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
