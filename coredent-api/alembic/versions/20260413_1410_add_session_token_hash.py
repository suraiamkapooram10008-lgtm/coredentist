"""add session token hash

Revision ID: 20260413_1410
Revises: 20260413_1400
Create Date: 2026-04-13 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260413_1410'
down_revision = '20260413_1400'
branch_labels = None
depends_on = None


def upgrade():
    # Add token_hash column to sessions table
    op.add_column('sessions', sa.Column('token_hash', sa.String(length=255), nullable=True))
    
    # Create index on token_hash for fast lookups
    op.create_index('idx_session_token_hash', 'sessions', ['token_hash'], unique=False)


def downgrade():
    # Drop index
    op.drop_index('idx_session_token_hash', table_name='sessions')
    
    # Drop column
    op.drop_column('sessions', 'token_hash')
