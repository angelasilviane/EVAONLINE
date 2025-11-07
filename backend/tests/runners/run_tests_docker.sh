#!/bin/bash
# ============================================================================
# SCRIPT PARA EXECUTAR TESTES - EVAonline
# ============================================================================
# Usa docker-compose para executar testes de forma isolada

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# FUNÇÕES
# ============================================================================

print_header() {
    echo -e "${CYAN}${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  ${1}${NC}"
}

# ============================================================================
# MAIN
# ============================================================================

echo ""
echo "============================================================================"
print_header "🧪 SISTEMA DE TESTES - EVAonline (via Docker)"
echo "============================================================================"
echo ""

# Verificar se docker-compose está instalado
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose não encontrado. Instale e tente novamente."
    exit 1
fi

# Verificar se docker está rodando
if ! docker info > /dev/null 2>&1; then
    print_error "Docker não está rodando. Inicie o Docker e tente novamente."
    exit 1
fi

print_info "Docker encontrado: $(docker --version)"
print_info "Docker Compose encontrado: $(docker-compose --version)"

echo ""

# ============================================================================
# BUILD E INICIALIZAÇÃO
# ============================================================================

echo "============================================================================"
print_header "▶️  Iniciando serviços (PostgreSQL, Redis)"
echo "============================================================================"
echo ""

# Construir imagem de testes se não existir
print_info "Construindo imagens do Docker..."
docker-compose build --quiet postgres redis test-runner
print_success "Imagens construídas"

echo ""

# Iniciar apenas os serviços necessários
print_info "Iniciando PostgreSQL e Redis..."
docker-compose up -d postgres redis
print_success "Serviços iniciados"

echo ""

# Aguardar serviços ficarem saudáveis
print_info "Aguardando serviços ficarem saudáveis..."
sleep 5

max_attempts=30
attempt=0

# PostgreSQL
while ! docker exec evaonline-postgres pg_isready -U evaonline &> /dev/null; do
    if [ $attempt -ge $max_attempts ]; then
        print_error "PostgreSQL não respondeu após $max_attempts tentativas"
        exit 1
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 1
done
print_success "PostgreSQL pronto"

# Redis
attempt=0
while ! docker exec evaonline-redis redis-cli ping &> /dev/null; do
    if [ $attempt -ge $max_attempts ]; then
        print_error "Redis não respondeu após $max_attempts tentativas"
        exit 1
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 1
done
print_success "Redis pronto"

echo ""

# ============================================================================
# EXECUTAR TESTES
# ============================================================================

echo "============================================================================"
print_header "🧪 EXECUTANDO TESTES"
echo "============================================================================"
echo ""

# Executar testes
docker-compose run --rm test-runner

TEST_RESULT=$?

echo ""

# ============================================================================
# LIMPEZA
# ============================================================================

echo "============================================================================"
print_header "🧹 Limpeza"
echo "============================================================================"
echo ""

read -p "Deseja parar os containers? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    print_info "Parando containers..."
    docker-compose down -v
    print_success "Containers parados"
else
    print_warning "Containers continuam rodando. Pare manualmente com: docker-compose down"
fi

echo ""

# ============================================================================
# RESULTADO FINAL
# ============================================================================

if [ $TEST_RESULT -eq 0 ]; then
    echo "============================================================================"
    print_success "TODOS OS TESTES PASSARAM!"
    print_success "Backend está operacional e pronto para uso."
    echo "============================================================================"
    exit 0
else
    echo "============================================================================"
    print_error "TESTES FALHARAM"
    print_error "Verifique os erros acima."
    echo "============================================================================"
    exit 1
fi
