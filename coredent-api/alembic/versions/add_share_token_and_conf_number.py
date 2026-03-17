"""Add share_token to images and confirmation_number to claims

Revision ID: add_share_token_and_conf_number
Revises: 
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_share_token_and_conf_number'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add share_token column to patient_images
    op.add_column('patient_images', sa.Column('share_token', sa.String(255), nullable=True))
    
    # Add confirmation_number column to insurance_claims
    op.add_column('insurance_claims', sa.Column('confirmation_number', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('insurance_claims', 'confirmation_number')
    op.drop_column('patient_images', 'share_token')
