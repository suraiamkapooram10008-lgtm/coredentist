"""
Add MFA fields to users and consent fields to patients

Revision ID: 20260424_1430
Revises: 20260408_1830
Create Date: 2026-04-24 14:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260424_1430'
down_revision = '20260408_1830'
branch_labels = None
depends_on = None


def upgrade():
    # Add MFA fields to users table
    op.add_column('users', sa.Column('mfa_secret', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('mfa_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('mfa_backup_codes', sa.String(1000), nullable=True))
    
    # Add consent fields to patients table
    op.add_column('patients', sa.Column('consent_given', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('patients', sa.Column('consent_purpose', sa.String(255), nullable=True, server_default='Dental treatment and record keeping'))


def downgrade():
    # Remove MFA fields from users
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'mfa_verified')
    op.drop_column('users', 'mfa_backup_codes')
    
    # Remove consent fields from patients
    op.drop_column('patients', 'consent_given')
    op.drop_column('patients', 'consent_purpose')
