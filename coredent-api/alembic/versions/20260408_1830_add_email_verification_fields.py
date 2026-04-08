"""Add email verification fields

Revision ID: 20260408_1830
Revises: 20260408_1800
Create Date: 2026-04-08 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260408_1830'
down_revision = '20260408_1800'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email verification fields
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'is_email_verified')