"""
Test configuration and fixtures for CoreDent API tests
Optimized for performance with shared database and proper cleanup
"""
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

# Set required env vars BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-chars-long"
os.environ["ENCRYPTION_KEY"] = "GjdYWzriVw8SYTY3eYIwb1ZO8qvL7nYGAXf6aekvR7E="
os.environ["DEBUG"] = "True"
os.environ["ENVIRONMENT"] = "test"
os.environ["REDIS_URL"] = ""  # Disable Redis for tests
os.environ["SMTP_HOST"] = ""  # Disable email for tests
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_S3_BUCKET"] = "test-bucket"
os.environ["STRIPE_API_KEY"] = "sk_test_123"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_secret"
os.environ["RAZORPAY_KEY_ID"] = "rzp_test_123"
os.environ["RAZORPAY_KEY_SECRET"] = "test_secret"
os.environ["RAZORPAY_WEBHOOK_SECRET"] = "test_webhook_secret"

import pytest
import pytest_asyncio
import datetime
import uuid
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import configure_mappers

# Import all models to register them with SQLAlchemy
import app.models
import app.models.password_reset
import app.models.subscription
from app.core.base import Base
from app.core.security import get_password_hash

# Disable rate limiting for tests
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core import limiter as limiter_module
limiter_module.limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/minute"],
    enabled=False
)

from app.models.practice import Practice
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.appointment import Appointment

# Configure mappers AFTER all models are imported
configure_mappers()

# Create async test engine - in-memory SQLite for speed
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async session factory
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, autocommit=False, autoflush=False, expire_on_commit=False
)

# Import app and override get_db AFTER engines are configured
from app.main import app as fastapi_app
from app.core.database import get_db


import atexit

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create database tables once per test session"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Register engine disposal via atexit to avoid async generator finalizer issues
    def _dispose_engine():
        try:
            loop = _asyncio.new_event_loop()
            _asyncio.set_event_loop(loop)
            loop.run_until_complete(engine.dispose())
            loop.close()
        except Exception:
            pass
    atexit.register(_dispose_engine)
    return True


import asyncio as _asyncio

@pytest_asyncio.fixture(scope="function")
def event_loop():
    """Override pytest-asyncio event_loop to not close before fixture finalizers run"""
    loop = _asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    # Loop closure deferred to allow fixture finalizers

@pytest.fixture(scope="function")
def db_session(request):
    """Create database session for testing - uses transaction rollback for speed"""
    loop = _asyncio.new_event_loop()
    _asyncio.set_event_loop(loop)
    session_maker = TestingSessionLocal()
    session = loop.run_until_complete(session_maker.__aenter__())

    def cleanup():
        cleanup_loop = _asyncio.new_event_loop()
        _asyncio.set_event_loop(cleanup_loop)
        try:
            cleanup_loop.run_until_complete(session.rollback())
            cleanup_loop.run_until_complete(session_maker.__aexit__(None, None, None))
        finally:
            cleanup_loop.close()

    request.addfinalizer(cleanup)
    return session


@pytest.fixture(scope="function")
def db(db_session):
    return db_session.sync_session


