"""add audit log partitioning

Revision ID: 20260430_1200
Revises: 20260424_1430
Create Date: 2026-04-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta


# revision identifiers, used by Alembic.
revision = '20260430_1200'
down_revision = '20260424_1430'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Convert audit_logs to partitioned table by month
    This improves query performance and enables efficient archival
    """
    
    # Note: This migration requires PostgreSQL 10+
    # For production, run this during maintenance window
    
    # Create new partitioned table
    op.execute("""
        -- Rename existing table
        ALTER TABLE audit_logs RENAME TO audit_logs_old;
        
        -- Create partitioned table
        CREATE TABLE audit_logs (
            id UUID DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id UUID NOT NULL,
            changes JSONB,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at);
        
        -- Create indexes on partitioned table
        CREATE INDEX idx_audit_user_partitioned ON audit_logs(user_id, created_at);
        CREATE INDEX idx_audit_timestamp_partitioned ON audit_logs(created_at);
        CREATE INDEX idx_audit_entity_partitioned ON audit_logs(entity_type, entity_id, created_at);
    """)
    
    # Create partitions for current and next 6 months
    current_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    for i in range(7):
        partition_date = current_date + timedelta(days=32 * i)
        partition_date = partition_date.replace(day=1)
        next_month = (partition_date + timedelta(days=32)).replace(day=1)
        
        partition_name = f"audit_logs_{partition_date.strftime('%Y_%m')}"
        
        op.execute(f"""
            CREATE TABLE {partition_name} PARTITION OF audit_logs
            FOR VALUES FROM ('{partition_date.isoformat()}') TO ('{next_month.isoformat()}');
        """)
    
    # Copy data from old table to new partitioned table
    op.execute("""
        INSERT INTO audit_logs 
        SELECT * FROM audit_logs_old;
    """)
    
    # Drop old table
    op.execute("DROP TABLE audit_logs_old;")


def downgrade() -> None:
    """
    Revert to non-partitioned table
    """
    
    # Create non-partitioned table
    op.execute("""
        -- Rename partitioned table
        ALTER TABLE audit_logs RENAME TO audit_logs_partitioned;
        
        -- Create non-partitioned table
        CREATE TABLE audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id UUID NOT NULL,
            changes JSONB,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes
        CREATE INDEX idx_audit_user ON audit_logs(user_id);
        CREATE INDEX idx_audit_timestamp ON audit_logs(created_at);
        CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
        
        -- Copy data back
        INSERT INTO audit_logs 
        SELECT id, user_id, action, entity_type, entity_id, changes, ip_address, user_agent, created_at
        FROM audit_logs_partitioned;
        
        -- Drop partitioned table (will drop all partitions)
        DROP TABLE audit_logs_partitioned CASCADE;
    """)
