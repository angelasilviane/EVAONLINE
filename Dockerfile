# ===========================================
# MULTI-STAGE DOCKERFILE - EVAonline OTIMIZADO
# Usa pyproject.toml como única fonte de dependências
# ===========================================

# ===========================================
# Stage 1: Builder - Production Dependencies
# ===========================================
FROM python:3.12-slim AS builder-prod

# Metadata para melhor rastreabilidade da imagem
LABEL maintainer="Ângela Cunha Soares <angelassilviane@gmail.com>"
LABEL stage="builder-prod"
LABEL description="Builder stage for production dependencies"

# Configurar diretório de trabalho para o build
WORKDIR /build

# Instalar dependências de compilação PRIMEIRO
# Isso é ESSENCIAL para compilar pacotes como psycopg2, pandas, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar APENAS pyproject.toml primeiro para otimizar cache
# Se pyproject.toml não mudar, o cache é reutilizado
COPY pyproject.toml .

# Instalar projeto e dependências de produção do pyproject.toml
# --user instala no diretório do usuário para fácil cópia entre stages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user .

# ===========================================
# Stage 1B: Builder - Development Dependencies
# ===========================================
FROM builder-prod AS builder-dev

LABEL stage="builder-dev"

# Instalar dependências de desenvolvimento do pyproject.toml
# [dev] refere-se à seção project.optional-dependencies no pyproject.toml
RUN pip install --no-cache-dir --user .[dev]

# ===========================================
# Stage 2: Runtime (Production) - IMAGEM FINAL LEVE
# ===========================================
FROM python:3.12-slim AS runtime

# Metadata da imagem final
LABEL maintainer="Ângela Cunha Soares <angelassilviane@gmail.com>"
LABEL stage="runtime"
LABEL description="Production runtime image for EVAonline"

# Instalar APENAS dependências essenciais de runtime
# Removemos build-essential, gcc, g++ para imagem mais segura e leve
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Para health checks e wait-for-service
    netcat-traditional \
    # Cliente PostgreSQL
    libpq5 \
    # Para health checks
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 -s /bin/bash evaonline

# Configurar variáveis de ambiente para otimização Python
# Logs em tempo real
ENV PYTHONUNBUFFERED=1 \
    # Não criar arquivos .pyc
    PYTHONDONTWRITEBYTECODE=1 \
    # Path para imports
    PYTHONPATH=/app \
    # Incluir .local/bin no PATH
    PATH="/home/evaonline/.local/bin:${PATH}" \
    # Timezone padrão
    TZ=America/Sao_Paulo

WORKDIR /app

#  Criar diretórios ANTES de copiar arquivos
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R evaonline:evaonline /app

# Copiar APENAS dependências do builder de produção
# Isso evita ferramentas de desenvolvimento na imagem final
COPY --from=builder-prod --chown=evaonline:evaonline /root/.local /home/evaonline/.local

# Copiar entrypoint do local correto
COPY --chown=evaonline:evaonline docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copiar código em ordem estratégica para cache
# Arquivos que mudam pouco primeiro (melhor cache)
COPY --chown=evaonline:evaonline pyproject.toml .
COPY --chown=evaonline:evaonline alembic.ini .
COPY --chown=evaonline:evaonline pytest.ini .

# Arquivos que mudam com média frequência
COPY --chown=evaonline:evaonline config/ ./config/
COPY --chown=evaonline:evaonline alembic/ ./alembic/
COPY --chown=evaonline:evaonline shared_utils/ ./shared_utils/

# Arquivos que mudam frequentemente (últimos - pior cache)
COPY --chown=evaonline:evaonline backend/ ./backend/
COPY --chown=evaonline:evaonline frontend/ ./frontend/

# Mudar para usuário não-root para segurança
USER evaonline

# Expor porta padrão da aplicação
EXPOSE 8000

# Health check para monitoramento de saúde do container
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Entrypoint para inicialização flexível
ENTRYPOINT ["/entrypoint.sh"]

# ===========================================
# Stage 3: Development - Hot Reload e Debug
# ===========================================
FROM runtime AS development

LABEL stage="development"
LABEL description="Development image com hot-reload"

# Copiar dependências de desenvolvimento SOBRESCREVENDO produção
# Isso adiciona pytest, black, ruff, etc. sem afetar o stage runtime
COPY --from=builder-dev --chown=evaonline:evaonline /root/.local /home/evaonline/.local

USER evaonline

# Variáveis de ambiente para desenvolvimento
# Ativar hot-reload
ENV RELOAD=true \
    # Ambiente desenvolvimento
    ENVIRONMENT=development \
    # Logs detalhados
    LOG_LEVEL=DEBUG

# Comando padrão para desenvolvimento com hot-reload
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ===========================================
# Stage 4: Testing - Ambiente de Testes
# ===========================================
FROM development AS testing

LABEL stage="testing"
LABEL description="Testing image com pytest"

# Instalar ferramentas adicionais para testes ANTES de trocar user
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-traditional \
    redis-tools \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

USER evaonline

# Copiar testes
COPY --chown=evaonline:evaonline backend/tests/ ./backend/tests/

# Copiar entrypoint dos testes
COPY --chown=evaonline:evaonline docker/docker-entrypoint-tests.sh /entrypoint-tests.sh
RUN chmod +x /entrypoint-tests.sh

# Variáveis de ambiente para testes
ENV ENVIRONMENT=testing \
    TESTING=true

# Entrypoint para execução de testes
ENTRYPOINT ["/entrypoint-tests.sh"]
