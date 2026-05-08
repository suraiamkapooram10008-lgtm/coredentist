"""add payment fields for billing

Revision ID: 20260505_1400
Revises: 20260430_1200
Create Date: 2026-05-05 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260505_1400'
down_revision = '20260430_1200'
branch_labels = None
depends_on = None


def upgrade():
    """Add new fields to payments table for enhanced billing functionality"""
    
    # Add new columns to payments table
    op.add_column('payments', sa.Column('payment_number', sa.String(length=50), nullable=True))
    op.add_column('payments', sa.Column('payment_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('payments', sa.Column('reference_number', sa.String(length=255), nullable=True))
    op.add_column('payments', sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('payments', sa.Column('refunded_amount', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('payments', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    
    # Create unique constraint on payment_number
    op.create_unique_constraint('uq_payments_payment_number', 'payments', ['payment_number'])
    
    # Backfill payment_number for existing records
    op.execute("""
        UPDATE payments 
        SET payment_number = 'PAY-LEGACY-' || LPAD(CAST(ROW_NUMBER() OVER (ORDER BY created_at) AS TEXT), 6, '0')
        WHERE payment_number IS NULL
    """)
    
    # Backfill payment_date from created_at for existing records
    op.execute("""
        UPDATE payments 
        SET payment_date = created_at
        WHERE payment_date IS NULL
    """)


def downgrade():
    """Remove payment fields"""
    
    # Drop unique constraint
    op.drop_constraint('uq_payments_payment_number', 'payments', type_='unique')
    
    # Drop columns
    op.drop_column('payments', 'updated_at')
    op.drop_column('payments', 'refunded_amount')
    op.drop_column('payments', 'refunded_at')
    op.drop_column('payments', 'reference_number')
    op.drop_column('payments', 'payment_date')
    op.drop_column('payments', 'payment_number')
