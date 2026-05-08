"""add webhook_events table

Revision ID: 20260506_0001
Revises: 20260505_1500
Create Date: 2026-05-06 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260506_0001'
down_revision = '20260505_1500'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create webhook_events table for idempotent webhook processing
    op.create_table(
        'webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('provider', sa.String(50), nullable=False, index=True),
        sa.Column('event_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('payload_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('idx_webhook_provider_event', 'webhook_events', ['provider', 'event_id'])
    op.create_index('idx_webhook_processed', 'webhook_events', ['processed', 'created_at'])


def downgrade() -> None:
    op.drop_table('webhook_events')