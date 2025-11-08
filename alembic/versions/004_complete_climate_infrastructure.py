"""Complete climate infrastructure with all tables

Revision ID: 004_complete_climate_infrastructure
Revises:
Create Date: 2025-11-07

Esta migração consolida TODA a infraestrutura necessária:
- Schema climate_history
- Tabela climate_data (dados multi-API com JSONB)
- Tabela api_variables (metadados das APIs)
- Tabelas do climate_history (studied_cities, monthly_climate_normals, weather_stations, city_nearby_stations)
- Tabelas administrativas (admin_users, cache, visitor_stats, eto_results)
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004_climate_infra"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria toda a infraestrutura do zero."""

    # ========================================
    # 1. CRIAR SCHEMA CLIMATE_HISTORY
    # ========================================
    op.execute("CREATE SCHEMA IF NOT EXISTS climate_history")

    # ========================================
    # 2. TABELAS ADMINISTRATIVAS (PUBLIC)
    # ========================================

    # Tabela de administradores
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("is_superuser", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_login", sa.DateTime, nullable=True),
    )

    # Tabela de cache de usuário
    op.create_table(
        "user_cache",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("cache_key", sa.String(255), nullable=False),
        sa.Column("cache_data", postgresql.JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )
    op.create_index(
        "idx_user_cache_user_key", "user_cache", ["user_id", "cache_key"]
    )
    op.create_index("idx_user_cache_expires", "user_cache", ["expires_at"])

    # Tabela de favoritos
    op.create_table(
        "user_favorites",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("city_name", sa.String(255), nullable=False),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_user_favorites_user", "user_favorites", ["user_id"])

    # Tabela de estatísticas de visitantes
    op.create_table(
        "visitor_stats",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("page_path", sa.String(255), nullable=True),
        sa.Column("referrer", sa.String(500), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column(
            "visited_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_visitor_stats_session", "visitor_stats", ["session_id"]
    )
    op.create_index("idx_visitor_stats_date", "visitor_stats", ["visited_at"])

    # Tabela de resultados de ETO (legado)
    op.create_table(
        "eto_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("eto_mm_day", sa.Float, nullable=True),
        sa.Column("method", sa.String(50), nullable=True),
        sa.Column("temperature_max", sa.Float, nullable=True),
        sa.Column("temperature_min", sa.Float, nullable=True),
        sa.Column("humidity", sa.Float, nullable=True),
        sa.Column("wind_speed", sa.Float, nullable=True),
        sa.Column("solar_radiation", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_eto_results_location_date",
        "eto_results",
        ["latitude", "longitude", "date"],
    )

    # ========================================
    # 3. TABELAS DE DADOS CLIMÁTICOS (PUBLIC)
    # ========================================

    # Tabela principal de dados climáticos (multi-API com JSONB)
    op.create_table(
        "climate_data",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "source_api",
            sa.String(50),
            nullable=False,
            comment="nasa_power, openmeteo, nws, met_norway",
        ),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column(
            "raw_data",
            postgresql.JSONB,
            nullable=False,
            comment="Dados brutos da API original",
        ),
        sa.Column(
            "harmonized_data",
            postgresql.JSONB,
            nullable=True,
            comment="Dados normalizados para formato padrão",
        ),
        sa.Column(
            "eto_mm_day",
            sa.Float,
            nullable=True,
            comment="ETO calculado em mm/dia",
        ),
        sa.Column(
            "eto_method",
            sa.String(50),
            nullable=True,
            comment="Método usado: penman_monteith, hargreaves",
        ),
        sa.Column(
            "quality_score",
            sa.Float,
            nullable=True,
            comment="Score de qualidade 0-1",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_api",
            "latitude",
            "longitude",
            "date",
            name="uq_climate_data_location_date",
        ),
    )

    # Índices para climate_data
    op.create_index("idx_climate_data_source", "climate_data", ["source_api"])
    op.create_index(
        "idx_climate_data_location", "climate_data", ["latitude", "longitude"]
    )
    op.create_index("idx_climate_data_date", "climate_data", ["date"])
    op.create_index(
        "idx_climate_data_source_date", "climate_data", ["source_api", "date"]
    )

    # Tabela de variáveis das APIs (metadados)
    op.create_table(
        "api_variables",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "api_name",
            sa.String(50),
            nullable=False,
            comment="nasa_power, openmeteo_archive, etc",
        ),
        sa.Column(
            "variable_name",
            sa.String(100),
            nullable=False,
            comment="Nome original da variável na API",
        ),
        sa.Column(
            "unit", sa.String(50), nullable=True, comment="Unidade de medida"
        ),
        sa.Column(
            "description",
            sa.Text,
            nullable=True,
            comment="Descrição da variável",
        ),
        sa.Column(
            "mapping",
            sa.String(100),
            nullable=True,
            comment="Nome harmonizado: temp_max_celsius, humidity_percent, etc",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "api_name", "variable_name", name="uq_api_variable"
        ),
    )

    # Índices para api_variables
    op.create_index("idx_api_variables_api", "api_variables", ["api_name"])
    op.create_index("idx_api_variables_mapping", "api_variables", ["mapping"])

    # ========================================
    # 4. SCHEMA CLIMATE_HISTORY
    # ========================================

    # Tabela de cidades estudadas
    op.create_table(
        "studied_cities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("city_name", sa.String(150), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("state_province", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("elevation_m", sa.Float, nullable=True),
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326),
            nullable=False,
            comment="Coordenadas geográficas PostGIS",
        ),
        sa.Column("timezone", sa.String(50), nullable=True),
        sa.Column(
            "data_sources",
            postgresql.JSONB,
            nullable=True,
            comment="Array de fontes de dados disponíveis",
        ),
        sa.Column(
            "reference_periods",
            postgresql.JSONB,
            nullable=False,
            comment="Períodos de referência: {1991-2020: true, 1981-2010: true}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "city_name", "latitude", "longitude", name="uq_studied_city"
        ),
        schema="climate_history",
    )

    # Índices para studied_cities (COM IF NOT EXISTS para evitar erro de duplicação)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_studied_cities_location "
        "ON climate_history.studied_cities USING gist (location)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_studied_cities_city_country "
        "ON climate_history.studied_cities (city_name, country)"
    )

    # Tabela de normais climatológicas mensais
    op.create_table(
        "monthly_climate_normals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "city_id",
            sa.Integer,
            sa.ForeignKey(
                "climate_history.studied_cities.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "period_key",
            sa.String(20),
            nullable=False,
            comment="1991-2020, 1981-2010",
        ),
        sa.Column("month", sa.Integer, nullable=False, comment="1-12"),
        sa.Column(
            "temp_max_avg",
            sa.Float,
            nullable=True,
            comment="Temperatura máxima média (°C)",
        ),
        sa.Column(
            "temp_min_avg",
            sa.Float,
            nullable=True,
            comment="Temperatura mínima média (°C)",
        ),
        sa.Column(
            "temp_mean_avg",
            sa.Float,
            nullable=True,
            comment="Temperatura média (°C)",
        ),
        sa.Column(
            "precipitation_mm",
            sa.Float,
            nullable=True,
            comment="Precipitação total (mm)",
        ),
        sa.Column(
            "humidity_percent",
            sa.Float,
            nullable=True,
            comment="Umidade relativa média (%)",
        ),
        sa.Column(
            "wind_speed_ms",
            sa.Float,
            nullable=True,
            comment="Velocidade do vento (m/s)",
        ),
        sa.Column(
            "radiation_mj_m2",
            sa.Float,
            nullable=True,
            comment="Radiação solar (MJ/m²/dia)",
        ),
        sa.Column(
            "eto_mm_day",
            sa.Float,
            nullable=True,
            comment="ETO médio mensal (mm/dia)",
        ),
        sa.Column(
            "data_source",
            sa.String(100),
            nullable=True,
            comment="Fonte dos dados",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "city_id", "period_key", "month", name="uq_monthly_normals"
        ),
        schema="climate_history",
    )

    # Índices para monthly_climate_normals
    op.create_index(
        "idx_monthly_normals_city_month",
        "monthly_climate_normals",
        ["city_id", "month"],
        schema="climate_history",
    )
    op.create_index(
        "idx_monthly_normals_city_period",
        "monthly_climate_normals",
        ["city_id", "period_key"],
        schema="climate_history",
    )

    # Tabela de estações meteorológicas próximas
    op.create_table(
        "weather_stations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("station_name", sa.String(150), nullable=True),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("elevation_m", sa.Float, nullable=True),
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326),
            nullable=False,
        ),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column(
            "data_provider",
            sa.String(100),
            nullable=True,
            comment="WMO, INMET, etc",
        ),
        sa.Column(
            "station_type",
            sa.String(50),
            nullable=True,
            comment="automatic, conventional",
        ),
        sa.Column(
            "available_variables",
            postgresql.JSONB,
            nullable=True,
            comment="Lista de variáveis disponíveis",
        ),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="climate_history",
    )

    # Índices para weather_stations
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_weather_stations_location "
        "ON climate_history.weather_stations USING gist (location)"
    )
    op.create_index(
        "idx_weather_stations_country",
        "weather_stations",
        ["country"],
        schema="climate_history",
    )

    # Tabela de associação cidade-estação
    op.create_table(
        "city_nearby_stations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "city_id",
            sa.Integer,
            sa.ForeignKey(
                "climate_history.studied_cities.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "station_id",
            sa.Integer,
            sa.ForeignKey(
                "climate_history.weather_stations.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "distance_km", sa.Float, nullable=False, comment="Distância em km"
        ),
        sa.Column(
            "is_primary",
            sa.Boolean,
            default=False,
            comment="Estação primária para a cidade",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("city_id", "station_id", name="uq_city_station"),
        schema="climate_history",
    )

    # Índices para city_nearby_stations
    op.create_index(
        "idx_city_nearby_stations_city",
        "city_nearby_stations",
        ["city_id"],
        schema="climate_history",
    )
    op.create_index(
        "idx_city_nearby_stations_distance",
        "city_nearby_stations",
        ["city_id", "distance_km"],
        schema="climate_history",
    )

    # ========================================
    # MENSAGEM DE SUCESSO
    # ========================================
    print("\n" + "=" * 80)
    print("✅ MIGRAÇÃO COMPLETA EXECUTADA COM SUCESSO!")
    print("=" * 80)
    print("\n📊 TABELAS CRIADAS:")
    print("\n  PUBLIC SCHEMA:")
    print("    ✅ admin_users")
    print("    ✅ user_cache")
    print("    ✅ user_favorites")
    print("    ✅ visitor_stats")
    print("    ✅ eto_results")
    print("    ✅ climate_data (multi-API com JSONB)")
    print("    ✅ api_variables (metadados)")
    print("\n  CLIMATE_HISTORY SCHEMA:")
    print("    ✅ studied_cities (27 cidades)")
    print("    ✅ monthly_climate_normals")
    print("    ✅ weather_stations")
    print("    ✅ city_nearby_stations")
    print("\n📝 PRÓXIMOS PASSOS:")
    print(
        "    1. Popular api_variables: python scripts/populate_api_variables.py"
    )
    print(
        "    2. Importar histórico: python scripts/import_historical_reports.py"
    )
    print("    3. Testar APIs: python scripts/test_api_integration.py")
    print("=" * 80 + "\n")


def downgrade() -> None:
    """Remove toda a infraestrutura."""

    # Remover schema climate_history (CASCADE remove todas as tabelas)
    op.execute("DROP SCHEMA IF EXISTS climate_history CASCADE")

    # Remover tabelas do schema public
    op.drop_table(
        "city_nearby_stations", schema="climate_history", if_exists=True
    )
    op.drop_table("weather_stations", schema="climate_history", if_exists=True)
    op.drop_table(
        "monthly_climate_normals", schema="climate_history", if_exists=True
    )
    op.drop_table("studied_cities", schema="climate_history", if_exists=True)

    op.drop_table("api_variables", if_exists=True)
    op.drop_table("climate_data", if_exists=True)
    op.drop_table("eto_results", if_exists=True)
    op.drop_table("visitor_stats", if_exists=True)
    op.drop_table("user_favorites", if_exists=True)
    op.drop_table("user_cache", if_exists=True)
    op.drop_table("admin_users", if_exists=True)

    print("\n❌ Todas as tabelas foram removidas.")
