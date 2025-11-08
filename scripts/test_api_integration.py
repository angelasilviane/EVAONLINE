"""
Script para testar integração com as APIs climáticas e salvamento no banco.

Este script:
1. Busca dados reais de cada uma das 6 APIs
2. Salva os dados na tabela climate_data
3. Valida se os dados foram salvos corretamente

Usage:
    uv run python scripts/test_api_integration.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db_context
from sqlalchemy import text


async def test_nasa_power(lat: float, lon: float):
    """Testa NASA POWER API."""
    print("\n📡 Testando NASA POWER API...")

    try:
        from backend.api.services.nasa_power.nasa_power_sync_adapter import (
            NASAPowerSyncAdapter,
        )

        adapter = NASAPowerSyncAdapter()

        # Buscar dados dos últimos 7 dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        data = adapter.fetch_data_sync(
            latitude=lat,
            longitude=lon,
            start_date=start_date,
            end_date=end_date,
        )

        if data and "daily" in data:
            print(f"  ✅ Dados recebidos: {len(data['daily'])} dias")

            # Salvar no banco
            with get_db_context() as db:
                for date_str, values in data["daily"].items():
                    db.execute(
                        text(
                            """
                            INSERT INTO climate_data 
                            (source_api, latitude, longitude, date, raw_data)
                            VALUES 
                            (:api, :lat, :lon, :date, :data::jsonb)
                            ON CONFLICT (source_api, latitude, longitude, date) 
                            DO UPDATE SET raw_data = EXCLUDED.raw_data
                        """
                        ),
                        {
                            "api": "nasa_power",
                            "lat": lat,
                            "lon": lon,
                            "date": date_str,
                            "data": str(values).replace("'", '"'),
                        },
                    )
                db.commit()

            print(f"  💾 Salvos {len(data['daily'])} registros no banco")
            return True
        else:
            print("  ❌ Nenhum dado recebido")
            return False

    except Exception as e:
        print(f"  ❌ Erro: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_openmeteo_archive(lat: float, lon: float):
    """Testa Open-Meteo Archive API."""
    print("\n📡 Testando Open-Meteo Archive API...")

    try:
        from backend.api.services.openmeteo_archive.openmeteo_archive_sync_adapter import (
            OpenMeteoArchiveSyncAdapter,
        )

        adapter = OpenMeteoArchiveSyncAdapter()

        # Buscar dados dos últimos 7 dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        data = adapter.fetch_data_sync(
            latitude=lat,
            longitude=lon,
            start_date=start_date,
            end_date=end_date,
        )

        if data and "daily" in data:
            print(f"  ✅ Dados recebidos: {len(data['daily'])} dias")

            # Salvar no banco
            with get_db_context() as db:
                count = 0
                for idx in range(len(data["daily"].get("time", []))):
                    date_str = data["daily"]["time"][idx]

                    # Montar registro com todas as variáveis
                    record = {}
                    for key in data["daily"].keys():
                        if key != "time":
                            record[key] = (
                                data["daily"][key][idx]
                                if idx < len(data["daily"][key])
                                else None
                            )

                    db.execute(
                        text(
                            """
                            INSERT INTO climate_data 
                            (source_api, latitude, longitude, date, raw_data)
                            VALUES 
                            (:api, :lat, :lon, :date, :data::jsonb)
                            ON CONFLICT (source_api, latitude, longitude, date) 
                            DO UPDATE SET raw_data = EXCLUDED.raw_data
                        """
                        ),
                        {
                            "api": "openmeteo_archive",
                            "lat": lat,
                            "lon": lon,
                            "date": date_str,
                            "data": str(record)
                            .replace("'", '"')
                            .replace("None", "null"),
                        },
                    )
                    count += 1

                db.commit()

            print(f"  💾 Salvos {count} registros no banco")
            return True
        else:
            print("  ❌ Nenhum dado recebido")
            return False

    except Exception as e:
        print(f"  ❌ Erro: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_openmeteo_forecast(lat: float, lon: float):
    """Testa Open-Meteo Forecast API."""
    print("\n📡 Testando Open-Meteo Forecast API...")

    try:
        from backend.api.services.openmeteo_forecast.openmeteo_forecast_sync_adapter import (
            OpenMeteoForecastSyncAdapter,
        )

        adapter = OpenMeteoForecastSyncAdapter()

        # Buscar previsão dos próximos 7 dias
        data = adapter.fetch_data_sync(
            latitude=lat, longitude=lon, days_ahead=7
        )

        if data and "daily" in data:
            print(
                f"  ✅ Dados recebidos: {len(data['daily'].get('time', []))} dias"
            )

            # Salvar no banco
            with get_db_context() as db:
                count = 0
                for idx in range(len(data["daily"].get("time", []))):
                    date_str = data["daily"]["time"][idx]

                    # Montar registro com todas as variáveis
                    record = {}
                    for key in data["daily"].keys():
                        if key != "time":
                            record[key] = (
                                data["daily"][key][idx]
                                if idx < len(data["daily"][key])
                                else None
                            )

                    db.execute(
                        text(
                            """
                            INSERT INTO climate_data 
                            (source_api, latitude, longitude, date, raw_data)
                            VALUES 
                            (:api, :lat, :lon, :date, :data::jsonb)
                            ON CONFLICT (source_api, latitude, longitude, date) 
                            DO UPDATE SET raw_data = EXCLUDED.raw_data
                        """
                        ),
                        {
                            "api": "openmeteo_forecast",
                            "lat": lat,
                            "lon": lon,
                            "date": date_str,
                            "data": str(record)
                            .replace("'", '"')
                            .replace("None", "null"),
                        },
                    )
                    count += 1

                db.commit()

            print(f"  💾 Salvos {count} registros no banco")
            return True
        else:
            print("  ❌ Nenhum dado recebido")
            return False

    except Exception as e:
        print(f"  ❌ Erro: {e}")
        import traceback

        traceback.print_exc()
        return False


async def validate_saved_data(lat: float, lon: float):
    """Valida dados salvos no banco."""
    print("\n📊 VALIDANDO DADOS SALVOS NO BANCO:")
    print("-" * 80)

    with get_db_context() as db:
        result = db.execute(
            text(
                """
                SELECT 
                    source_api,
                    COUNT(*) as total_records,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM climate_data
                WHERE latitude = :lat AND longitude = :lon
                GROUP BY source_api
                ORDER BY source_api
            """
            ),
            {"lat": lat, "lon": lon},
        )

        total = 0
        for row in result:
            print(
                f"  📡 {row.source_api:25s} → {row.total_records:3d} registros "
                f"({row.earliest_date} a {row.latest_date})"
            )
            total += row.total_records

        print("-" * 80)
        print(f"  📦 TOTAL: {total} registros salvos")
        print("-" * 80 + "\n")


async def main():
    """Função principal."""

    # Coordenadas de teste: Balsas-MA, Brasil
    LAT = -7.5322
    LON = -46.0392

    print("\n" + "=" * 80)
    print("🧪 TESTE DE INTEGRAÇÃO COM APIs CLIMÁTICAS")
    print("=" * 80)
    print(f"\n📍 Localização de teste: Balsas-MA ({LAT}, {LON})")

    # Testar cada API
    results = {
        "nasa_power": await test_nasa_power(LAT, LON),
        "openmeteo_archive": await test_openmeteo_archive(LAT, LON),
        "openmeteo_forecast": await test_openmeteo_forecast(LAT, LON),
    }

    # Validar dados salvos
    await validate_saved_data(LAT, LON)

    # Resumo final
    print("\n" + "=" * 80)
    print("📋 RESUMO DOS TESTES:")
    print("=" * 80)

    for api, success in results.items():
        status = "✅ OK" if success else "❌ FALHOU"
        print(f"  {status:10s} {api}")

    total_success = sum(1 for s in results.values() if s)
    print(f"\n  🎯 {total_success}/{len(results)} APIs testadas com sucesso")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
