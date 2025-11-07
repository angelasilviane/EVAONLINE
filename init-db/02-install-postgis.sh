#!/bin/bash
# ===========================================
# PostGIS Extension Installation Script
# ===========================================
# Este script instala a extensão PostGIS no banco de dados PostgreSQL
# durante a inicialização do container Docker.
#
# Executado automaticamente pelo entrypoint do container postgis/postgis
# após os scripts em /docker-entrypoint-initdb.d/

set -e

echo "================================================"
echo "Instalando extensão PostGIS..."
echo "================================================"

# Instala PostGIS no banco principal
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;

    -- Verifica versão instalada
    SELECT PostGIS_version();
EOSQL

echo "✅ PostGIS instalado com sucesso!"
echo "================================================"

# Lista todas as extensões instaladas
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "\dx"

echo "================================================"
echo "✅ Configuração PostGIS concluída!"
echo "================================================"
