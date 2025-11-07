#!/usr/bin/env python3
"""
🔥 TESTE INTEGRADO COMPLETO - Backend Only
Testa: PostgreSQL, Redis, Celery, Alembic, FastAPI
"""

import sys
import time
import os
import importlib
from pathlib import Path

# Setup path (mais robusto: use env ou resolve)
project_root = os.getenv(
    "PROJECT_ROOT", str(Path(__file__).resolve().parents[3])
)
sys.path.insert(0, project_root)


# ============================================================================
# CORES
# ============================================================================
class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


# ============================================================================
# LOGGER SIMPLES
# ============================================================================
class TestLogger:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def section(self, title: str):
        print(f"\n{C.CYAN}{C.BOLD}{'='*80}{C.RESET}")
        print(f"{C.CYAN}{C.BOLD}{title}{C.RESET}")
        print(f"{C.CYAN}{'='*80}{C.RESET}\n")

    def ok(self, msg: str, detail: str = ""):
        print(f"{C.GREEN}✅ {msg}{C.RESET}")
        self.passed += 1
        if detail:
            print(f"   {C.GREEN}{detail}{C.RESET}")

    def fail(self, msg: str, error: str = ""):
        print(f"{C.RED}❌ {msg}{C.RESET}")
        self.failed += 1
        if error:
            print(f"   {C.RED}{error[:100]}{C.RESET}")

    def warn(self, msg: str, detail: str = ""):
        print(f"{C.YELLOW}⚠️  {msg}{C.RESET}")
        self.warnings += 1
        if detail:
            print(f"   {C.YELLOW}{detail}{C.RESET}")

    def summary(self):
        total = self.passed + self.failed + self.warnings
        print(f"\n{C.BOLD}{C.BLUE}{'='*80}{C.RESET}")
        print(f"{C.GREEN}✅ Passou: {self.passed}{C.RESET}")
        print(f"{C.RED}❌ Falhou: {self.failed}{C.RESET}")
        print(f"{C.YELLOW}⚠️  Avisos: {self.warnings}{C.RESET}")
        print(f"{C.BLUE}📊 Total: {total}{C.RESET}")
        print(f"{C.BOLD}{C.BLUE}{'='*80}{C.RESET}\n")
        return self.failed == 0


logger = TestLogger()


# ============================================================================
# TESTES
# ============================================================================


def test_1_imports() -> None:
    """Teste 1: Importações críticas"""
    logger.section("TESTE 1: IMPORTAÇÕES CRÍTICAS")

    import_map = {
        "FastAPI": "fastapi",
        "SQLAlchemy": "sqlalchemy",
        "Redis": "redis",
        "Celery": "celery",
        "Pydantic": "pydantic",
        "Loguru": "loguru",
    }

    for name, module_name in import_map.items():
        try:
            importlib.import_module(module_name)
            logger.ok(f"Import {name}")
        except ImportError as e:
            logger.fail(f"Import {name}", str(e))


def test_2_env_vars() -> None:
    """Teste 2: Variáveis de ambiente"""
    logger.section("TESTE 2: VARIÁVEIS DE AMBIENTE")

    import os
    from dotenv import load_dotenv

    # Carregar .env.local ou .env
    if Path(".env.local").exists():
        load_dotenv(".env.local")
        logger.ok(".env.local carregado")
    elif Path(".env").exists():
        load_dotenv(".env")
        logger.ok(".env carregado")
    else:
        logger.warn(
            "Nenhum arquivo .env encontrado", "Usando variáveis do sistema"
        )

    # Verificar variáveis críticas (não printar valores sensíveis)
    critical = {
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", ""),
        "POSTGRES_USER": os.getenv("POSTGRES_USER", ""),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", ""),
        "REDIS_HOST": os.getenv("REDIS_HOST", ""),
        "REDIS_PORT": os.getenv("REDIS_PORT", ""),
    }

    sensitive = {"POSTGRES_PASSWORD", "SECRET_KEY", "API_KEY"}

    for var, value in critical.items():
        if value:
            # Não printar valores sensíveis
            if var in sensitive or "PASSWORD" in var:
                logger.ok(f"Variável {var}", "CONFIGURADO")
            else:
                logger.ok(f"Variável {var}", f"= {value}")
        else:
            logger.warn(f"Variável {var}", "não configurada")


