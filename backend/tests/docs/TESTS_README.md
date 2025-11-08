# 🧪 Testes do Backend - EVAonline

## 📋 Descrição

Este diretório contém uma suíte completa de testes para validar a infraestrutura do backend sem usar o frontend.

## 🚀 Scripts de Teste

### 1. **test_backend_audit.py** - Auditoria Completa
Testa toda a infraestrutura do backend em 14 seções:

```bash
python backend/tests/test_backend_audit.py
```

**Testa:**
- ✅ Importações críticas (FastAPI, SQLAlchemy, Redis, etc.)
- ✅ Configurações (Pydantic Settings)
- ✅ Conexão PostgreSQL
- ✅ Conexão Redis
- ✅ Modelos SQLAlchemy
- ✅ App FastAPI
- ✅ Rotas de Health Check
- ✅ Rotas de ETo
- ✅ Fontes de Clima
- ✅ Configuração Celery
- ✅ Migrações Alembic
- ✅ Variáveis de Ambiente
- ✅ Tabelas do Banco
- ✅ Prometheus Metrics

---

### 2. **test_routes.py** - Teste de Rotas
Testa todos os endpoints da API com diferentes métodos HTTP:

```bash
python backend/tests/test_routes.py
```

**Testa:**
- ✅ Health Check endpoints (GET /health, /health/detailed, /ready)
- ✅ Status endpoints (config, services, cache, tasks, logs)
- ✅ ETo calculation (POST, GET)
- ✅ Favorites management (ADD, LIST, DELETE)
- ✅ Climate sources (available, info, coverage)
- ✅ Cache operations (stats, clear)
- ✅ Statistics endpoints
- ✅ Documentation (docs, redoc, openapi.json)
- ✅ Prometheus metrics

**Totalizando:** ~40+ rotas testadas

---

### 3. **test_database.py** - Teste do Banco de Dados
Testa operações CRUD e integridade dos dados:

```bash
python backend/tests/test_database.py
```

**Testa:**
- ✅ Conexão e Schema
- ✅ Operações VisitorStats (INSERT, UPDATE, DELETE, SELECT)
- ✅ Operações UserFavorites (CREATE, READ, UPDATE, DELETE)
- ✅ Operações Cache
- ✅ Performance de Queries
- ✅ Transações
- ✅ Integridade de Dados (Foreign Keys, Unique Constraints)

---

### 4. **test_performance.py** - Teste de Performance
Load testing e análise de performance:

```bash
python backend/tests/test_performance.py
```

**Testa:**
- ✅ Health check load test (100 requisições)
- ✅ Requisições concorrentes (50 simultâneas)
- ✅ Comparação de endpoints
- ✅ Taxa de erro
- ✅ Stress test (30 segundos contínuos)

**Métricas Coletadas:**
- Throughput (req/s)
- Latência (avg, min, max, mediana)
- Taxa de sucesso
- Códigos de erro HTTP

---

### 5. **run_all_tests.py** - Executor de Todos os Testes
Executa todos os scripts de teste em sequência:

```bash
python backend/tests/run_all_tests.py
```

Executa:
1. test_backend_audit.py
2. test_routes.py
3. test_database.py
4. test_performance.py

Gera um resumo final com status de cada teste.

---

## 🔧 Requisitos

- Python 3.12+
- Ambiente virtual ativado (.venv)
- Dependências instaladas: `pip install -e .`
- PostgreSQL rodando (localhost:5432)
- Redis rodando (localhost:6379)
- Backend rodando (localhost:8000) - para testes de rotas

### Iniciar Serviços

**PostgreSQL (Docker):**
```bash
docker run -d --name postgres -e POSTGRES_PASSWORD=pass -p 5432:5432 postgres:15
```

**Redis (Docker):**
```bash
docker run -d --name redis -p 6379:6379 redis:7
```

**Backend:**
```bash
cd backend
uvicorn main:app --reload
```

---

## 📊 Interpretando Resultados

### Status dos Testes

```
✅ PASSOU     - Teste bem-sucedido
❌ FALHOU     - Teste falhou (erro crítico)
⚠️  AVISO      - Teste com aviso (não-crítico)
ℹ️  INFO       - Informação adicional
```

### Saída Esperada

Cada teste produz uma saída estruturada com:
- Cabeçalho descritivo
- Resultado de cada sub-teste
- Detalhes/erros quando aplicável
- Resumo final com estatísticas

**Exemplo:**
```
================================================================================
TESTE 1: AUDITORIA BACKEND
================================================================================

✅ Import FastAPI
✅ Import SQLAlchemy
✅ Conexão PostgreSQL | Versão: PostgreSQL 15.2
...

================================================================================
📊 RESUMO
================================================================================

✅ Passou: 28/30 (93.3%)
❌ Falhou: 2
⚠️  Avisos: 0

================================================================================
✅ BACKEND ESTÁ SAUDÁVEL!
```

---

## 🐛 Troubleshooting

### Erro: "Connection refused" (PostgreSQL)
- Verifique se PostgreSQL está rodando
- Verify .env tem credenciais corretas
- Teste conexão: `psql -U evaonline -h localhost`

### Erro: "REDIS_PASSWORD" não configurado
- Verifique arquivo .env
- Redis pode estar sem password: `REDIS_PASSWORD=` (deixar vazio)

### Erro: "Module not found"
- Ative o ambiente virtual: `.venv\Scripts\activate`
- Instale dependências: `pip install -e .`

### Erro: "Address already in use"
- Verifique se porta 8000 já está em uso
- Kill processo: `taskkill /f /im python.exe /t`

---

## 📈 Melhorias Sugeridas

Após os testes passarem:

1. **Integração Contínua**
   - Adicionar testes a CI/CD pipeline
   - Executar testes automaticamente em cada push

2. **Monitoramento**
   - Acompanhar métricas de performance ao longo do tempo
   - Alertas se performance degradar

3. **Testes Adicionais**
   - Testes de segurança (CORS, autenticação)
   - Testes de resiliência (falhas de BD, Redis)
   - Testes end-to-end com dados reais

---

## 📝 Estrutura de Testes

```
backend/tests/
├── test_backend_audit.py      # Auditoria geral (14 testes)
├── test_routes.py              # Rotas API (40+ endpoints)
├── test_database.py            # Operações BD (7 testes)
├── test_performance.py         # Performance (5 testes)
├── run_all_tests.py            # Executor principal
├── conftest.py                 # Configuração pytest
├── pytest.ini                  # Configuração pytest
├── unit/                       # Testes unitários
└── README.md                   # Este arquivo
```

---

## 🚀 Próximos Passos

1. **Execute auditoria backend:**
   ```bash
   python backend/tests/test_backend_audit.py
   ```

2. **Teste todas as rotas:**
   ```bash
   python backend/tests/test_routes.py
   ```

3. **Teste o banco de dados:**
   ```bash
   python backend/tests/test_database.py
   ```

4. **Execute teste de performance:**
   ```bash
   python backend/tests/test_performance.py
   ```

5. **Execute todos os testes:**
   ```bash
   python backend/tests/run_all_tests.py
   ```

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique o arquivo .env
2. Certifique-se que todos os serviços estão rodando
3. Verifique os logs em `logs/` diretório
4. Execute com flag `-v` para verbose mode

---

**Última atualização:** 2025-11-03
**Versão:** 1.0.0
