"""
Test configuration and fixtures for CoreDent API tests
"""
import os

# Ensure required env vars for Settings to load during tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
import asyncio
import datetime
import uuid
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.practice import Practice
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Create test client"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create database session for testing"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_practice(db_session):
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
    db_session.commit()
    db_session.refresh(practice)
    return practice


@pytest.fixture
def test_user(db_session, test_practice):
    """Create test user with unique email"""
    import uuid
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        password_hash=get_password_hash("secret"),  # secret
        first_name="Test",
        last_name="User",
        role="dentist",
        practice_id=test_practice.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_patient(db_session, test_practice):
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
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def test_appointment(db_session, test_practice, test_patient, test_user):
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
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    login_data = {
        "email": test_user.email,
        "password": "secret"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return {
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": SQLALCHEMY_DATABASE_URL,
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "ENVIRONMENT": "test",
    }