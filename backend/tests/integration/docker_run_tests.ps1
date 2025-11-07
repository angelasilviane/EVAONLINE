#!/usr/bin/env pwsh
# 🚀 START DOCKER - Inicia ambiente completo com testes

Write-Host "`n$('='*80)" -ForegroundColor Cyan
Write-Host "🚀 DOCKER SETUP - EVAonline Backend Complete" -ForegroundColor Cyan
Write-Host "$('='*80)`n" -ForegroundColor Cyan

# 1. Stop old containers
Write-Host "[1] Parando containers antigos..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# 2. Start PostgreSQL and Redis
Write-Host "[2] Iniciando PostgreSQL e Redis..." -ForegroundColor Yellow
docker-compose up -d postgres redis

# 3. Wait for services
Write-Host "[3] Aguardando services ficarem prontos..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# 4. Check health
Write-Host "[4] Verificando saude dos services..." -ForegroundColor Yellow

# PostgreSQL
try {
    $pgCheck = docker exec evaonline-postgres pg_isready -U evaonline -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ PostgreSQL pronto" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  PostgreSQL ainda iniciando..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ❌ Erro ao verificar PostgreSQL" -ForegroundColor Red
}

# Redis
try {
    $redisCheck = docker exec evaonline-redis redis-cli ping 2>&1
    if ($redisCheck -match "PONG" -or $LASTEXITCODE -eq 0) {
        Write-Host "    ✅ Redis pronto" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  Redis ainda iniciando..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ⚠️  Redis verificacao" -ForegroundColor Yellow
}

# 5. Start test runner
Write-Host "`n[5] Iniciando test-runner no Docker..." -ForegroundColor Yellow
Write-Host "    Executando: docker-compose run --rm test-runner`n" -ForegroundColor Cyan

docker-compose run --rm test-runner

$exitCode = $LASTEXITCODE

Write-Host "`n$('='*80)" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "✅ TESTES PASSARAM - Ambiente pronto!" -ForegroundColor Green
} else {
    Write-Host "❌ TESTES FALHARAM - Verifique os erros acima" -ForegroundColor Red
}
Write-Host "$('='*80)`n" -ForegroundColor Cyan

# 6. Options for next steps
Write-Host "[6] Opcoes de continuacao:" -ForegroundColor Yellow
Write-Host "    • Rodar API:              docker-compose up -d api" -ForegroundColor White
Write-Host "    • Rodar API (dev):        docker-compose up -d api-dev" -ForegroundColor White
Write-Host "    • Rodar Celery:           docker-compose up -d celery-worker celery-beat" -ForegroundColor White
Write-Host "    • Ver Logs API:           docker logs -f evaonline-api" -ForegroundColor White
Write-Host "    • Ver status services:    docker-compose ps" -ForegroundColor White
Write-Host "    • Parar tudo:             docker-compose down" -ForegroundColor White
Write-Host "`n"

exit $exitCode
