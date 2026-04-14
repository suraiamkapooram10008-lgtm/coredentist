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
    # Check if table exists, if not create it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'password_reset_tokens' not in inspector.get_table_names():
        # Create the table if it doesn't exist
        op.create_table(
            'password_reset_tokens',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('token', sa.String(length=255), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('used', sa.Boolean(), nullable=True, default=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )
        op.create_index('idx_password_reset_token', 'password_reset_tokens', ['token'], unique=True)
        op.create_index('idx_password_reset_user_id', 'password_reset_tokens', ['user_id'], unique=False)
    
    # Add token_hash column to password_reset_tokens table
    op.add_column('password_reset_tokens', sa.Column('token_hash', sa.String(length=255), nullable=True))
    
    # Create index on token_hash for fast lookups
    op.create_index('idx_password_reset_token_hash', 'password_reset_tokens', ['token_hash'], unique=False)


def downgrade():
    # Drop index
    op.drop_index('idx_password_reset_token_hash', table_name='password_reset_tokens')
    
    # Drop column
    op.drop_column('password_reset_tokens', 'token_hash')
