"""add_performance_indexes

Revision ID: 20260407_1200
Revises: 20260407_1130
Create Date: 2026-04-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260407_1200'
down_revision = '20260407_1130'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add database indexes for frequently queried fields"""
    
    # User indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_practice_id', 'users', ['practice_id'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    
    # Patient indexes
    op.create_index('idx_patients_practice_id', 'patients', ['practice_id'])
    op.create_index('idx_patients_email', 'patients', ['email'])
    op.create_index('idx_patients_phone', 'patients', ['phone'])
    op.create_index('idx_patients_status', 'patients', ['status'])
    op.create_index('idx_patients_created_at', 'patients', ['created_at'])
    
    # Appointment indexes
    op.create_index('idx_appointments_practice_id', 'appointments', ['practice_id'])
    op.create_index('idx_appointments_patient_id', 'appointments', ['patient_id'])
    op.create_index('idx_appointments_provider_id', 'appointments', ['provider_id'])
    op.create_index('idx_appointments_status', 'appointments', ['status'])
    op.create_index('idx_appointments_start_time', 'appointments', ['start_time'])
    op.create_index('idx_appointments_date_status', 'appointments', ['start_time', 'status'])
    
    # Invoice indexes
    op.create_index('idx_invoices_practice_id', 'invoices', ['practice_id'])
    op.create_index('idx_invoices_patient_id', 'invoices', ['patient_id'])
    op.create_index('idx_invoices_status', 'invoices', ['status'])
    op.create_index('idx_invoices_invoice_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('idx_invoices_created_at', 'invoices', ['created_at'])
    op.create_index('idx_invoices_due_date', 'invoices', ['due_date'])
    
    # Payment indexes
    op.create_index('idx_payments_invoice_id', 'payments', ['invoice_id'])
    op.create_index('idx_payments_patient_id', 'payments', ['patient_id'])
    op.create_index('idx_payments_status', 'payments', ['status'])
    op.create_index('idx_payments_transaction_id', 'payments', ['transaction_id'], unique=True)
    op.create_index('idx_payments_created_at', 'payments', ['created_at'])
    
    # Insurance Claim indexes
    op.create_index('idx_insurance_claims_practice_id', 'insurance_claims', ['practice_id'])
    op.create_index('idx_insurance_claims_patient_id', 'insurance_claims', ['patient_id'])
    op.create_index('idx_insurance_claims_status', 'insurance_claims', ['status'])
    op.create_index('idx_insurance_claims_claim_number', 'insurance_claims', ['claim_number'], unique=True)
    
    # Treatment Plan indexes
    op.create_index('idx_treatment_plans_practice_id', 'treatment_plans', ['practice_id'])
    op.create_index('idx_treatment_plans_patient_id', 'treatment_plans', ['patient_id'])
    op.create_index('idx_treatment_plans_status', 'treatment_plans', ['status'])
    
    # Audit Log indexes (for HIPAA compliance queries)
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_user_action_date', 'audit_logs', ['user_id', 'action', 'created_at'])


def downgrade() -> None:
    """Remove performance indexes"""
    
    # User indexes
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_practice_id', table_name='users')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_is_active', table_name='users')
    
    # Patient indexes
    op.drop_index('idx_patients_practice_id', table_name='patients')
    op.drop_index('idx_patients_email', table_name='patients')
    op.drop_index('idx_patients_phone', table_name='patients')
    op.drop_index('idx_patients_status', table_name='patients')
    op.drop_index('idx_patients_created_at', table_name='patients')
    
    # Appointment indexes
    op.drop_index('idx_appointments_practice_id', table_name='appointments')
    op.drop_index('idx_appointments_patient_id', table_name='appointments')
    op.drop_index('idx_appointments_provider_id', table_name='appointments')
    op.drop_index('idx_appointments_status', table_name='appointments')
    op.drop_index('idx_appointments_start_time', table_name='appointments')
    op.drop_index('idx_appointments_date_status', table_name='appointments')
    
    # Invoice indexes
    op.drop_index('idx_invoices_practice_id', table_name='invoices')
    op.drop_index('idx_invoices_patient_id', table_name='invoices')
    op.drop_index('idx_invoices_status', table_name='invoices')
    op.drop_index('idx_invoices_invoice_number', table_name='invoices')
    op.drop_index('idx_invoices_created_at', table_name='invoices')
    op.drop_index('idx_invoices_due_date', table_name='invoices')
    
    # Payment indexes
    op.drop_index('idx_payments_invoice_id', table_name='payments')
    op.drop_index('idx_payments_patient_id', table_name='payments')
    op.drop_index('idx_payments_status', table_name='payments')
    op.drop_index('idx_payments_transaction_id', table_name='payments')
    op.drop_index('idx_payments_created_at', table_name='payments')
    
    # Insurance Claim indexes
    op.drop_index('idx_insurance_claims_practice_id', table_name='insurance_claims')
    op.drop_index('idx_insurance_claims_patient_id', table_name='insurance_claims')
    op.drop_index('idx_insurance_claims_status', table_name='insurance_claims')
    op.drop_index('idx_insurance_claims_claim_number', table_name='insurance_claims')
    
    # Treatment Plan indexes
    op.drop_index('idx_treatment_plans_practice_id', table_name='treatment_plans')
    op.drop_index('idx_treatment_plans_patient_id', table_name='treatment_plans')
    op.drop_index('idx_treatment_plans_status', table_name='treatment_plans')
    
    # Audit Log indexes
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_action_date', table_name='audit_logs')
