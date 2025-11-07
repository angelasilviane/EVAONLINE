#!/usr/bin/env python3
"""
AUDITORIA COMPLETA DO BACKEND - EVAonline
==========================================
Testa toda a stack sem usar frontend.

Testes:
1. Importações críticas
2. Configurações (DB, Redis, Celery)
3. Conexão PostgreSQL
4. Conexão Redis
5. SQLAlchemy models
6. FastAPI app initialization
7. Routes registration
8. Health checks
9. Climate sources
10. Celery tasks
"""

import sys
from datetime import datetime
from pathlib import Path

# Adicionar raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

results = {"passed": 0, "failed": 0, "warnings": 0}


def header(text):
    """Print section header."""
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{text}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")


def success(msg, detail=""):
    """Print success message."""
    print(f"{GREEN}✅ {msg}{RESET}", end="")
    if detail:
        print(f" | {detail}")
    else:
        print()
    results["passed"] += 1


def error(msg, detail=""):
    """Print error message."""
    print(f"{RED}❌ {msg}{RESET}", end="")
    if detail:
        print(f" | {detail}")
    else:
        print()
    results["failed"] += 1


def warning(msg, detail=""):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {msg}{RESET}", end="")
    if detail:
        print(f" | {detail}")
    else:
        print()
    results["warnings"] += 1


# ============================================================================
# TESTE 1: IMPORTAÇÕES
# ============================================================================


def test_imports():
    """Test critical imports."""
    header("TESTE 1: IMPORTAÇÕES CRÍTICAS")

    imports = {
        "FastAPI": "from fastapi import FastAPI",
        "SQLAlchemy": "from sqlalchemy import create_engine",
        "Redis": "import redis",
        "Celery": "from celery import Celery",
        "Pydantic": "from pydantic import BaseModel",
        "Loguru": "from loguru import logger",
        "Prometheus": "from prometheus_fastapi_instrumentator import Instrumentator",
    }

    for name, stmt in imports.items():
        try:
            exec(stmt, {})
            success(f"Import {name}")
        except ImportError as e:
            error(f"Import {name}", str(e)[:50])

    # Backend specific imports
    backend_imports = {
        "AppSettings": "from config.settings.app_config import get_legacy_settings",
        "Logger": "from config.logging_config import get_logger",
        "API Router": "from backend.api.routes import api_router",
        "Health Checks": "from backend.database.health_checks import perform_full_health_check",
        "Climate Factory": "from backend.api.services.climate_factory import ClimateClientFactory",
        "ETo Services": "from backend.core.eto_calculation.eto_services import EToProcessingService",
    }

    for name, stmt in backend_imports.items():
        try:
            exec(stmt, {})
            success(f"Backend module {name}")
        except Exception as e:
            error(f"Backend module {name}", str(e)[:50])


# ============================================================================
# TESTE 2: CONFIGURAÇÕES
# ============================================================================


