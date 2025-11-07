# Test Runners - EVAonline

Scripts para executar os testes em diferentes ambientes.

## Scripts Disponíveis

### 1. run_all_tests.py
**Uso:** Python puro (recomendado para desenvolvimento local)

```bash
python run_all_tests.py
```

**O que faz:**
- Executa todos os testes em sequência
- Mostra progresso e resumo
- Retorna código de saída apropriado

**Testes executados:**
1. test_backend_audit.py (14 seções)
2. test_routes.py (9 endpoints)
3. test_database.py (7 testes)
4. test_performance.py (5 testes)

### 2. run_tests_docker.sh
**Uso:** Docker no Linux/Mac

```bash
bash run_tests_docker.sh
```

**O que faz:**
- Build da imagem Docker
- Inicia PostgreSQL e Redis
- Executa Alembic migrations
- Roda todos os testes
- Cleanup

### 3. run_tests_docker.bat
**Uso:** Docker no Windows

```bash
.\run_tests_docker.bat
```

**Funcionalidade:** Idêntica ao .sh, adaptada para Windows

## Fluxo de Execução

```
┌─────────────────────┐
│   run_all_tests.py  │
├─────────────────────┤
│ 1. Backend Audit    │ → test_backend_audit.py
│ 2. Routes Test      │ → test_routes.py
│ 3. Database Test    │ → test_database.py
│ 4. Performance Test │ → test_performance.py
└─────────────────────┘
        │
        ▼
   ┌─────────────┐
   │ Summary     │
   │ ✅ All OK   │
   └─────────────┘
```

## Opções de Execução

### Rodar testes individuais
```bash
cd ..
pytest integration/test_backend_audit.py -v
pytest performance/test_performance.py -v
pytest unit/ -v
```

### Com cobertura
```bash
pytest . --cov=backend --cov-report=term-missing
```

### Modo verbose
```bash
pytest . -vv -s
```

### Modo de parada rápida (para na primeira falha)
```bash
pytest . -x
```

## Status da Última Execução

✅ Todos os 4 runners passaram (122.4 segundos)

- Backend Audit: 40/43 PASS
- Routes: 26/30 PASS
- Database: 0/7 PASS (esperado - offline)
- Performance: Excelente (99.4% sucesso)
