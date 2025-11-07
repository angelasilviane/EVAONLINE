@echo off
REM ============================================================================
REM SCRIPT PARA EXECUTAR TESTES COM DOCKER - EVAonline (Windows)
REM ============================================================================
REM Usa docker-compose para executar testes de forma isolada

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo [*] 🧪 SISTEMA DE TESTES - EVAonline (via Docker)
echo ============================================================================
echo.

REM Verificar se docker-compose está instalado
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ❌ docker-compose não encontrado
    exit /b 1
)

REM Verificar se docker está rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ❌ Docker não está rodando
    exit /b 1
)

for /f "tokens=*" %%i in ('docker --version') do set DOCKER_VERSION=%%i
for /f "tokens=*" %%i in ('docker-compose --version') do set COMPOSE_VERSION=%%i

echo [INFO] ℹ️  Docker: %DOCKER_VERSION%
echo [INFO] ℹ️  Docker Compose: %COMPOSE_VERSION%
echo.

REM ============================================================================
REM BUILD E INICIALIZAÇÃO
REM ============================================================================

echo ============================================================================
echo [*] ▶️  Iniciando serviços (PostgreSQL, Redis)
echo ============================================================================
echo.

echo [INFO] ℹ️  Construindo imagens do Docker...
docker-compose build --quiet postgres redis test-runner
if errorlevel 1 (
    echo [ERROR] ❌ Erro ao construir imagens
    exit /b 1
)
echo [SUCCESS] ✅ Imagens construídas
echo.

echo [INFO] ℹ️  Iniciando PostgreSQL e Redis...
docker-compose up -d postgres redis
if errorlevel 1 (
    echo [ERROR] ❌ Erro ao iniciar serviços
    exit /b 1
)
echo [SUCCESS] ✅ Serviços iniciados
echo.

REM Aguardar 5 segundos
echo [INFO] ℹ️  Aguardando serviços ficarem saudáveis...
timeout /t 5 /nobreak >nul

REM Aguardar PostgreSQL
set /a attempt=0
set /a max_attempts=30

:wait_postgres
if %attempt% geq %max_attempts% (
    echo [ERROR] ❌ PostgreSQL não respondeu após %max_attempts% tentativas
    exit /b 1
)

docker exec evaonline-postgres pg_isready -U evaonline >nul 2>&1
if errorlevel 1 (
    set /a attempt+=1
    echo -n .
    timeout /t 1 /nobreak >nul
    goto wait_postgres
)
echo.
echo [SUCCESS] ✅ PostgreSQL pronto
echo.

REM Aguardar Redis
set /a attempt=0

:wait_redis
if %attempt% geq %max_attempts% (
    echo [ERROR] ❌ Redis não respondeu após %max_attempts% tentativas
    exit /b 1
)

docker exec evaonline-redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    set /a attempt+=1
    echo -n .
    timeout /t 1 /nobreak >nul
    goto wait_redis
)
echo.
echo [SUCCESS] ✅ Redis pronto
echo.

REM ============================================================================
REM EXECUTAR TESTES
REM ============================================================================

echo ============================================================================
echo [*] 🧪 EXECUTANDO TESTES
echo ============================================================================
echo.

docker-compose run --rm test-runner
set TEST_RESULT=%errorlevel%

echo.

REM ============================================================================
REM LIMPEZA
REM ============================================================================

echo ============================================================================
echo [*] 🧹 Limpeza
echo ============================================================================
echo.

set /p CLEANUP="Deseja parar os containers? (s/n): "
if /i "%CLEANUP%"=="s" (
    echo [INFO] ℹ️  Parando containers...
    docker-compose down -v
    if errorlevel 1 (
        echo [WARNING] ⚠️  Erro ao parar containers
    ) else (
        echo [SUCCESS] ✅ Containers parados
    )
) else (
    echo [WARNING] ⚠️  Containers continuam rodando
    echo [INFO] ℹ️  Pare manualmente com: docker-compose down
)

echo.

REM ============================================================================
REM RESULTADO FINAL
REM ============================================================================

if %TEST_RESULT% equ 0 (
    echo ============================================================================
    echo [SUCCESS] ✅ TODOS OS TESTES PASSARAM!
    echo [SUCCESS] ✅ Backend está operacional e pronto para uso.
    echo ============================================================================
    exit /b 0
) else (
    echo ============================================================================
    echo [ERROR] ❌ TESTES FALHARAM
    echo [ERROR] ❌ Verifique os erros acima.
    echo ============================================================================
    exit /b 1
)
