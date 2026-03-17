"""
Test configuration and fixtures for CoreDent API tests
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
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
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        first_name="Test",
        last_name="User",
        role="dentist",
        practice_id="practice-1",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_patient(db_session):
    """Create test patient"""
    patient = Patient(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        date_of_birth="1990-01-01",
        gender="male",
        address={
            "street": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62701",
            "country": "USA"
        },
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
def test_appointment(db_session, test_patient, test_user):
    """Create test appointment"""
    appointment = Appointment(
        patient_id=test_patient.id,
        provider_id=test_user.id,
        appointment_type="cleaning",
        status="scheduled",
        start_time="2026-03-17T10:00:00",
        end_time="2026-03-17T11:00:00",
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
        "username": test_user.email,
        "password": "secret"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
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