"""
Script para popular tabela api_variables com metadados das 6 APIs climáticas.

Este script insere informações sobre todas as variáveis disponíveis
em cada API, incluindo nome original, unidade de medida, descrição
e mapeamento harmonizado.

APIs suportadas:
- NASA POWER
- Open-Meteo Archive
- Open-Meteo Forecast
- NWS Forecast
- NWS Stations
- MET Norway

Usage:
    uv run python scripts/populate_api_variables.py
"""

import sys
from pathlib import Path
from backend.database.connection import get_db_context
from sqlalchemy import text

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def populate_api_variables():
    """Popula tabela api_variables com metadados de todas as APIs."""

    # Definir variáveis de cada API com seus metadados
    variables = [
        # =====================================================
        # NASA POWER API
        # =====================================================
        {
            "api_name": "nasa_power",
            "variable_name": "T2M_MAX",
            "unit": "°C",
            "description": "Temperatura máxima a 2 metros",
            "mapping": "temp_max_celsius",
        },
        {
            "api_name": "nasa_power",
            "variable_name": "T2M_MIN",
            "unit": "°C",
            "description": "Temperatura mínima a 2 metros",
            "mapping": "temp_min_celsius",
        },
        {
            "api_name": "nasa_power",
            "variable_name": "T2M",
            "unit": "°C",
            "description": "Temperatura média a 2 metros",
            "mapping": "temp_mean_celsius",
        },
        {
            "api_name": "nasa_power",
            "variable_name": "RH2M",
            "unit": "%",
            "description": "Umidade relativa a 2 metros",
            "mapping": "humidity_percent",
        },
        {
            "api_name": "nasa_power",
            "variable_name": "WS2M",
            "unit": "m/s",
            "description": "Velocidade do vento a 2 metros",
            "mapping": "wind_speed_ms",
        },
        {
            "api_name": "nasa_power",
            "variable_name": "ALLSKY_SFC_SW_DWN",
            "unit": "MJ/m²/dia",
            "description": "Radiação solar de onda curta incidente na superfície",
            "mapping": "radiation_mj_m2",
        },
        {
            "api_name": "nasa_power",
            "variable_name": "PRECTOTCORR",
            "unit": "mm/dia",
            "description": "Precipitação total corrigida",
            "mapping": "precipitation_mm",
        },
        # =====================================================
        # OPEN-METEO ARCHIVE (Dados Históricos)
        # =====================================================
        {
            "api_name": "openmeteo_archive",
            "variable_name": "temperature_2m_max",
            "unit": "°C",
            "description": "Temperatura máxima diária a 2m",
            "mapping": "temp_max_celsius",
        },
        {
            "api_name": "openmeteo_archive",
            "variable_name": "temperature_2m_min",
            "unit": "°C",
            "description": "Temperatura mínima diária a 2m",
            "mapping": "temp_min_celsius",
        },
        {
            "api_name": "openmeteo_archive",
            "variable_name": "temperature_2m_mean",
            "unit": "°C",
            "description": "Temperatura média diária a 2m",
            "mapping": "temp_mean_celsius",
        },
        {
            "api_name": "openmeteo_archive",
            "variable_name": "relative_humidity_2m_mean",
            "unit": "%",
            "description": "Umidade relativa média a 2m",
            "mapping": "humidity_percent",
        },
        {
            "api_name": "openmeteo_archive",
            "variable_name": "wind_speed_10m_mean",
            "unit": "m/s",
            "description": "Velocidade média do vento a 10m",
            "mapping": "wind_speed_ms",
        },
        {
            "api_name": "openmeteo_archive",
            "variable_name": "shortwave_radiation_sum",
            "unit": "MJ/m²",
            "description": "Radiação solar de onda curta total diária",
            "mapping": "radiation_mj_m2",
        },
        {
            "api_name": "openmeteo_archive",
            "variable_name": "precipitation_sum",
            "unit": "mm",
            "description": "Precipitação total diária",
            "mapping": "precipitation_mm",
        },
        {
            "api_name": "openmeteo_archive",
            "variable_name": "et0_fao_evapotranspiration",
            "unit": "mm",
            "description": "ETO FAO-56 Penman-Monteith",
            "mapping": "eto_mm_day",
        },
        # =====================================================
        # OPEN-METEO FORECAST (Previsão)
        # =====================================================
        {
            "api_name": "openmeteo_forecast",
            "variable_name": "temperature_2m_max",
            "unit": "°C",
            "description": "Temperatura máxima prevista a 2m",
            "mapping": "temp_max_celsius",
        },
        {
            "api_name": "openmeteo_forecast",
            "variable_name": "temperature_2m_min",
            "unit": "°C",
            "description": "Temperatura mínima prevista a 2m",
            "mapping": "temp_min_celsius",
        },
        {
            "api_name": "openmeteo_forecast",
            "variable_name": "relative_humidity_2m",
            "unit": "%",
            "description": "Umidade relativa prevista a 2m",
            "mapping": "humidity_percent",
        },
        {
            "api_name": "openmeteo_forecast",
            "variable_name": "wind_speed_10m",
            "unit": "m/s",
            "description": "Velocidade do vento prevista a 10m",
            "mapping": "wind_speed_ms",
        },
        {
            "api_name": "openmeteo_forecast",
            "variable_name": "shortwave_radiation",
            "unit": "W/m²",
            "description": "Radiação solar de onda curta prevista",
            "mapping": "radiation_w_m2",
        },
        {
            "api_name": "openmeteo_forecast",
            "variable_name": "precipitation",
            "unit": "mm",
            "description": "Precipitação prevista",
            "mapping": "precipitation_mm",
        },
        {
            "api_name": "openmeteo_forecast",
            "variable_name": "et0_fao_evapotranspiration",
            "unit": "mm",
            "description": "ETO FAO-56 previsto",
            "mapping": "eto_mm_day",
        },
        # =====================================================
        # NWS FORECAST (National Weather Service - EUA)
        # =====================================================
        {
            "api_name": "nws_forecast",
            "variable_name": "temperature",
            "unit": "°C",
            "description": "Temperatura prevista",
            "mapping": "temp_celsius",
        },
        {
            "api_name": "nws_forecast",
            "variable_name": "relativeHumidity",
            "unit": "%",
            "description": "Umidade relativa prevista",
            "mapping": "humidity_percent",
        },
        {
            "api_name": "nws_forecast",
            "variable_name": "windSpeed",
            "unit": "m/s",
            "description": "Velocidade do vento prevista",
            "mapping": "wind_speed_ms",
        },
        {
            "api_name": "nws_forecast",
            "variable_name": "windDirection",
            "unit": "graus",
            "description": "Direção do vento",
            "mapping": "wind_direction_deg",
        },
        {
            "api_name": "nws_forecast",
            "variable_name": "precipitationProbability",
            "unit": "%",
            "description": "Probabilidade de precipitação",
            "mapping": "precipitation_probability",
        },
        # =====================================================
        # NWS STATIONS (Estações Meteorológicas - EUA)
        # =====================================================
        {
            "api_name": "nws_stations",
            "variable_name": "temperature",
            "unit": "°C",
            "description": "Temperatura observada",
            "mapping": "temp_celsius",
        },
        {
            "api_name": "nws_stations",
            "variable_name": "relativeHumidity",
            "unit": "%",
            "description": "Umidade relativa observada",
            "mapping": "humidity_percent",
        },
        {
            "api_name": "nws_stations",
            "variable_name": "windSpeed",
            "unit": "m/s",
            "description": "Velocidade do vento observada",
            "mapping": "wind_speed_ms",
        },
        {
            "api_name": "nws_stations",
            "variable_name": "windDirection",
            "unit": "graus",
            "description": "Direção do vento observada",
            "mapping": "wind_direction_deg",
        },
        {
            "api_name": "nws_stations",
            "variable_name": "barometricPressure",
            "unit": "Pa",
            "description": "Pressão atmosférica",
            "mapping": "pressure_pa",
        },
        # =====================================================
        # MET NORWAY (Instituto Meteorológico Norueguês)
        # =====================================================
        {
            "api_name": "met_norway",
            "variable_name": "air_temperature",
            "unit": "°C",
            "description": "Temperatura do ar",
            "mapping": "temp_celsius",
        },
        {
            "api_name": "met_norway",
            "variable_name": "relative_humidity",
            "unit": "%",
            "description": "Umidade relativa",
            "mapping": "humidity_percent",
        },
        {
            "api_name": "met_norway",
            "variable_name": "wind_speed",
            "unit": "m/s",
            "description": "Velocidade do vento",
            "mapping": "wind_speed_ms",
        },
        {
            "api_name": "met_norway",
            "variable_name": "wind_from_direction",
            "unit": "graus",
            "description": "Direção de origem do vento",
            "mapping": "wind_direction_deg",
        },
        {
            "api_name": "met_norway",
            "variable_name": "cloud_area_fraction",
            "unit": "%",
            "description": "Fração de área com nuvens",
            "mapping": "cloud_cover_percent",
        },
    ]

    print("\n" + "=" * 80)
    print("🌍 POPULANDO TABELA API_VARIABLES")
    print("=" * 80)

    with get_db_context() as db:
        inserted = 0
        skipped = 0

        for var in variables:
            try:
                # Inserir com ON CONFLICT DO NOTHING para evitar duplicatas
                result = db.execute(
                    text(
                        """
                        INSERT INTO api_variables 
                        (api_name, variable_name, unit, description, mapping)
                        VALUES 
                        (:api_name, :variable_name, :unit, :description, :mapping)
                        ON CONFLICT (api_name, variable_name) DO NOTHING
                        RETURNING id
                    """
                    ),
                    var,
                )

                if result.fetchone():
                    inserted += 1
                    print(
                        f"  ✅ {var['api_name']}.{var['variable_name']} → {var['mapping']}"
                    )
                else:
                    skipped += 1
                    print(
                        f"  ⏭️  {var['api_name']}.{var['variable_name']} (já existe)"
                    )

            except Exception as e:
                print(
                    f"  ❌ Erro ao inserir {var['api_name']}.{var['variable_name']}: {e}"
                )

        db.commit()

    print("\n" + "=" * 80)
    print(f"✅ POPULAÇÃO CONCLUÍDA!")
    print(f"   📊 Inseridas: {inserted} variáveis")
    print(f"   ⏭️  Ignoradas: {skipped} (já existentes)")
    print(f"   📦 Total: {len(variables)} variáveis definidas")
    print("=" * 80 + "\n")

    # Mostrar resumo por API
    print("\n📋 RESUMO POR API:")
    print("-" * 80)

    with get_db_context() as db:
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
            print(f"  📡 {row.api_name:25s} → {row.total:2d} variáveis")

    print("-" * 80 + "\n")


if __name__ == "__main__":
    try:
        populate_api_variables()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
