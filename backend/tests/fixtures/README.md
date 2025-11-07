# Fixtures e Configurações - EVAonline Tests

Dados compartilhados, configurações e mocks para todos os testes.

## Arquivos

- **test_config.py** - Configurações de teste
  - Variáveis de ambiente para Redis, PostgreSQL, API
  - Tokens de autenticação
  - Timeouts e retry settings

- **conftest.py** - Configuração do pytest
  - Fixtures compartilhadas
  - Setup e teardown
  - Banco de dados de teste

## Como Usar

### Em seus testes

```python
from backend.tests.fixtures.test_config import REDIS_HOST, POSTGRES_HOST

def test_something():
    assert REDIS_HOST == "localhost"
```

### Com pytest fixtures

```python
import pytest

@pytest.fixture
def client():
    """Fixture para cliente API"""
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)

def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
```

## Configurações Disponíveis

### Redis
- `REDIS_HOST`: localhost
- `REDIS_PORT`: 6379
- `REDIS_PASSWORD`: (env var)
- `REDIS_DB`: 0

### PostgreSQL
- `POSTGRES_HOST`: localhost
- `POSTGRES_PORT`: 5432
- `POSTGRES_USER`: evaonline
- `POSTGRES_PASSWORD`: (env var)
- `POSTGRES_DB`: evaonline

### API
- `API_BASE_URL`: http://localhost:8000
- `METRICS_TOKEN`: test-token-12345

### Testes
- `TEST_RETRIES`: 3
- `TEST_TIMEOUT`: 10 segundos
