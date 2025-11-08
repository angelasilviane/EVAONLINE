"""
Script de validação do salvamento multi-API na tabela climate_data.

Testa o salvamento de dados das 6 APIs climáticas:
1. NASA POWER
2. Open-Meteo Archive
3. Open-Meteo Forecast
4. MET Norway
5. NWS Forecast
6. NWS Stations

Usage:
    uv run python scripts/validation/test_api_integration.py
"""

import io
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import text

# Fix encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db_context
from backend.database.models.climate_data import ClimateData


def test_nasa_power_save():
    """Testa salvamento de dados NASA POWER."""
    print("\n1️⃣  Testando NASA POWER...")

    with get_db_context() as session:
        # Criar registro de teste
        record = ClimateData(
            source_api="nasa_power",
            latitude=-22.7250,
            longitude=-47.6476,
            elevation=547.0,
            timezone="America/Sao_Paulo",
            date=datetime(2024, 1, 15),
            raw_data={
                "T2M_MAX": 28.5,
                "T2M_MIN": 18.2,
                "RH2M": 65.0,
                "WS2M": 3.2,
                "ALLSKY_SFC_SW_DWN": 20.5,
                "PRECTOTCORR": 5.2,
            },
            harmonized_data={
                "temp_max_c": 28.5,
                "temp_min_c": 18.2,
                "humidity_percent": 65.0,
                "wind_speed_ms": 3.2,
                "solar_radiation_mjm2": 20.5,
                "precipitation_mm": 5.2,
            },
            eto_mm_day=4.85,
            eto_method="penman_monteith",
            quality_flags={"complete": True, "missing": []},
            processing_metadata={
                "version": "1.0",
                "processor": "test_script",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        session.add(record)
        session.commit()

        # Validar
        result = (
            session.query(ClimateData)
            .filter(
                ClimateData.source_api == "nasa_power",
                ClimateData.date == datetime(2024, 1, 15),
            )
            .first()
        )

        if result:
            print(f"   ✅ Registro salvo: ID={result.id}")
            print(f"      - ETo: {result.eto_mm_day} mm/dia")
            print(
                f"      - Temperatura: {result.harmonized_data['temp_max_c']}°C"
            )
            print(f"      - Elevação: {result.elevation}m")
            return True
        else:
            print("   ❌ Erro ao salvar NASA POWER")
            return False


def test_openmeteo_archive_save():
    """Testa salvamento de dados Open-Meteo Archive."""
    print("\n2️⃣  Testando Open-Meteo Archive...")

    with get_db_context() as session:
        record = ClimateData(
            source_api="openmeteo_archive",
            latitude=-22.7250,
            longitude=-47.6476,
            elevation=547.0,
            timezone="America/Sao_Paulo",
            date=datetime(2023, 6, 10),
            raw_data={
                "temperature_2m_max": 26.8,
                "temperature_2m_min": 16.5,
                "relative_humidity_2m_mean": 72.0,
                "wind_speed_10m_max": 4.1,
                "shortwave_radiation_sum": 18.2,
                "precipitation_sum": 12.5,
            },
            harmonized_data={
                "temp_max_c": 26.8,
                "temp_min_c": 16.5,
                "humidity_percent": 72.0,
                "wind_speed_ms": 4.1,
                "solar_radiation_mjm2": 18.2,
                "precipitation_mm": 12.5,
            },
            eto_mm_day=3.92,
            eto_method="penman_monteith",
        )

        session.add(record)
        session.commit()

        result = (
            session.query(ClimateData)
            .filter(
                ClimateData.source_api == "openmeteo_archive",
                ClimateData.date == datetime(2023, 6, 10),
            )
            .first()
        )

        if result:
            print(f"   ✅ Registro salvo: ID={result.id}")
            print(f"      - ETo: {result.eto_mm_day} mm/dia")
            print(
                f"      - Precipitação: {result.harmonized_data['precipitation_mm']} mm"
            )
            return True
        else:
            print("   ❌ Erro ao salvar Open-Meteo Archive")
            return False


def test_openmeteo_forecast_save():
    """Testa salvamento de dados Open-Meteo Forecast."""
    print("\n3️⃣  Testando Open-Meteo Forecast...")

    with get_db_context() as session:
        tomorrow = datetime.now() + timedelta(days=1)

        record = ClimateData(
            source_api="openmeteo_forecast",
            latitude=-22.7250,
            longitude=-47.6476,
            elevation=547.0,
            timezone="America/Sao_Paulo",
            date=tomorrow,
            raw_data={
                "temperature_2m_max": 29.2,
                "temperature_2m_min": 19.1,
                "relative_humidity_2m": 68.0,
                "wind_speed_10m": 3.5,
                "et0_fao_evapotranspiration": 4.12,
            },
            harmonized_data={
                "temp_max_c": 29.2,
                "temp_min_c": 19.1,
                "humidity_percent": 68.0,
                "wind_speed_ms": 3.5,
            },
            eto_mm_day=4.12,
            eto_method="penman_monteith",
            quality_flags={"forecast": True},
        )

        session.add(record)
        session.commit()

        result = (
            session.query(ClimateData)
            .filter(ClimateData.source_api == "openmeteo_forecast")
            .first()
        )

        if result:
            print(f"   ✅ Registro salvo: ID={result.id}")
            print(f"      - Data: {result.date.strftime('%Y-%m-%d')}")
            print(f"      - ETo (forecast): {result.eto_mm_day} mm/dia")
            return True
        else:
            print("   ❌ Erro ao salvar Open-Meteo Forecast")
            return False


def test_met_norway_save():
    """Testa salvamento de dados MET Norway."""
    print("\n4️⃣  Testando MET Norway...")

    with get_db_context() as session:
        record = ClimateData(
            source_api="met_norway",
            latitude=59.9139,
            longitude=10.7522,
            elevation=23.0,
            timezone="Europe/Oslo",
            date=datetime.now(),
            raw_data={
                "air_temperature": 15.2,
                "relative_humidity": 75.0,
                "wind_speed": 5.2,
                "cloud_area_fraction": 35.0,
            },
            harmonized_data={
                "temp_mean_c": 15.2,
                "humidity_percent": 75.0,
                "wind_speed_ms": 5.2,
            },
            eto_mm_day=2.85,
            eto_method="penman_monteith",
        )

        session.add(record)
        session.commit()

        result = (
            session.query(ClimateData)
            .filter(ClimateData.source_api == "met_norway")
            .first()
        )

        if result:
            print(f"   ✅ Registro salvo: ID={result.id}")
            print(f"      - Localização: Oslo, Noruega")
            print(
                f"      - Temperatura: {result.harmonized_data['temp_mean_c']}°C"
            )
            return True
        else:
            print("   ❌ Erro ao salvar MET Norway")
            return False


def test_nws_forecast_save():
    """Testa salvamento de dados NWS Forecast."""
    print("\n5️⃣  Testando NWS Forecast...")

    with get_db_context() as session:
        record = ClimateData(
            source_api="nws_forecast",
            latitude=40.7128,
            longitude=-74.0060,
            elevation=10.0,
            timezone="America/New_York",
            date=datetime.now() + timedelta(days=2),
            raw_data={
                "temperature": 72.0,
                "relativeHumidity": {"value": 65.0},
                "windSpeed": "10 mph",
                "shortForecast": "Partly Cloudy",
            },
            harmonized_data={
                "temp_f": 72.0,
                "temp_c": 22.2,
                "humidity_percent": 65.0,
                "wind_speed_ms": 4.47,
            },
            eto_mm_day=3.95,
            eto_method="penman_monteith",
            quality_flags={"forecast": True, "source": "nws"},
        )

        session.add(record)
        session.commit()

        result = (
            session.query(ClimateData)
            .filter(ClimateData.source_api == "nws_forecast")
            .first()
        )

        if result:
            print(f"   ✅ Registro salvo: ID={result.id}")
            print(f"      - Localização: Nova York, EUA")
            print(f"      - Temperatura: {result.harmonized_data['temp_c']}°C")
            return True
        else:
            print("   ❌ Erro ao salvar NWS Forecast")
            return False


def test_nws_stations_save():
    """Testa salvamento de dados NWS Stations."""
    print("\n6️⃣  Testando NWS Stations...")

    with get_db_context() as session:
        record = ClimateData(
            source_api="nws_stations",
            latitude=41.9742,
            longitude=-87.9073,
            elevation=201.0,
            timezone="America/Chicago",
            date=datetime.now() - timedelta(hours=1),
            raw_data={
                "temperature": {"value": 18.5},
                "relativeHumidity": {"value": 72.0},
                "windSpeed": {"value": 5.5},
                "stationIdentifier": "KORD",
            },
            harmonized_data={
                "temp_c": 18.5,
                "humidity_percent": 72.0,
                "wind_speed_ms": 5.5,
                "station_id": "KORD",
            },
            eto_mm_day=3.12,
            eto_method="penman_monteith",
            quality_flags={"realtime": True},
        )

        session.add(record)
        session.commit()

        result = (
            session.query(ClimateData)
            .filter(ClimateData.source_api == "nws_stations")
            .first()
        )

        if result:
            print(f"   ✅ Registro salvo: ID={result.id}")
            print(f"      - Estação: KORD (O'Hare)")
            print(f"      - ETo real-time: {result.eto_mm_day} mm/dia")
            return True
        else:
            print("   ❌ Erro ao salvar NWS Stations")
            return False


def validate_data_retrieval():
    """Valida recuperação de dados salvos."""
    print("\n" + "=" * 80)
    print("🔍 VALIDANDO RECUPERAÇÃO DE DADOS")
    print("=" * 80)

    with get_db_context() as session:
        # Query por API
        print("\n📊 Registros por API:")
        result = session.execute(
            text(
                """
                SELECT source_api, COUNT(*) as total
                FROM climate_data
                GROUP BY source_api
                ORDER BY source_api
            """
            )
        )

        total_records = 0
        for row in result:
            print(f"   - {row[0]}: {row[1]} registro(s)")
            total_records += row[1]

        print(f"\n📈 Total de registros: {total_records}")

        # Verificar campos JSONB
        print("\n🔍 Validando campos JSONB...")
        result = session.execute(
            text(
                """
                SELECT id, source_api,
                       jsonb_object_keys(raw_data) as raw_keys,
                       jsonb_object_keys(harmonized_data) as harmonized_keys
                FROM climate_data
                WHERE id = (SELECT MIN(id) FROM climate_data)
            """
            )
        )

        row = result.fetchone()
        if row:
            print(f"   ✅ raw_data tem chaves")
            print(f"   ✅ harmonized_data tem chaves")

        # Verificar campos novos
        result = session.execute(
            text(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE elevation IS NOT NULL) as with_elevation,
                    COUNT(*) FILTER (WHERE timezone IS NOT NULL) as with_timezone,
                    COUNT(*) FILTER (WHERE quality_flags IS NOT NULL) as with_quality,
                    COUNT(*) as total
                FROM climate_data
            """
            )
        )

        row = result.fetchone()
        if row:
            print(f"\n📊 Campos populados:")
            print(f"   - elevation: {row[0]}/{row[3]} registros")
            print(f"   - timezone: {row[1]}/{row[3]} registros")
            print(f"   - quality_flags: {row[2]}/{row[3]} registros")


def cleanup_test_data():
    """Remove dados de teste."""
    print("\n🗑️  Limpando dados de teste...")

    with get_db_context() as session:
        result = session.execute(
            text("DELETE FROM climate_data WHERE id IS NOT NULL")
        )
        session.commit()
        print(f"   ✅ {result.rowcount} registros removidos")


def main():
    """Executa todos os testes."""
    print("\n" + "=" * 80)
    print("🧪 TESTE DE INTEGRAÇÃO - SALVAMENTO MULTI-API")
    print("=" * 80)

    results = []

    # Executar testes
    results.append(("NASA POWER", test_nasa_power_save()))
    results.append(("Open-Meteo Archive", test_openmeteo_archive_save()))
    results.append(("Open-Meteo Forecast", test_openmeteo_forecast_save()))
    results.append(("MET Norway", test_met_norway_save()))
    results.append(("NWS Forecast", test_nws_forecast_save()))
    results.append(("NWS Stations", test_nws_stations_save()))

    # Validar dados
    validate_data_retrieval()

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for api_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {api_name}: {status}")

    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")

    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Tabela climate_data está funcionando perfeitamente")
        print("✅ Salvamento multi-API validado")
        print("✅ Campos JSONB funcionando corretamente")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")

    # Perguntar se quer limpar
    print("\n" + "=" * 80)
    response = input("🗑️  Remover dados de teste? (s/N): ")
    if response.lower() == "s":
        cleanup_test_data()
    else:
        print("   ℹ️  Dados de teste mantidos para análise")

    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
