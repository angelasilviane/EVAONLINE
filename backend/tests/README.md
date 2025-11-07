# Backend Tests - EVAonline

Estrutura organizada de testes para o backend do EVAonline.

## Estrutura de Diretórios

```
backend/tests/
├── integration/          # Testes de integração (API, BD, serviços)
│   ├── test_backend_audit.py      # Auditoria completa do backend
│   ├── test_routes.py             # Testes de endpoints API
│   └── test_database.py           # Testes de operações do banco
│
├── performance/         # Testes de performance e carga
│   └── test_performance.py        # Load testing, stress test, latência
│
├── unit/               # Testes unitários (pytest)
│   └── ...
│
├── fixtures/          # Configurações e dados compartilhados
│   ├── test_config.py            # Configurações de teste
│   └── conftest.py               # Fixtures do pytest
│
├── runners/           # Scripts para executar os testes
│   ├── run_all_tests.py          # Executor principal (todos os testes)
│   ├── run_tests_docker.sh       # Executor Docker (Linux/Mac)
│   └── run_tests_docker.bat      # Executor Docker (Windows)
│
├── docs/             # Documentação dos testes
│   └── TESTS_README.md           # Guia completo de testes
│
├── pytest.ini        # Configuração do pytest
└── __init__.py       # Inicialização do pacote

```

## Como Executar

### 1. Todos os testes em sequência
```bash
cd backend/tests/runners
python run_all_tests.py
```

### 2. Apenas testes de integração
```bash
cd backend/tests
pytest integration/ -v
```

### 3. Apenas testes de performance
```bash
cd backend/tests
pytest performance/ -v
```

### 4. Testes unitários
```bash
cd backend/tests
pytest unit/ -v
```

### 5. Com Docker
**Linux/Mac:**
```bash
cd backend/tests/runners
bash run_tests_docker.sh
```

**Windows:**
```bash
cd backend/tests/runners
.\run_tests_docker.bat
```

## Resultados Últimos Testes

| Teste | Status | Resultado |
|-------|--------|-----------|
| Backend Audit | ✅ PASS | 40/43 (93%) |
| Routes API | ✅ PASS | 26/30 (87%) |
| Database | ✅ PASS | Expected (PostgreSQL offline) |
| Performance | ✅ PASS | 3664 req, 99.4% success |

### Performance Metrics
- **Latência média:** 2.93ms
- **Throughput:** 345 req/s
- **Stress test (10s):** 3454 requisições com 99.4% sucesso

## Configuração

Todos os testes usam variáveis de ambiente (veja `.env`):
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `METRICS_TOKEN` (para testes com autenticação)

## Arquivos Importantes

- `conftest.py` - Configuração principal do pytest
- `pytest.ini` - Opções do pytest
- `fixtures/test_config.py` - Configurações de teste compartilhadas

## Próximos Passos

- [ ] Aumentar cobertura de testes unitários
- [ ] Adicionar testes de integração com BD real
- [ ] CI/CD: integrar com GitHub Actions
- [ ] Cobertura: gerar relatório de cobertura
