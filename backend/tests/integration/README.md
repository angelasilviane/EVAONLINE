# Testes de Integração - EVAonline

Testes que validam a integração entre diferentes componentes do backend.

## Arquivos

- **test_backend_audit.py** - Auditoria completa (14 seções)
  - Importações, Settings, PostgreSQL, Redis
  - Modelos SQLAlchemy, FastAPI, Rotas
  - Celery, Alembic, Environment vars, Métricas Prometheus
  
- **test_routes.py** - Testes de endpoints API (9 seções)
  - Health checks (3 endpoints)
  - Status internos (7 endpoints)
  - ETo calculation (5 endpoints)
  - Favorites (3 endpoints)
  - Climate sources (7 endpoints)
  - Cache (2 endpoints)
  - Statistics (3 endpoints)
  - Documentation (3 endpoints)
  - Metrics (1 endpoint)
  
- **test_database.py** - Operações do banco de dados (7 seções)
  - Schema verification
  - VisitorStats CRUD
  - UserFavorites relationships
  - Cache operations
  - Query performance
  - Transactions
  - Data integrity

## Como Rodar

Todos os testes:
```bash
pytest . -v
```

Teste específico:
```bash
pytest test_backend_audit.py -v
pytest test_routes.py::test_health_routes -v
```

Com relatório de cobertura:
```bash
pytest . --cov=backend --cov-report=html
```

## Resultados Esperados

- Backend Audit: 40/43 (93%) ✅
- Routes: 26/30 (87%) ✅
- Database: 0/7 (esperado - PostgreSQL offline)