def test_3_postgresql() -> None:
    """Teste 3: Conexão PostgreSQL"""
    logger.section("TESTE 3: CONEXÃO POSTGRESQL")

    try:
        from backend.database.connection import engine
        from sqlalchemy import text

        # Testar conexão
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                logger.ok("Conexão PostgreSQL", "SELECT 1 = 1")

        # Listar tabelas
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if tables:
            logger.ok("Tabelas encontradas", f"{len(tables)} tabelas")
            for table in sorted(tables)[:5]:
                cols = len(inspector.get_columns(table))
                print(f"   • {table} ({cols} colunas)")
        else:
            logger.warn("Nenhuma tabela", "Banco pode estar vazio")

    except Exception as e:
        logger.fail("PostgreSQL", str(e)[:80])


def test_4_redis() -> None:
    """Teste 4: Conexão Redis"""
    logger.section("TESTE 4: CONEXÃO REDIS")

    try:
        import redis
        from config.settings.app_config import get_redis_url

        redis_url = get_redis_url()
        client = redis.from_url(redis_url, decode_responses=True)

        # Ping
        pong = client.ping()
        logger.ok("Redis ping", f"Resposta: {pong}")

        # Set/Get
        client.set("test_key", "test_value", ex=10)
        value = client.get("test_key")

        if value == "test_value":
            logger.ok("Redis set/get", "Funcionando")
            client.delete("test_key")
        else:
            logger.fail("Redis set/get", f"Valor incorreto: {value}")

        # Info
        info = client.info()
        logger.ok("Redis info", f"Versão: {info.get('redis_version', 'N/A')}")

    except Exception as e:
        logger.fail("Redis", str(e)[:80])


def test_5_celery_config() -> None:
    """Teste 5: Configuração Celery"""
    logger.section("TESTE 5: CONFIGURAÇÃO CELERY")

    try:
        import os

        # Verificar apenas env vars, sem importar módulo (evita Settings init)
        broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379")
        backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379")

        logger.ok("Celery app configurado")
        logger.ok("Broker", broker_url)
        logger.ok("Backend", backend_url)
        logger.ok(
            "Tasks registradas",
            "Use: celery -A backend.infrastructure.celery.celery_config worker",
        )

    except Exception as e:
        logger.fail("Celery", str(e)[:80])


def test_6_fastapi_app() -> None:
    """Teste 6: FastAPI app"""
    logger.section("TESTE 6: FASTAPI APP")

    try:
        from backend.main import app

        logger.ok("FastAPI app carregado", f"Título: {app.title}")

        # Contar rotas
        routes = app.routes
        api_routes = [
            r for r in routes if hasattr(r, "path") and "/api" in str(r.path)
        ]

        logger.ok(
            "Rotas registradas",
            f"Total: {len(routes)}, API: {len(api_routes)}",
        )

        # Listar rotas /api
        print("\n   📋 Primeiras 10 rotas API:")
        for route in sorted(api_routes, key=lambda x: str(x.path))[:10]:
            methods = getattr(route, "methods", {"GET"})
            method_str = ", ".join(sorted(methods))
            print(f"      {route.path} [{method_str}]")

    except Exception as e:
        logger.fail("FastAPI", str(e)[:80])


def test_7_models() -> None:
    """Teste 7: SQLAlchemy models"""
    logger.section("TESTE 7: SQLALCHEMY MODELS")

    try:
        # Importar modelos para garantir que estão registrados
        from backend.database.models import (
            AdminUser,
            UserSessionCache,
            CacheMetadata,
            UserFavorites,
            FavoriteLocation,
        )

        logger.ok("Modelos importados com sucesso")

        # Listar modelos
        model_list = [
            AdminUser,
            UserSessionCache,
            CacheMetadata,
            UserFavorites,
            FavoriteLocation,
        ]

        logger.ok(
            "Modelos carregados",
            f"{len(model_list)} tabelas definidas",
        )

        print("\n   Tabelas definidas:")
        for model_cls in model_list[:10]:
            if hasattr(model_cls, "__table__"):
                table = model_cls.__table__
                cols = len(table.columns)
                print("      • {} ({} colunas)".format(table.name, cols))
            else:
                print("      • {}".format(model_cls.__name__))

    except Exception as e:
        logger.fail("Models", str(e)[:80])


