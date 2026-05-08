"""
Tests for SubscriptionService
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.subscription_service import SubscriptionService
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionInterval
from app.models.practice import Practice
from app.models.user import User


class TestSubscriptionService:
    """Test suite for SubscriptionService"""

    @pytest.fixture
    async def subscription_service(self, db_session: AsyncSession):
        """Create subscription service instance"""
        return SubscriptionService(db_session)

    @pytest.fixture
    async def test_plan(self, db_session: AsyncSession):
        """Create a test subscription plan"""
        plan = SubscriptionPlan(
            id=uuid4(),
            name="Professional Plan",
            description="Professional features",
            amount=Decimal("99.00"),
            interval=SubscriptionInterval.MONTHLY,
            features={"users": 10, "storage": "100GB"},
            is_active=True
        )
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        return plan

    @pytest.mark.asyncio
    async def test_calculate_period_start_end_monthly(
        self,
        subscription_service: SubscriptionService
    ):
        """Test calculating billing period for monthly subscription"""
        start_date = datetime(2026, 1, 15)
        
        period_start, period_end = subscription_service.calculate_period_start_end(
            start_date=start_date,
            billing_cycle=SubscriptionInterval.MONTHLY
        )

        assert period_start == start_date
        assert period_end.month == 2  # Next month
        assert period_end.day == 15

    @pytest.mark.asyncio
    async def test_calculate_period_start_end_yearly(
        self,
        subscription_service: SubscriptionService
    ):
        """Test calculating billing period for yearly subscription"""
        start_date = datetime(2026, 1, 15)
        
        period_start, period_end = subscription_service.calculate_period_start_end(
            start_date=start_date,
            billing_cycle=SubscriptionInterval.YEARLY
        )

        assert period_start == start_date
        assert period_end.year == 2027  # Next year
        assert period_end.month == 1
        assert period_end.day == 15

    @pytest.mark.asyncio
    async def test_calculate_proration_amount(
        self,
        subscription_service: SubscriptionService
    ):
        """Test calculating prorated amount for plan change"""
        old_price = Decimal("99.00")
        new_price = Decimal("199.00")
        days_remaining = 15
        total_days = 30

        prorated_amount = subscription_service.calculate_proration_amount(
            old_price=old_price,
            new_price=new_price,
            days_remaining=days_remaining,
            total_days=total_days
        )

        # Should charge difference for remaining days
        assert prorated_amount > 0
        assert prorated_amount < new_price - old_price

    @pytest.mark.asyncio
    @patch('stripe.Subscription.create')
    async def test_create_stripe_subscription_success(
        self,
        mock_stripe_create,
        subscription_service: SubscriptionService,
        test_practice: Practice,
        test_plan: SubscriptionPlan
    ):
        """Test successful Stripe subscription creation"""
        # Mock Stripe response
        mock_stripe_create.return_value = Mock(
            id="sub_test_123",
            status="active",
            current_period_start=int(datetime.now().timestamp()),
            current_period_end=int((datetime.now() + timedelta(days=30)).timestamp()),
            customer="cus_test_123"
        )

        subscription = await subscription_service.create_stripe_subscription(
            practice_id=test_practice.id,
            plan_id=test_plan.id,
            stripe_customer_id="cus_test_123",
            stripe_price_id="price_test_123"
        )

        assert subscription is not None
        assert subscription.stripe_subscription_id == "sub_test_123"
        assert subscription.status == "active"
        assert subscription.practice_id == test_practice.id
        assert subscription.plan_id == test_plan.id

    @pytest.mark.asyncio
    async def test_get_subscription_with_plan(
        self,
        subscription_service: SubscriptionService,
        test_practice: Practice,
        test_plan: SubscriptionPlan,
        db_session: AsyncSession
    ):
        """Test getting subscription with plan details"""
        # Create subscription
        subscription = Subscription(
            id=uuid4(),
            practice_id=test_practice.id,
            plan_id=test_plan.id,
            status="active",
            interval=SubscriptionInterval.MONTHLY,
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30),
            stripe_subscription_id="sub_test_123",
            stripe_customer_id="cus_test_123"
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        # Get subscription with plan
        result = await subscription_service.get_subscription_with_plan(
            subscription_id=subscription.id
        )

        assert result is not None
        assert result.id == subscription.id
        assert result.plan_id == test_plan.id

    @pytest.mark.asyncio
    @patch('stripe.Subscription.modify')
    @patch('stripe.Subscription.retrieve')
    async def test_change_plan_success(
        self,
        mock_stripe_retrieve,
        mock_stripe_modify,
        subscription_service: SubscriptionService,
        test_practice: Practice,
        test_plan: SubscriptionPlan,
        db_session: AsyncSession
    ):
        """Test successful plan change"""
        # Create current subscription
        subscription = Subscription(
            id=uuid4(),
            practice_id=test_practice.id,
            plan_id=test_plan.id,
            status="active",
            interval=SubscriptionInterval.MONTHLY,
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30),
            stripe_subscription_id="sub_test_123",
            stripe_customer_id="cus_test_123"
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        # Create new plan
        new_plan = SubscriptionPlan(
            id=uuid4(),
            name="Enterprise Plan",
            description="Enterprise features",
            amount=Decimal("199.00"),
            interval=SubscriptionInterval.MONTHLY,
            features={"users": 50, "storage": "500GB"},
            is_active=True
        )
        db_session.add(new_plan)
        await db_session.commit()
        await db_session.refresh(new_plan)

        # Mock Stripe response
        mock_stripe_retrieve.return_value = {
            "items": {"data": [{"id": "si_test_123"}]}
        }
        mock_stripe_modify.return_value = Mock(
            id="sub_test_123",
            status="active",
            current_period_start=int(datetime.now().timestamp()),
            current_period_end=int((datetime.now() + timedelta(days=30)).timestamp())
        )

        # Change plan
        updated = await subscription_service.change_plan(
            subscription_id=subscription.id,
            new_plan_id=new_plan.id,
            stripe_price_id="price_new_123"
        )

        assert updated is not None
        assert updated.plan_id == new_plan.id

    @pytest.mark.asyncio
    async def test_record_usage(
        self,
        subscription_service: SubscriptionService,
        test_practice: Practice,
        test_plan: SubscriptionPlan,
        db_session: AsyncSession
    ):
        """Test recording usage for metered billing"""
        # Create subscription
        subscription = Subscription(
            id=uuid4(),
            practice_id=test_practice.id,
            plan_id=test_plan.id,
            status="active",
            interval=SubscriptionInterval.MONTHLY,
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30),
            stripe_subscription_id="sub_test_123",
            stripe_customer_id="cus_test_123"
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        # Record usage
        usage = await subscription_service.record_usage(
            subscription_id=subscription.id,
            metric_name="api_calls",
            quantity=100
        )

        assert usage is not None
        assert usage.subscription_id == subscription.id
        assert usage.metric_name == "api_calls"
        assert usage.quantity == 100

    @pytest.mark.asyncio
    async def test_get_usage_records(
        self,
        subscription_service: SubscriptionService,
        test_practice: Practice,
        test_plan: SubscriptionPlan,
        db_session: AsyncSession
    ):
        """Test getting usage records for a subscription"""
        # Create subscription
        subscription = Subscription(
            id=uuid4(),
            practice_id=test_practice.id,
            plan_id=test_plan.id,
            status="active",
            interval=SubscriptionInterval.MONTHLY,
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30),
            stripe_subscription_id="sub_test_123",
            stripe_customer_id="cus_test_123"
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        # Record some usage
        await subscription_service.record_usage(
            subscription_id=subscription.id,
            metric_name="api_calls",
            quantity=100
        )
        await subscription_service.record_usage(
            subscription_id=subscription.id,
            metric_name="storage",
            quantity=50
        )

        # Get usage records
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        records = await subscription_service.get_usage_records(
            subscription_id=subscription.id,
            start_date=start_date,
            end_date=end_date
        )

        assert records is not None
        assert len(records) >= 2

    @pytest.mark.asyncio
    @patch('stripe.Subscription.modify')
    async def test_cancel_stripe_subscription(
        self,
        mock_stripe_modify,
        subscription_service: SubscriptionService,
        test_practice: Practice,
        test_plan: SubscriptionPlan,
        db_session: AsyncSession
    ):
        """Test canceling a Stripe subscription"""
        # Create subscription
        subscription = Subscription(
            id=uuid4(),
            practice_id=test_practice.id,
            plan_id=test_plan.id,
            status="active",
            interval=SubscriptionInterval.MONTHLY,
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30),
            stripe_subscription_id="sub_test_123",
            stripe_customer_id="cus_test_123"
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        # Mock Stripe response
        mock_stripe_modify.return_value = Mock(
            id="sub_test_123",
            status="canceled",
            cancel_at_period_end=True
        )

        # Cancel subscription
        cancelled = await subscription_service.cancel_stripe_subscription(
            subscription_id=subscription.id,
            cancel_at_period_end=True
        )

        assert cancelled is True

    @pytest.mark.asyncio
    async def test_subscription_payment_failed(
        self,
        subscription_service: SubscriptionService,
        test_practice: Practice,
        test_plan: SubscriptionPlan,
        db_session: AsyncSession
    ):
        """Test handling subscription payment failure"""
        # Create subscription
        subscription = Subscription(
            id=uuid4(),
            practice_id=test_practice.id,
            plan_id=test_plan.id,
            status="active",
            interval=SubscriptionInterval.MONTHLY,
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30),
            stripe_subscription_id="sub_test_123",
            stripe_customer_id="cus_test_123"
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        # Simulate payment failure by updating status
        subscription.status = "past_due"
        await db_session.commit()
        await db_session.refresh(subscription)

        assert subscription.status == "past_due"

    @pytest.mark.asyncio
    async def test_calculate_proration_zero_days(
        self,
        subscription_service: SubscriptionService
    ):
        """Test proration calculation with zero days remaining"""
        old_price = Decimal("99.00")
        new_price = Decimal("199.00")
        days_remaining = 0
        total_days = 30

        prorated_amount = subscription_service.calculate_proration_amount(
            old_price=old_price,
            new_price=new_price,
            days_remaining=days_remaining,
            total_days=total_days
        )

        # Should be zero if no days remaining
        assert prorated_amount == 0
