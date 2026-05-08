"""convert invoice properties to columns

Revision ID: 20260505_1500
Revises: 20260505_1400
Create Date: 2026-05-05 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260505_1500'
down_revision = '20260505_1400'
branch_labels = None
depends_on = None


def upgrade():
    # Add amount_paid and balance_due columns to invoices table
    op.add_column('invoices', sa.Column('amount_paid', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'))
    op.add_column('invoices', sa.Column('balance_due', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'))
    
    # Update balance_due to equal total for existing invoices
    op.execute("UPDATE invoices SET balance_due = total WHERE balance_due = 0")


def downgrade():
    # Remove the columns
    op.drop_column('invoices', 'balance_due')
    op.drop_column('invoices', 'amount_paid')
