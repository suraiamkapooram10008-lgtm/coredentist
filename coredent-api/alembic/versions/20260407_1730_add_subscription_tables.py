"""add subscription tables

Revision ID: 20260407_1730
Revises: 20260407_1200
Create Date: 2026-04-07 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260407_1730'
down_revision = '20260407_1200'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('practice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('practices.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(100), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('interval', sa.Enum('WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMI_ANNUAL', 'ANNUAL', name='subscriptioninterval'), nullable=False),
        sa.Column('trial_period_days', sa.Integer(), server_default='0'),
        sa.Column('features', postgresql.JSON(), nullable=True),
        sa.Column('limits', postgresql.JSON(), nullable=True),
        sa.Column('stripe_price_id', sa.String(255), nullable=True),
        sa.Column('stripe_product_id', sa.String(255), nullable=True),
        sa.Column('razorpay_plan_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_recommended', sa.Boolean(), server_default='false'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('is_usage_based', sa.Boolean(), server_default='false'),
        sa.Column('usage_meter_name', sa.String(255), nullable=True),
        sa.Column('usage_unit_label', sa.String(50), nullable=True),
        sa.Column('included_usage', sa.Numeric(10, 2), server_default='0'),
        sa.Column('overage_rate', sa.Numeric(10, 4), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_plan_practice_active', 'subscription_plans', ['practice_id', 'is_active'])
    op.create_index('idx_plan_stripe_id', 'subscription_plans', ['stripe_price_id'])

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('practice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('practices.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscription_plans.id'), nullable=False),
        sa.Column('payment_card_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_cards.id'), nullable=True),
        sa.Column('status', sa.Enum('TRIALING', 'ACTIVE', 'PAST_DUE', 'CANCELED', 'PAUSED', 'EXPIRED', 'INCOMPLETE', 'UNPAID', name='subscriptionstatus'), server_default='incomplete'),
        sa.Column('interval', sa.Enum('WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMI_ANNUAL', 'ANNUAL', name='subscriptioninterval2'), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_day', sa.Integer(), server_default='1'),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_used', sa.Boolean(), server_default='false'),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default='false'),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('cancellation_feedback', sa.String(255), nullable=True),
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paused_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('proration_behavior', sa.Enum('CREATE_PRORATIONS', 'ALWAYS_INVOICE', 'NONE', name='prorationbehavior'), server_default='create_prorations'),
        sa.Column('proration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('latest_invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('dunning_retry_count', sa.Integer(), server_default='0'),
        sa.Column('dunning_max_retries', sa.Integer(), server_default='4'),
        sa.Column('last_payment_error', sa.Text(), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_usage', sa.Numeric(10, 2), server_default='0'),
        sa.Column('current_overage', sa.Numeric(10, 2), server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_sub_practice_status', 'subscriptions', ['practice_id', 'status'])
    op.create_index('idx_sub_patient_status', 'subscriptions', ['patient_id', 'status'])
    op.create_index('idx_sub_stripe_id', 'subscriptions', ['stripe_subscription_id'])
    op.create_index('idx_sub_next_billing', 'subscriptions', ['next_billing_date'])

    # Create usage_meters table
    op.create_table(
        'usage_meters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscription_plans.id'), nullable=False),
        sa.Column('meter_name', sa.String(255), nullable=False),
        sa.Column('unit_label', sa.String(50), nullable=False),
        sa.Column('aggregation', sa.String(50), server_default='sum'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create usage_records table
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('meter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usage_meters.id'), nullable=True),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
    )
    op.create_index('idx_usage_sub_period', 'usage_records', ['subscription_id', 'subscription_id'])

    # Create dunning_events table
    op.create_table(
        'dunning_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('action', sa.Enum('RETRY_PAYMENT', 'SEND_EMAIL', 'SUSPEND_SUBSCRIPTION', 'CANCEL_SUBSCRIPTION', name='dunningaction'), nullable=False),
        sa.Column('result', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create cancellation_surveys table
    op.create_table(
        'cancellation_surveys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('reason_code', sa.String(50), nullable=False),
        sa.Column('additional_feedback', sa.Text(), nullable=True),
        sa.Column('likelihood_to_return', sa.Integer(), nullable=True),
        sa.Column('used_trial', sa.Boolean(), server_default='false'),
        sa.Column('sub_duration_days', sa.Integer(), nullable=True),
        sa.Column('total_amount_paid', sa.Numeric(10, 2), server_default='0'),
        sa.Column('save_offer_type', sa.String(50), nullable=True),
        sa.Column('save_offer_accepted', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('cancellation_surveys')
    op.drop_table('dunning_events')
    op.drop_index('idx_usage_sub_period', 'usage_records')
    op.drop_table('usage_records')
    op.drop_table('usage_meters')
    op.drop_index('idx_sub_next_billing', 'subscriptions')
    op.drop_index('idx_sub_stripe_id', 'subscriptions')
    op.drop_index('idx_sub_patient_status', 'subscriptions')
    op.drop_index('idx_sub_practice_status', 'subscriptions')
    op.drop_table('subscriptions')
    op.drop_index('idx_plan_stripe_id', 'subscription_plans')
    op.drop_index('idx_plan_practice_active', 'subscription_plans')
    op.drop_table('subscription_plans')
    op.execute('DROP TYPE IF EXISTS subscriptioninterval')
    op.execute('DROP TYPE IF EXISTS subscriptioninterval2')
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
    op.execute('DROP TYPE IF EXISTS prorationbehavior')
    op.execute('DROP TYPE IF EXISTS dunningaction')