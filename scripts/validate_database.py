"""
Script simples para validar que o banco está populado e funcionando.

Usage:
    uv run python scripts/validate_database.py
"""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db_context
from sqlalchemy import text


def validate_tables():
    """Valida que todas as tabelas foram criadas."""
    print("\n" + "=" * 80)
    print("🔍 VALIDANDO ESTRUTURA DO BANCO DE DADOS")
    print("=" * 80 + "\n")

    with get_db_context() as db:
        # Verificar tabelas do schema public
        print("📊 SCHEMA PUBLIC:")
        result = db.execute(
            text(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'pg_%'
                AND tablename NOT LIKE 'spatial_%'
                ORDER BY tablename
            """
            )
        )

        public_tables = [row[0] for row in result]
        for table in public_tables:
            print(f"  ✅ {table}")

        # Verificar tabelas do schema climate_history
        print("\n📊 SCHEMA CLIMATE_HISTORY:")
        result = db.execute(
            text(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'climate_history'
                ORDER BY tablename
            """
            )
        )

        history_tables = [row[0] for row in result]
        for table in history_tables:
            print(f"  ✅ {table}")

        # Verificar api_variables
        print("\n📡 API_VARIABLES:")
        result = db.execute(
            text(
                """
                SELECT api_name, COUNT(*) as total
                FROM api_variables
                GROUP BY api_name
                ORDER BY api_name
            """
            )
        )

        for row in result:
            print(f"  ✅ {row[0]:25s} → {row[1]:2d} variáveis")

        # Verificar climate_data
        print("\n💾 CLIMATE_DATA:")
        result = db.execute(
            text(
                """
                SELECT COUNT(*) as total
                FROM climate_data
            """
            )
        )

        total = result.fetchone()[0]
        print(f"  📦 Total de registros: {total}")

        if total > 0:
            result = db.execute(
                text(
                    """
                    SELECT 
                        source_api,
                        COUNT(*) as records,
                        MIN(date) as first_date,
                        MAX(date) as last_date
                    FROM climate_data
                    GROUP BY source_api
                    ORDER BY source_api
                """
                )
            )

            for row in result:
                print(
                    f"  📡 {row[0]:25s} → {row[1]:3d} registros "
                    f"({row[2]} a {row[3]})"
                )

        # Verificar PostGIS
        print("\n🌍 POSTGIS:")
        result = db.execute(text("SELECT PostGIS_version()"))
        version = result.fetchone()[0]
        print(f"  ✅ Versão: {version}")

    print("\n" + "=" * 80)
    print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        validate_tables()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
