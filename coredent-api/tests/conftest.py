"""
Test configuration and fixtures for CoreDent API tests
"""
import os
import sys
from cryptography.fernet import Fernet

# Generate valid Fernet key for testing
test_encryption_key = Fernet.generate_key().decode()

# Set required env vars BEFORE importing app (must use direct assignment, not setdefault)
test_database_url = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["DATABASE_URL"] = test_database_url
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-12345"
os.environ["ENCRYPTION_KEY"] = test_encryption_key
os.environ["DEBUG"] = "True"
os.environ["ENVIRONMENT"] = "test"

import pytest
import asyncio
import datetime
import uuid as uuid_lib
from typing import AsyncGenerator, Generator
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import configure_mappers

# Import all models to ensure they're registered with SQLAlchemy
from app.core.database import Base
from app.core.config_simple import settings
from app.core.security import get_password_hash
from app.main import app as fastapi_app
from app.api.deps import get_db, verify_csrf, verify_csrf_no_auth

# Import all models to register them with SQLAlchemy
import app.models
from app.models.practice import Practice, PracticeGroup
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.referral import Referral, ReferralSource1

# Configure all mappers before creating tables
configure_mappers()

# Test database URL (async SQLite)
SQLALCHEMY_DATABASE_URL = test_database_url

# Create async test engine. StaticPool keeps a single in-memory SQLite
# database alive across fixture connections; PostgreSQL uses its normal pool.
_engine_options = {"echo": False}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    _engine_options.update(
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, **_engine_options)

TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(name="engine")
def engine_fixture():
    """Expose the shared async test engine to tests that inspect raw storage."""
    return engine


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for testing"""
    async with TestingSessionLocal() as session:
        yield session


fastapi_app.dependency_overrides[get_db] = override_get_db


# Bypass CSRF verification in tests. The httpx AsyncClient does not manage
# CSRF cookies, and the production CSRF flow is covered by dedicated tests
# in test_security.py. Production behavior is unchanged.
async def _bypass_csrf() -> bool:
    return True


fastapi_app.dependency_overrides[verify_csrf] = _bypass_csrf
fastapi_app.dependency_overrides[verify_csrf_no_auth] = _bypass_csrf


# Disable slowapi rate limiting in tests. Each test fixture performs a
# login, and @limiter.limit("5/minute") on /auth/login otherwise rejects
# the 6th login in the suite with HTTP 429 (surfacing as 401 downstream).
# Production limits are unaffected.
from app.core.limiter import limiter as _limiter

_limiter.enabled = False


@pytest.fixture(scope="function")
async def setup_database():
    """Create database tables before tests"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Don't drop tables - just truncate for speed
    async with TestingSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()  # Rollback any uncommitted changes


