"""Add account lockout fields for brute force protection

Revision ID: 20260408_1800
Revises: 20260407_1730
Create Date: 2026-04-08 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260408_1800'
down_revision = '20260407_1730'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add account lockout fields for brute force protection
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_failed_login', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_failed_login')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')