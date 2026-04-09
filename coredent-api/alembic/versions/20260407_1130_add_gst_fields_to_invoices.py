"""Add GST fields to invoices table

Revision ID: 20260407_1130
Revises: 001_initial
Create Date: 2026-04-07 11:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260407_1130'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add GST fields to invoices table for Indian tax compliance"""
    # GST Identification Number
    op.add_column('invoices', sa.Column('gstin', sa.String(15), nullable=True))
    
    # GST Rate (default 18%)
    op.add_column('invoices', sa.Column('gst_rate', sa.Numeric(5, 2), server_default='18.00', nullable=False))
    
    # Central GST amount (CGST)
    op.add_column('invoices', sa.Column('cgst_amount', sa.Numeric(10, 2), server_default='0', nullable=False))
    
    # State GST amount (SGST)
    op.add_column('invoices', sa.Column('sgst_amount', sa.Numeric(10, 2), server_default='0', nullable=False))
    
    # Integrated GST amount (IGST)
    op.add_column('invoices', sa.Column('igst_amount', sa.Numeric(10, 2), server_default='0', nullable=False))
    
    # Inter-state flag
    op.add_column('invoices', sa.Column('is_inter_state', sa.String(1), server_default='N', nullable=False))


def downgrade() -> None:
    """Remove GST fields from invoices table"""
    op.drop_column('invoices', 'is_inter_state')
    op.drop_column('invoices', 'igst_amount')
    op.drop_column('invoices', 'sgst_amount')
    op.drop_column('invoices', 'cgst_amount')
    op.drop_column('invoices', 'gst_rate')
    op.drop_column('invoices', 'gstin')