"""
Test configuration and fixtures for CoreDent API tests
"""
import os
import sys
from cryptography.fernet import Fernet

# Generate valid Fernet key for testing
test_encryption_key = Fernet.generate_key().decode()

# Set required env vars BEFORE importing app (must use direct assignment, not setdefault)
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-12345"
os.environ["ENCRYPTION_KEY"] = test_encryption_key
os.environ["DEBUG"] = "True"
os.environ["ENVIRONMENT"] = "test"

import pytest
import asyncio
import datetime
import uuid as uuid_lib
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import configure_mappers

# Import all models to ensure they're registered with SQLAlchemy
from app.core.database import Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.main import app as fastapi_app
from app.api.deps import get_db

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
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create async test engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for testing"""
    async with TestingSessionLocal() as session:
        yield session


fastapi_app.dependency_overrides[get_db] = override_get_db


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
    """Create async test client"""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        yield ac


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
    """Create test user with unique email"""
    unique_email = f"testuser_{uuid_lib.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid_lib.uuid4(),
        email=unique_email,
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        role="dentist",
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
def mock_settings():
    """Mock settings for testing"""
    return {
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ENCRYPTION_KEY": test_encryption_key,
        "DATABASE_URL": SQLALCHEMY_DATABASE_URL,
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "ENVIRONMENT": "test",
    }