@pytest_asyncio.fixture(scope="function")
async def client(db_session) -> AsyncClient:
    """Create async test client with redirect following"""
    # Override get_db to use the same session
    async def override_get_db_override():
        yield db_session
    
    fastapi_app.dependency_overrides[get_db] = override_get_db_override
    
    async with AsyncClient(app=fastapi_app, base_url="http://test", follow_redirects=True) as ac:
        yield ac
    
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user):
    """Get authentication headers for test user"""
    login_data = {
        "email": test_user.email,
        "password": "secret"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_practice(db_session):
    """Create test practice"""
    practice = Practice(
        name="Test Practice",
        email="test@practice.com",
        phone="555-0100",
        address_street="123 Test St",
        address_city="Testville",
        address_state="TS",
        address_zip="12345",
    )
    db_session.add(practice)
    await db_session.commit()
    await db_session.refresh(practice)
    return practice


@pytest_asyncio.fixture
async def test_user(db_session, test_practice):
    """Create test user with unique email"""
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        password_hash=get_password_hash("secret"),
        first_name="Test",
        last_name="User",
        role=UserRole.OWNER,
        practice_id=test_practice.id,
        is_active=True,
        is_email_verified=True,
        mfa_enabled=True,
        mfa_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_provider(test_user):
    return test_user


@pytest_asyncio.fixture
async def test_patient(db_session, test_practice):
    """Create test patient"""
    patient = Patient(
        practice_id=test_practice.id,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        date_of_birth=datetime.date(1990, 1, 1),
        gender="male",
        address_street="123 Main St",
        address_city="Springfield",
        address_state="IL",
        address_zip="62701",
        emergency_contact={
            "name": "Jane Doe",
            "relationship": "spouse",
            "phone": "+1234567891"
        },
        medical_alerts=[],
        status="active",
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest_asyncio.fixture
async def test_appointment(db_session, test_practice, test_patient, test_user):
    """Create test appointment"""
    appointment = Appointment(
        practice_id=test_practice.id,
        patient_id=test_patient.id,
        provider_id=test_user.id,
        appointment_type="cleaning",
        status="scheduled",
        start_time=datetime.datetime(2026, 3, 17, 10, 0, 0),
        end_time=datetime.datetime(2026, 3, 17, 11, 0, 0),
        duration=60,
        notes="Regular cleaning appointment",
    )
    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)
    return appointment


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return {
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "ENVIRONMENT": "test",
    }


@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock all external service calls to prevent network delays"""
    with patch('app.core.email.EmailService.send_email', new_callable=AsyncMock) as mock_email:
        # Configure mock return values
        mock_email.return_value = {"status": "sent", "message_id": "test123"}
        
        yield {
            'email': mock_email,
        }


@pytest.fixture(autouse=True)
def mock_stripe():
    """Mock Stripe API calls"""
    try:
        with patch('stripe.Customer.create') as mock_customer, \
             patch('stripe.Subscription.create') as mock_subscription, \
             patch('stripe.PaymentIntent.create') as mock_payment:
            
            mock_customer.return_value = MagicMock(id="cus_test123")
            mock_subscription.return_value = MagicMock(id="sub_test123", status="active")
            mock_payment.return_value = MagicMock(id="pi_test123", status="succeeded")
            
            yield {
                'customer': mock_customer,
                'subscription': mock_subscription,
                'payment': mock_payment,
            }
    except ImportError:
        # Stripe not installed, skip mocking
        yield {}


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, db_session, test_practice):
    """Get authentication token for admin user"""
    # Create admin user
    unique_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    admin_user = User(
        email=unique_email,
        password_hash=get_password_hash("secret"),
        first_name="Admin",
        last_name="User",
        role="admin",
        practice_id=test_practice.id,
        is_active=True,
        is_email_verified=True,
        mfa_enabled=True,
        mfa_verified=True,
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    
    # Login and get token
    login_data = {
        "email": admin_user.email,
        "password": "secret"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def test_plan_id(db_session, test_practice):
    """Create test subscription plan and return its ID"""
    try:
        from app.models.subscription import SubscriptionPlan, SubscriptionInterval
        from decimal import Decimal
        
        plan = SubscriptionPlan(
            practice_id=test_practice.id,
            name="Test Plan",
            description="Test subscription plan",
            amount=Decimal("99.99"),
            interval=SubscriptionInterval.MONTHLY,
            features=["feature1", "feature2"],
            is_active=True,
        )
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        return plan.id
    except ImportError:
        # SubscriptionPlan model not available
        return uuid.uuid4()


@pytest_asyncio.fixture
async def test_subscription_id(db_session, test_practice, test_plan_id):
    """Create test subscription and return its ID"""
    try:
        from app.models.subscription import Subscription
        from decimal import Decimal
        
        subscription = Subscription(
            practice_id=test_practice.id,
            plan_id=test_plan_id,
            status="active",
            interval="monthly",
            current_period_start=datetime.datetime.now(),
            current_period_end=datetime.datetime.now() + datetime.timedelta(days=30),
            stripe_subscription_id="sub_test123",
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        return subscription.id
    except ImportError:
        # Subscription model not available
        return uuid.uuid4()
