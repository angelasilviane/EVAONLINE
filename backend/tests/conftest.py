"""
Fixtures compartilhadas para todos os testes do EVAonline
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Imports do projeto
from backend.database.connection import Base, get_db
from backend.main import app


# ============================================================================
# CONFIGURAÇÃO DO AMBIENTE DE TESTES
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configura variáveis de ambiente para testes"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/14"
    os.environ["LOG_LEVEL"] = "ERROR"
    yield
    # Cleanup após todos os testes


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def test_db_engine():
    """Engine SQLite em memória para testes"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Sessão do banco de dados para testes"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override da dependência get_db do FastAPI"""

    def _override_get_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def test_client(override_get_db) -> Generator[TestClient, None, None]:
    """Cliente de teste síncrono para a API"""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def async_test_client(
    override_get_db,
) -> AsyncGenerator[AsyncClient, None]:
    """Cliente de teste assíncrono para a API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# REDIS FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def mock_redis():
    """Mock do Redis para testes unitários"""
    try:
        import fakeredis

        redis_client = fakeredis.FakeRedis(decode_responses=True)
        yield redis_client
        redis_client.flushdb()
    except ImportError:
        # Se fakeredis não estiver instalado, usa mock
        mock = MagicMock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False
        yield mock


# ============================================================================
# CELERY FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def mock_celery():
    """Mock do Celery para testes unitários"""
    mock = MagicMock()
    mock.send_task.return_value.id = "test-task-id-123"
    mock.AsyncResult.return_value.state = "SUCCESS"
    mock.AsyncResult.return_value.result = {"status": "completed"}
    yield mock


# ============================================================================
# DATA FIXTURES (Exemplos de dados climáticos)
# ============================================================================


@pytest.fixture
def sample_climate_data():
    """Dados climáticos de exemplo"""
    return {
        "latitude": -23.5505,
        "longitude": -46.6333,
        "date": "2024-01-15",
        "temperature_max": 28.5,
        "temperature_min": 19.2,
        "humidity": 65.0,
        "wind_speed": 3.5,
        "solar_radiation": 22.5,
        "precipitation": 0.0,
    }


@pytest.fixture
def sample_eto_request():
    """Requisição ETO de exemplo"""
    return {
        "latitude": -23.5505,
        "longitude": -46.6333,
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "altitude": 760,
    }


# ============================================================================
# MOCK EXTERNAL APIS
# ============================================================================


@pytest.fixture
def mock_nasa_power_api(monkeypatch):
    """Mock da API NASA POWER"""

    async def mock_fetch(*args, **kwargs):
        return {
            "properties": {
                "parameter": {
                    "T2M": {"20240115": 23.5},
                    "T2M_MAX": {"20240115": 28.5},
                    "T2M_MIN": {"20240115": 19.2},
                }
            }
        }

    monkeypatch.setattr(
        "backend.api.services.nasa_power.fetch_nasa_power_data", mock_fetch
    )


@pytest.fixture
def mock_openmeteo_api(monkeypatch):
    """Mock da API OpenMeteo"""

    async def mock_fetch(*args, **kwargs):
        return {
            "daily": {
                "time": ["2024-01-15"],
                "temperature_2m_max": [28.5],
                "temperature_2m_min": [19.2],
                "precipitation_sum": [0.0],
            }
        }

    monkeypatch.setattr(
        "backend.api.services.openmeteo_archive.fetch_openmeteo_data",
        mock_fetch,
    )


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================


@pytest.fixture
def benchmark_timer():
    """Timer para testes de performance"""
    import time

    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.end = time.perf_counter()
            self.elapsed = self.end - self.start

    return Timer


# ============================================================================
# CLEANUP
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Limpa recursos após cada teste"""
    yield
    # Cleanup code aqui se necessário
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))