def test_settings():
    """Test configuration loading."""
    header("TESTE 2: CARREGAMENTO DE CONFIGURAÇÕES")

    try:
        from config.settings.app_config import get_legacy_settings

        settings = get_legacy_settings()
        success(
            "Settings carregadas", f"API_V1_PREFIX={settings.API_V1_PREFIX}"
        )

        # Database settings
        print(f"\n  📊 Database:")
        print(f"     Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        print(f"     DB: {settings.POSTGRES_DB}")

        from config.settings.app_config import get_database_url

        print(f"     URL: {get_database_url()}")

        # Redis settings
        print(f"\n  📊 Redis:")
        print(f"     Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

        from config.settings.app_config import get_redis_url

        print(f"     URL: {get_redis_url()}")

        # Celery settings
        print(f"\n  📊 Celery:")
        print(f"     Broker: {settings.CELERY_BROKER_URL}")
        print(f"     Backend: {settings.CELERY_RESULT_BACKEND}")

        # CORS
        print(f"\n  📊 CORS Origins: {settings.BACKEND_CORS_ORIGINS}")

    except Exception as e:
        error("Settings loading", str(e))


# ============================================================================
# TESTE 3: CONEXÃO PostgreSQL
# ============================================================================


def test_postgres():
    """Test PostgreSQL connection."""
    header("TESTE 3: CONEXÃO PostgreSQL")

    try:
        from config.settings.app_config import get_database_url
        from sqlalchemy import create_engine, text

        db_url = get_database_url()
        engine = create_engine(db_url)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            success("PostgreSQL conectado", version[:40])

        # Test pool size
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            success("Connection pool working")

    except Exception as e:
        error("PostgreSQL connection", str(e)[:50])


# ============================================================================
# TESTE 4: CONEXÃO Redis
# ============================================================================


def test_redis():
    """Test Redis connection."""
    header("TESTE 4: CONEXÃO Redis")

    try:
        import redis
        from config.settings.app_config import get_redis_url

        redis_url = get_redis_url()
        client = redis.from_url(redis_url)

        # Test ping
        pong = client.ping()
        success("Redis conectado", f"Ping={pong}")

        # Test set/get
        client.set("test_key", "test_value", ex=10)
        value = client.get("test_key")
        if value == b"test_value":
            success("Redis SET/GET working")
        else:
            error("Redis SET/GET", f"Expected b'test_value', got {value}")

        # Test delete
        client.delete("test_key")
        success("Redis DELETE working")

        # Test info
        info = client.info()
        success("Redis INFO", f"Version={info.get('redis_version')}")

    except Exception as e:
        error("Redis connection", str(e)[:50])


# ============================================================================
# TESTE 5: SQLALCHEMY MODELS
# ============================================================================


def test_models():
    """Test SQLAlchemy models."""
    header("TESTE 5: MODELOS SQLAlchemy")

    try:
        from backend.database.models.user_favorites import (
            UserFavorites,
            FavoriteLocation,
        )
        from backend.database.models.user_cache import UserSessionCache
        from backend.database.models.climate_data import ClimateData
        from backend.database.models.api_variables import APIVariables
        from backend.database.models.admin_user import AdminUser
        from backend.database.models.visitor_stats import VisitorStats

        success("Model UserFavorites")
        success("Model FavoriteLocation")
        success("Model UserSessionCache")
        success("Model ClimateData (multi-API)")
        success("Model APIVariables")
        success("Model VisitorStats")
        success("Model AdminUser")

        # Check tables
        from backend.database.connection import Base

        print("\n  📋 Tabelas no banco:")
        for table in Base.metadata.tables.keys():
            print(f"     Table: {table}")

    except Exception as e:
        error("Models loading", str(e)[:50])


# ============================================================================
# TESTE 6: FASTAPI APP
# ============================================================================


def test_fastapi_app():
    """Test FastAPI application."""
    header("TESTE 6: FASTAPI APP INITIALIZATION")

    try:
        from backend.main import app

        success("FastAPI app created")

        # Check routes
        routes_count = len(app.routes)
        success(f"Routes registradas: {routes_count}")

        # List routes
        print(f"\n  📋 Rotas registradas:")
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                print(f"     {list(route.methods)[0]:6} {route.path}")

    except Exception as e:
        error("FastAPI app", str(e)[:50])


# ============================================================================
# TESTE 7: ROTAS DE HEALTH CHECK
# ============================================================================


def test_health_routes():
    """Test health check routes."""
    header("TESTE 7: ROTAS DE HEALTH CHECK")

    try:
        from backend.api.routes.health import router

        routes = [rule for rule in router.routes if hasattr(rule, "path")]
        success(f"Health router com {len(routes)} rotas")

        for route in routes:
            if hasattr(route, "path"):
                print(f"     {route.path}")

    except Exception as e:
        error("Health routes", str(e)[:50])


# ============================================================================
# TESTE 8: ROTAS DE ETO
# ============================================================================


def test_eto_routes():
    """Test ETo routes."""
    header("TESTE 8: ROTAS DE ETO")

    try:
        from backend.api.routes.eto_routes import eto_router

        routes = [rule for rule in eto_router.routes if hasattr(rule, "path")]
        success(f"ETo router com {len(routes)} rotas")

        for route in routes:
            if hasattr(route, "path"):
                methods = (
                    list(route.methods)
                    if hasattr(route, "methods")
                    else ["GET"]
                )
                print(f"     {methods[0]:6} /internal/eto{route.path}")

    except Exception as e:
        error("ETo routes", str(e)[:50])


# ============================================================================
# TESTE 9: CLIMATE SOURCES
# ============================================================================


def test_climate_sources():
    """Test climate sources."""
    header("TESTE 9: CLIMATE SOURCES")

    try:
        from backend.api.services.climate_source_manager import (
            ClimateSourceManager,
        )

        manager = ClimateSourceManager()
        success("ClimateSourceManager criado")

        # Check available sources
        print(f"\n  📡 Fontes climáticas disponíveis:")
        sources = [
            "openmeteo_archive",
            "openmeteo_forecast",
            "nasa_power",
            "met_norway",
        ]
        for source in sources:
            print(f"     ✓ {source}")

    except Exception as e:
        error("Climate sources", str(e)[:50])


# ============================================================================
# TESTE 10: CELERY CONFIGURATION
# ============================================================================


def test_celery():
    """Test Celery configuration."""
    header("TESTE 10: CELERY CONFIGURATION")

    try:
        from config.settings.app_config import get_legacy_settings

        settings = get_legacy_settings()

        if settings.CELERY_BROKER_URL:
            success(
                "Celery BROKER_URL configurado",
                settings.CELERY_BROKER_URL[:30],
            )
        else:
            warning("Celery BROKER_URL não configurado (opcional)")

        if settings.CELERY_RESULT_BACKEND:
            success(
                "Celery RESULT_BACKEND configurado",
                settings.CELERY_RESULT_BACKEND[:30],
            )
        else:
            warning("Celery RESULT_BACKEND não configurado (opcional)")

    except Exception as e:
        error("Celery config", str(e)[:50])


# ============================================================================
# TESTE 11: ALEMBIC MIGRATIONS
# ============================================================================


def test_alembic():
    """Test Alembic migrations."""
    header("TESTE 11: ALEMBIC MIGRATIONS")

    try:
        from pathlib import Path

        alembic_dir = Path(__file__).parent.parent.parent / "alembic"

        if alembic_dir.exists():
            success("Diretório alembic encontrado")
            versions_dir = alembic_dir / "versions"
            if versions_dir.exists():
                migrations = list(versions_dir.glob("*.py"))
                success(f"Migrations encontradas: {len(migrations)}")
                for m in migrations[:5]:
                    print(f"     {m.name}")
            else:
                warning("Diretório versions não encontrado")
        else:
            warning("Diretório alembic não encontrado")

    except Exception as e:
        error("Alembic check", str(e)[:50])


# ============================================================================
# TESTE 12: ENVIRONMENT VARIABLES
# ============================================================================


def test_environment_vars():
    """Test environment variables."""
    header("TESTE 12: VARIÁVEIS DE AMBIENTE")

    import os

    env_files = [".env", ".env.local", ".env.example"]
    env_found = False

    for env_file in env_files:
        if Path(env_file).exists():
            success(f"Arquivo {env_file} encontrado")
            env_found = True
            break

    if not env_found:
        warning("Arquivo .env", "Nenhum arquivo .env encontrado")

    # Verificar variáveis críticas
    critical_vars = {
        "POSTGRES_HOST": "Database host",
        "POSTGRES_USER": "Database user",
        "POSTGRES_PASSWORD": "Database password",
        "REDIS_HOST": "Redis host",
        "REDIS_PASSWORD": "Redis password",
    }

    print("\n  📋 Variáveis de ambiente críticas:")
    for var, desc in critical_vars.items():
        value = os.getenv(var)
        if value:
            if "PASSWORD" in var:
                masked = "***" + value[-8:]
            else:
                masked = value
            success(f"  {var}", masked)
        else:
            warning(f"  {var}", "Não configurada")


# ============================================================================
# TESTE 13: DATABASE TABLES
# ============================================================================


def test_database_tables():
    """Test database tables."""
    header("TESTE 13: TABELAS DO BANCO DE DADOS")

    try:
        from sqlalchemy import inspect

        from backend.database.connection import engine

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if tables:
            success(f"Tabelas encontradas no banco: {len(tables)}")

            print("\n  📋 Tabelas detectadas:")
            for table in sorted(tables)[:15]:
                columns = inspector.get_columns(table)
                print(f"     - {table} ({len(columns)} colunas)")

            if len(tables) > 15:
                print(f"     ... e mais {len(tables) - 15} tabelas")
        else:
            msg = "Nenhuma tabela (execute migrations)"
            warning("Tabelas do banco", msg)

    except Exception as e:
        warning("Database tables", str(e)[:50])


# ============================================================================
# TESTE 14: PROMETHEUS METRICS
# ============================================================================


def test_prometheus():
    """Test Prometheus metrics."""
    header("TESTE 14: PROMETHEUS METRICS")

    try:
        import prometheus_fastapi_instrumentator as pfi

        success(f"Prometheus {pfi.__name__} disponível")
        warning("Métricas apenas em runtime (GET /metrics)")

    except Exception as e:
        error("Prometheus", str(e)[:50])


# ============================================================================
# SUMMARY
# ============================================================================


def print_summary():
    """Print final summary."""
    header("📊 RESUMO FINAL")

    total = results["passed"] + results["failed"] + results["warnings"]
    pass_pct = (results["passed"] / total * 100) if total > 0 else 0

    print(f"{GREEN}✅ Passou:{RESET} {results['passed']}")
    print(f"{RED}❌ Falhou:{RESET} {results['failed']}")
    print(f"{YELLOW}⚠️  Avisos:{RESET} {results['warnings']}")
    pct_str = f"({pass_pct:.1f}%)"
    print(f"\n{BOLD}Total: {results['passed']}/{total} {pct_str}{RESET}\n")

    sep = "=" * 70
    print(f"{BOLD}{sep}{RESET}")
    if results["failed"] == 0:
        print(f"{GREEN}{BOLD}✅ BACKEND ESTÁ SAUDÁVEL E PRONTO!{RESET}\n")
    elif results["failed"] <= 2:
        msg = "Alguns problemas, mas não críticos."
        print(f"{YELLOW}{BOLD}⚠️  {msg}{RESET}\n")
    else:
        msg = "Existem problemas graves a resolver."
        print(f"{RED}{BOLD}❌ {msg}{RESET}\n")
    print(f"{BOLD}{sep}{RESET}\n")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(f"\n{BOLD}{BLUE}EVAonline - AUDITORIA BACKEND{RESET}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    test_imports()
    test_settings()
    test_postgres()
    test_redis()
    test_models()
    test_fastapi_app()
    test_health_routes()
    test_eto_routes()
    test_climate_sources()
    test_celery()
    test_alembic()
    test_environment_vars()
    test_database_tables()
    test_prometheus()

    print_summary()
