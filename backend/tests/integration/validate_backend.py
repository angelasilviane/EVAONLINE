#!/usr/bin/env python3
"""Validação completa do backend - sem documentos, só testes."""
import sys
from pathlib import Path

# Adicionar raiz ao path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print("\n" + "=" * 80)
print("VALIDACAO COMPLETA DO BACKEND - EVAonline")
print("=" * 80)

# 1. BANCO DE DADOS
print("\n[1] VERIFICANDO BANCO DE DADOS")
print("-" * 80)
try:
    from backend.database.connection import engine
    import sqlalchemy as sa

    # Listar tabelas
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    print("OK Conexao PostgreSQL")
    print("OK Tabelas encontradas: {}".format(len(tables)))
    for table in sorted(tables):
        cols = len(inspector.get_columns(table))
        print("   • {} ({} colunas)".format(table, cols))
except Exception as e:
    print("ERRO BD: {}".format(str(e)[:100]))

# 2. REDIS
print("\n[2] VERIFICANDO REDIS")
print("-" * 80)
try:
    from backend.database.redis_pool import initialize_redis_pool

    redis_client = initialize_redis_pool()
    redis_client.ping()
    info = redis_client.info()
    print("OK Conexao Redis")
    print("OK Versao: {}".format(info.get("redis_version")))
    print("OK Memory used: {}".format(info.get("used_memory_human")))
    print("OK Connected clients: {}".format(info.get("connected_clients")))
except Exception as e:
    print("ERRO Redis: {}".format(str(e)[:100]))

# 3. FASTAPI ROUTES
print("\n[3] VERIFICANDO FASTAPI ROUTES")
print("-" * 80)
try:
    from backend.main import app

    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append((route.path, route.methods))
    print("OK FastAPI app carregado")
    print("OK Rotas registradas: {}".format(len(routes)))
    health_routes = [r for r in routes if "health" in r[0].lower()]
    print("OK Health routes: {}".format(len(health_routes)))
except Exception as e:
    print("ERRO FastAPI: {}".format(str(e)[:100]))

# 4. CELERY
print("\n[4] VERIFICANDO CELERY")
print("-" * 80)
try:
    from backend.infrastructure.celery.celery_config import celery_app

    print("OK Celery app carregado")
    print("OK Broker: {}...".format(celery_app.conf.broker_url[:50]))
    print("OK Backend: {}...".format(celery_app.conf.result_backend[:50]))
    tasks = list(celery_app.tasks.keys())
    print("OK Tasks registradas: {}".format(len(tasks)))
    for task in tasks[:3]:
        print("   • {}".format(task))
except Exception as e:
    print("ERRO Celery: {}".format(str(e)[:100]))

# 5. SETTINGS
print("\n[5] VERIFICANDO SETTINGS")
print("-" * 80)
try:
    from config.settings.app_config import get_legacy_settings

    settings = get_legacy_settings()
    print("OK Settings carregadas")
    print("   • API_V1_PREFIX: {}".format(settings.API_V1_PREFIX))
    print("   • POSTGRES_HOST: {}".format(settings.POSTGRES_HOST))
    print("   • REDIS_HOST: {}".format(settings.REDIS_HOST))
    print("   • DB Pool size: {}".format(settings.DB_POOL_SIZE))
except Exception as e:
    print("ERRO Settings: {}".format(str(e)[:100]))

# 6. MODELS
print("\n[6] VERIFICANDO MODELS")
print("-" * 80)
try:
    from backend.database import models

    model_classes = [attr for attr in dir(models) if not attr.startswith("_")]
    print("OK Models importados")
    print("OK Classes disponiveis: {}".format(len(model_classes)))
    for model in model_classes[:5]:
        print("   • {}".format(model))
except Exception as e:
    print("ERRO Models: {}".format(str(e)[:100]))

# 7. HEALTH CHECK
print("\n[7] TESTANDO HEALTH CHECK")
print("-" * 80)
try:
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health")
    print("OK Health check: {}".format(response.status_code))
    data = response.json()
    print("   • Status: {}".format(data.get("status")))
    print("   • API version: {}".format(data.get("api_version")))
except Exception as e:
    print("ERRO Health: {}".format(str(e)[:100]))

print("\n" + "=" * 80)
print("VALIDACAO CONCLUIDA")
print("=" * 80 + "\n")