@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client.

    follow_redirects=True so tests can exercise routes defined at /path/
    with a trailing slash by requesting /path (FastAPI otherwise returns
    307 and httpx doesn't follow redirects by default).
    """
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as ac:
        yield ac


# Alias: several older test modules use the name `async_client` for the
# httpx AsyncClient fixture. Keep both names to avoid churn.
@pytest.fixture
async def async_client(client: AsyncClient) -> AsyncClient:
    return client


@pytest.fixture
async def test_practice(db_session: AsyncSession) -> Practice:
    """Create test practice"""
    practice = Practice(
        id=uuid_lib.uuid4(),
        name="Test Practice",
        email="test@practice.com",
        phone="555-0100",
        address_street="123 Test St",
        address_city="Testville",
        address_state="TS",
        address_zip="12345",
    )
    db_session.add(practice)
    await db_session.flush()
    await db_session.refresh(practice)
    return practice


@pytest.fixture
async def test_user(db_session: AsyncSession, test_practice: Practice) -> User:
    """Create test user with unique email.

    Uses OWNER role so role-restricted endpoints (e.g. delete_patient which
    requires OWNER/ADMIN) are exercisable. Role-specific permission tests
    should create their own user with the relevant role.
    """
    unique_email = f"testuser_{uuid_lib.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid_lib.uuid4(),
        email=unique_email,
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        role="OWNER",
        practice_id=test_practice.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_patient(db_session: AsyncSession, test_practice: Practice) -> Patient:
    """Create test patient"""
    from app.core.search_index import hmac_index
    patient = Patient(
        id=uuid_lib.uuid4(),
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
    patient.search_index_email = hmac_index("john.doe@example.com")
    patient.search_index_phone = hmac_index("+1234567890")
    patient.search_index_last_name = hmac_index("Doe")
    db_session.add(patient)
    await db_session.flush()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def test_appointment(
    db_session: AsyncSession,
    test_practice: Practice,
    test_patient: Patient,
    test_user: User
) -> Appointment:
    """Create test appointment"""
    appointment = Appointment(
        id=uuid_lib.uuid4(),
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
    await db_session.flush()
    await db_session.refresh(appointment)
    return appointment


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user"""
    login_data = {
        "email": test_user.email,
        "password": "testpassword123"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    if response.status_code != 200:
        # If login fails, return a dummy token for tests that don't require valid auth
        return {"Authorization": "Bearer dummy-token"}
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def other_practice(db_session: AsyncSession) -> Practice:
    """Create a second practice for cross-tenant isolation tests"""
    practice = Practice(
        id=uuid_lib.uuid4(),
        name="Other Practice",
        email="other@practice.com",
        phone="555-0200",
        address_street="456 Other St",
        address_city="Otherville",
        address_state="OT",
        address_zip="54321",
    )
    db_session.add(practice)
    await db_session.flush()
    await db_session.refresh(practice)
    return practice


@pytest.fixture
async def other_user(db_session: AsyncSession, other_practice: Practice) -> User:
    """Create a second user belonging to other_practice for tenant isolation tests"""
    unique_email = f"otheruser_{uuid_lib.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid_lib.uuid4(),
        email=unique_email,
        password_hash=get_password_hash("otherpassword123"),
        first_name="Other",
        last_name="User",
        role="OWNER",
        practice_id=other_practice.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_patient(db_session: AsyncSession, other_practice: Practice) -> Patient:
    """Create a patient in other_practice for cross-tenant tests"""
    patient = Patient(
        id=uuid_lib.uuid4(),
        practice_id=other_practice.id,
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        phone="+1987654321",
        date_of_birth=datetime.date(1985, 5, 15),
        gender="female",
        address_street="789 Oak St",
        address_city="Oakville",
        address_state="CA",
        address_zip="90210",
        emergency_contact={
            "name": "John Smith",
            "relationship": "spouse",
            "phone": "+1987654322"
        },
        medical_alerts=[],
        status="active",
    )
    db_session.add(patient)
    await db_session.flush()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def other_appointment(
    db_session: AsyncSession,
    other_practice: Practice,
    other_patient: Patient,
    other_user: User,
) -> Appointment:
    """Create an appointment in other_practice for cross-tenant tests"""
    appointment = Appointment(
        id=uuid_lib.uuid4(),
        practice_id=other_practice.id,
        patient_id=other_patient.id,
        provider_id=other_user.id,
        appointment_type="consultation",
        status="scheduled",
        start_time=datetime.datetime(2026, 4, 20, 14, 0, 0),
        end_time=datetime.datetime(2026, 4, 20, 15, 0, 0),
        duration=60,
        notes="Other practice appointment",
    )
    db_session.add(appointment)
    await db_session.flush()
    await db_session.refresh(appointment)
    return appointment


@pytest.fixture
async def other_auth_headers(client: AsyncClient, other_user: User) -> dict:
    """Get authentication headers for the other practice user"""
    login_data = {
        "email": other_user.email,
        "password": "otherpassword123"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    if response.status_code != 200:
        return {"Authorization": "Bearer dummy-token"}
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return {
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ENCRYPTION_KEY": test_encryption_key,
        "DATABASE_URL": SQLALCHEMY_DATABASE_URL,
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "ENVIRONMENT": "test",
    }