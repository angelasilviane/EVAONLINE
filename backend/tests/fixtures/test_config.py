"""
Configuração centralizada para testes
"""

import os

# Detectar ambiente
TESTING_ENV = os.getenv("TESTING_ENV", "local")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "evaonline")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "evaonline")

# API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
METRICS_TOKEN = os.getenv("METRICS_TOKEN", "test-token-12345")

# Settings
TEST_RETRIES = 3
TEST_TIMEOUT = 10
