#!/bin/bash
# ============================================================================
# ENTRYPOINT PARA TESTES - EVAonline
# ============================================================================
# Este script executa todos os testes do backend dentro do container Docker
# Usado pelo serviço test-runner no docker-compose.yml

set -e  # Exit on error

echo "============================================================================"
echo "🧪 SISTEMA DE TESTES - EVAonline"
echo "============================================================================"
echo ""
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container ID: $(hostname)"
echo "Ambiente: ${ENVIRONMENT:-testing}"
echo ""

# ============================================================================
# AGUARDAR SERVIÇOS SEREM SAUDÁVEIS
# ============================================================================

echo "⏳ Aguardando PostgreSQL..."
max_attempts=30
attempt=0
while ! nc -z postgres 5432; do
    if [ $attempt -ge $max_attempts ]; then
        echo "❌ PostgreSQL não respondeu após $max_attempts tentativas"
        exit 1
    fi
    attempt=$((attempt + 1))
    echo "   Tentativa $attempt/$max_attempts..."
    sleep 1
done
echo "✅ PostgreSQL pronto"

echo ""
echo "⏳ Aguardando Redis..."
attempt=0
while ! redis-cli -h redis -a "${REDIS_PASSWORD}" ping > /dev/null 2>&1; do
    if [ $attempt -ge $max_attempts ]; then
        echo "❌ Redis não respondeu após $max_attempts tentativas"
        exit 1
    fi
    attempt=$((attempt + 1))
    echo "   Tentativa $attempt/$max_attempts..."
    sleep 1
done
echo "✅ Redis pronto"

echo ""

# ============================================================================
# EXECUTAR MIGRATIONS (ALEMBIC)
# ============================================================================

echo "🔄 Executando migrações do banco de dados..."
cd /app

if [ -d "alembic" ] && [ -f "alembic.ini" ]; then
    echo "   Executando: alembic upgrade heads"
    alembic upgrade heads
    echo "✅ Migrações concluídas"
else
    echo "⚠️  Alembic não encontrado, pulando migrações"
fi

echo ""

# ============================================================================
# EXECUTAR TESTES
# ============================================================================

echo "============================================================================"
echo "🧪 INICIANDO TESTES"
echo "============================================================================"
echo ""

# Contador de testes
TESTS_PASSED=0
TESTS_FAILED=0

# Array de testes
declare -a TESTS=(
    "backend/tests/test_backend_audit.py:Auditoria Backend (14 testes)"
    "backend/tests/test_routes.py:Teste de Rotas (40+ endpoints)"
    "backend/tests/test_database.py:Teste do Banco (7 testes)"
    "backend/tests/test_performance.py:Teste de Performance (5 testes)"
)

# Executar cada teste
for test_info in "${TESTS[@]}"; do
    IFS=':' read -r test_script test_desc <<< "$test_info"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "▶️  $test_desc"
    echo "   Arquivo: $test_script"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [ -f "$test_script" ]; then
        if python "$test_script"; then
            echo ""
            echo "✅ $test_desc - PASSOU"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo ""
            echo "❌ $test_desc - FALHOU"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo "⚠️  Arquivo não encontrado: $test_script"
    fi
    
    echo ""
done

# ============================================================================
# RESUMO FINAL
# ============================================================================

echo "============================================================================"
echo "📊 RESUMO DOS TESTES"
echo "============================================================================"
echo ""
echo "✅ Testes aprovados: $TESTS_PASSED"
echo "❌ Testes falhados: $TESTS_FAILED"
echo "📊 Total: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "🎉 TODOS OS TESTES PASSARAM!"
    echo "   Backend está operacional e pronto para uso."
    exit 0
else
    echo "⚠️  $TESTS_FAILED TESTE(S) FALHARAM"
    echo "   Verifique os erros acima."
    exit 1
fi
