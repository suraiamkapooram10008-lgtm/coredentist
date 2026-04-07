"""
Test configuration and fixtures for CoreDent API tests
"""
import os

# Ensure required env vars for Settings to load during tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-bytes-long!")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
import asyncio
import datetime
import uuid as uuid_lib
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.practice import Practice
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment

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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
async def setup_database():
    """Create database tables before tests and drop after"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
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
    await db_session.commit()
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
    await db_session.commit()
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
    await db_session.commit()
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
    await db_session.commit()
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
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return {
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ENCRYPTION_KEY": "test-encryption-key-32-bytes-long!",
        "DATABASE_URL": SQLALCHEMY_DATABASE_URL,
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "ENVIRONMENT": "test",
    }