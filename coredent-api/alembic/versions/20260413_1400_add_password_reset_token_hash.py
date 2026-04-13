"""add password reset token hash

Revision ID: 20260413_1400
Revises: 20260408_1830
Create Date: 2026-04-13 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260413_1400'
down_revision = '20260408_1830'
branch_labels = None
depends_on = None


def upgrade():
    # Add token_hash column to password_reset_tokens table
    op.add_column('password_reset_tokens', sa.Column('token_hash', sa.String(length=255), nullable=True))
    
    # Create index on token_hash for fast lookups
    op.create_index('idx_password_reset_token_hash', 'password_reset_tokens', ['token_hash'], unique=False)


def downgrade():
    # Drop index
    op.drop_index('idx_password_reset_token_hash', table_name='password_reset_tokens')
    
    # Drop column
    op.drop_column('password_reset_tokens', 'token_hash')