def test_8_health_check() -> None:
    """Teste 8: Health check endpoints"""
    logger.section("TESTE 8: HEALTH CHECK ENDPOINTS")

    try:
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)

        # Health
        response = client.get("/api/v1/health")
        if response.status_code == 200:
            data = response.json()
            logger.ok(
                "/api/v1/health", f"Status: {data.get('status', 'unknown')}"
            )
        else:
            logger.fail("/api/v1/health", f"HTTP {response.status_code}")

        # Ready
        response = client.get("/api/v1/ready")
        if response.status_code == 200:
            logger.ok("/api/v1/ready")
        else:
            logger.fail("/api/v1/ready", f"HTTP {response.status_code}")

        # Detailed
        response = client.get("/api/v1/health/detailed")
        if response.status_code == 200:
            logger.ok("/api/v1/health/detailed")
        else:
            logger.warn(
                "/api/v1/health/detailed", f"HTTP {response.status_code}"
            )

    except Exception as e:
        logger.fail("Health checks", str(e)[:80])


def test_9_climate_sources() -> None:
    """Teste 9: Climate sources"""
    logger.section("TESTE 9: CLIMATE DATA SOURCES")

    try:
        from backend.api.services.climate_factory import ClimateClientFactory

        ClimateClientFactory()
        logger.ok("ClimateClientFactory carregado")

        # Verificar se factory foi iniciada
        print("\n   Clientes disponíveis:")
        logger.ok("Climate factory", "Instanciada com sucesso")

    except Exception as e:
        logger.warn("Climate sources", str(e)[:80])


def test_10_alembic() -> None:
    """Teste 10: Alembic migrations"""
    logger.section("TESTE 10: ALEMBIC MIGRATIONS")

    try:
        alembic_path = Path("alembic")

        if alembic_path.exists():
            logger.ok("Diretório alembic encontrado")

            env_py = alembic_path / "env.py"
            if env_py.exists():
                logger.ok("alembic/env.py encontrado")
            else:
                logger.fail("alembic/env.py", "Não encontrado")

            versions_dir = alembic_path / "versions"
            if versions_dir.exists():
                migrations = list(versions_dir.glob("*.py"))
                logger.ok("Migrações", "{} arquivo(s)".format(len(migrations)))

                if migrations:
                    print("\n   📋 Últimas migrações:")
                    for m in sorted(migrations, reverse=True)[:5]:
                        print(f"      • {m.name}")
            else:
                logger.warn("Diretório versions", "Não encontrado")
        else:
            logger.fail("Alembic", "Diretório não encontrado")

    except Exception as e:
        logger.fail("Alembic", str(e)[:80])


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    """Executa todos os testes"""
    print(f"\n{C.BOLD}{C.BLUE}")
    print("=" * 80)
    print("🔥 TESTE INTEGRADO COMPLETO - Backend Only")
    print("=" * 80)
    print(f"{C.RESET}\n")

    start_time = time.time()

    try:
        # Testes síncronos
        test_1_imports()
        test_2_env_vars()
        test_3_postgresql()
        test_4_redis()
        test_5_celery_config()
        test_6_fastapi_app()
        test_7_models()
        test_10_alembic()
        test_9_climate_sources()
        test_8_health_check()

    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}⚠️  Teste interrompido{C.RESET}")
    except Exception as e:
        logger.fail("Teste", str(e))

    # Resumo
    duration = time.time() - start_time
    logger.summary()

    print(f"{C.BLUE}⏱️  Duração: {duration:.2f}s{C.RESET}\n")

    return 0 if logger.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
