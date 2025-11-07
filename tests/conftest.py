"""
Pytest configuration and fixtures for the entire test suite.
Provides reusable fixtures for DB, Redis, FastAPI client, and settings.
"""

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Setup path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def db_url() -> str:
    """Get database URL from env or use test defaults."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://evaonline:evaonline@localhost:5432/evaonline_test",
    )


@pytest.fixture(scope="session")
def engine(db_url: str):
    """Create SQLAlchemy engine for test DB."""
    from backend.database.connection import Base

    engine = create_engine(db_url, echo=False)

    # Create tables
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# REDIS FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def redis_url() -> str:
    """Get Redis URL from env or use test defaults."""
    return os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")


@pytest.fixture
def redis_client(redis_url: str):
    """Provide a Redis client for testing."""
    import redis

    client = redis.from_url(redis_url, decode_responses=True)
    client.flushdb()  # Clean before test
    yield client
    client.flushdb()  # Clean after test
    client.close()


# ============================================================================
# FASTAPI FIXTURES
# ============================================================================


@pytest.fixture
def app():
    """Provide FastAPI app instance."""
    from backend.main import app

    return app


@pytest.fixture
def client(app) -> TestClient:
    """Provide FastAPI TestClient."""
    return TestClient(app)


# ============================================================================
# SETTINGS FIXTURES
# ============================================================================


@pytest.fixture
def settings():
    """Provide application settings."""
    from config.settings.app_config import get_settings

    return get_settings()


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================


@pytest.fixture
def mock_climate_data() -> dict:
    """Mock climate data for testing."""
    return {
        "latitude": -22.9068,
        "longitude": -43.1729,
        "temperature": 25.5,
        "humidity": 65,
        "pressure": 1013.25,
        "wind_speed": 5.2,
        "precipitation": 0.0,
    }


@pytest.fixture
def mock_admin_user() -> dict:
    """Mock admin user data."""
    return {
        "username": "test_admin",
        "email": "admin@test.local",
        "password_hash": "hashed_password",
        "is_active": True,
        "is_admin": True,
    }


@pytest.fixture
def mock_user_location() -> dict:
    """Mock user location favorite."""
    return {
        "name": "Test Location",
        "latitude": -22.9068,
        "longitude": -43.1729,
        "city": "Rio de Janeiro",
        "state": "RJ",
        "country": "Brazil",
    }
