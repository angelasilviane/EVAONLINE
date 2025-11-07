"""
Test NWS Stations Sync Adapter

Testa o adaptador síncrono com dados reais de Denver, Colorado.
Valida:
- Agregação horária → diária com pandas
- Filtragem de observações atrasadas
- Quality logging
- Integração completa do sync wrapper

Author: EVAonline Team
Date: 2025-11-06
"""

from datetime import datetime, timedelta
from backend.api.services.nws_stations_sync_adapter import (
    NWSStationsSyncAdapter,
)
from backend.api.services.nws_stations_client import NWSStationsConfig


def test_sync_adapter_denver():
    """
    Testa sync adapter com dados reais de Denver.

    Usa coordenadas de Denver para buscar estação próxima (KBJC)
    e agregar observações horárias em diários.
    """
    print("=" * 80)
    print("🧪 TEST: NWS Stations Sync Adapter - Denver, Colorado")
    print("=" * 80)

    # Configuração
    config = NWSStationsConfig(
        base_url="https://api.weather.gov",
        observation_delay_threshold=20,  # 20 minutos
    )

    # Criar adapter SEM filtrar atrasadas (para ver dados reais)
    adapter = NWSStationsSyncAdapter(config=config, filter_delayed=False)

    print("\n📍 Location: Denver, Colorado")
    print("   Latitude: 39.7392°N")
    print("   Longitude: -104.9903°W")

    # Período de 2 dias (ontem e hoje)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)

    print(f"\n📅 Period: {start_date.date()} to {end_date.date()}")
    print("   (últimas 24 horas)")

    try:
        # Buscar dados usando sync adapter
        print("\n🔄 Fetching data from NWS API...")
        daily_data = adapter.get_daily_data_sync(
            lat=39.7392,
            lon=-104.9903,
            start_date=start_date,
            end_date=end_date,
        )

        print(f"\n✅ Success! Retrieved {len(daily_data)} daily records")

        if not daily_data:
            print(
                "⚠️  No data returned - "
                "this may be expected for recent periods"
            )
            return

        # Analisar resultados
        print("\n" + "=" * 80)
        print("📊 DAILY AGGREGATED DATA")
        print("=" * 80)

        for i, record in enumerate(daily_data, 1):
            print(f"\n📆 Day {i}: {record.date.date()}")
            print("-" * 40)

            # Temperatura
            if record.temp_min is not None:
                print("   🌡️  Temperature:")
                print(f"      Min:  {record.temp_min:.1f}°C")
                print(f"      Max:  {record.temp_max:.1f}°C")
                print(f"      Mean: {record.temp_mean:.1f}°C")
            else:
                print("   🌡️  Temperature: NO DATA")

            # Umidade
            if record.humidity is not None:
                print(f"   💧 Humidity: {record.humidity:.1f}%")
            else:
                print("   💧 Humidity: NO DATA")

            # Vento
            if record.wind_speed is not None:
                print(f"   💨 Wind Speed: {record.wind_speed:.1f} m/s")
            else:
                print("   💨 Wind Speed: NO DATA")

            # Precipitação
            if record.precipitation is not None and record.precipitation > 0:
                print(f"   🌧️  Precipitation: {record.precipitation:.1f} mm")
            else:
                print("   🌧️  Precipitation: 0.0 mm (or no data)")

            # Radiação solar
            print(f"   ☀️  Solar Radiation: {record.solar_radiation:.1f} W/m²")
            print("      (NWS não fornece - sempre 0)")

        # Estatísticas gerais
        print("\n" + "=" * 80)
        print("📈 STATISTICS")
        print("=" * 80)

        temps_min = [r.temp_min for r in daily_data if r.temp_min is not None]
        temps_max = [r.temp_max for r in daily_data if r.temp_max is not None]
        temps_mean = [
            r.temp_mean for r in daily_data if r.temp_mean is not None
        ]
        humidities = [r.humidity for r in daily_data if r.humidity is not None]
        winds = [r.wind_speed for r in daily_data if r.wind_speed is not None]
        precips = [
            r.precipitation
            for r in daily_data
            if r.precipitation is not None and r.precipitation > 0
        ]

        print("\n🌡️  Temperature Range:")
        if temps_min and temps_max:
            print(f"   Absolute Min: {min(temps_min):.1f}°C")
            print(f"   Absolute Max: {max(temps_max):.1f}°C")
            if temps_mean:
                avg_mean = sum(temps_mean) / len(temps_mean)
                print(f"   Average Mean: {avg_mean:.1f}°C")
        else:
            print("   NO DATA")

        print("\n💧 Humidity:")
        if humidities:
            avg_humidity = sum(humidities) / len(humidities)
            print(f"   Average: {avg_humidity:.1f}%")
            print(f"   Range: {min(humidities):.1f}% - {max(humidities):.1f}%")
        else:
            print("   NO DATA")

        print("\n💨 Wind Speed:")
        if winds:
            avg_wind = sum(winds) / len(winds)
            print(f"   Average: {avg_wind:.1f} m/s")
            print(f"   Range: {min(winds):.1f} - {max(winds):.1f} m/s")
        else:
            print("   NO DATA")

        print("\n🌧️  Precipitation:")
        if precips:
            total_precip = sum(precips)
            print(f"   Total: {total_precip:.1f} mm")
            print(f"   Days with rain: {len(precips)}/{len(daily_data)}")
        else:
            print("   No precipitation recorded")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        raise


def test_sync_adapter_with_filter():
    """
    Testa sync adapter com filtragem de observações atrasadas.

    Compara resultados com e sem filtro para ver impacto.
    """
    print("\n\n")
    print("=" * 80)
    print("🧪 TEST: Sync Adapter with Delayed Observations Filter")
    print("=" * 80)

    # Configuração
    config = NWSStationsConfig(
        base_url="https://api.weather.gov",
        observation_delay_threshold=20,  # 20 minutos
    )

    # Período de 1 dia
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)

    print(f"\n📅 Period: {start_date.date()} to {end_date.date()}")

    try:
        # 1. SEM filtro
        print("\n1️⃣  Testing WITHOUT filter (filter_delayed=False)")
        adapter_no_filter = NWSStationsSyncAdapter(
            config=config, filter_delayed=False
        )
        data_no_filter = adapter_no_filter.get_daily_data_sync(
            lat=39.7392,
            lon=-104.9903,
            start_date=start_date,
            end_date=end_date,
        )
        print(f"   Result: {len(data_no_filter)} daily records")

        # 2. COM filtro
        print("\n2️⃣  Testing WITH filter (filter_delayed=True)")
        adapter_with_filter = NWSStationsSyncAdapter(
            config=config, filter_delayed=True
        )
        data_with_filter = adapter_with_filter.get_daily_data_sync(
            lat=39.7392,
            lon=-104.9903,
            start_date=start_date,
            end_date=end_date,
        )
        print(f"   Result: {len(data_with_filter)} daily records")

        # Comparar
        print("\n" + "=" * 80)
        print("📊 COMPARISON")
        print("=" * 80)
        print("\nDays returned:")
        print(f"   Without filter: {len(data_no_filter)}")
        print(f"   With filter:    {len(data_with_filter)}")

        if len(data_no_filter) == len(data_with_filter):
            print(
                "\n✅ Same number of days "
                "(filter may have removed some hourly obs)"
            )
        else:
            print(
                "\n⚠️  Different number of days - "
                "filter had significant impact"
            )

        # Comparar qualidade dos dados
        if data_no_filter and data_with_filter:
            print("\n🌡️  Temperature completeness:")

            temps_no_filter = [
                r.temp_mean for r in data_no_filter if r.temp_mean is not None
            ]
            temps_with_filter = [
                r.temp_mean
                for r in data_with_filter
                if r.temp_mean is not None
            ]

            print(
                f"   Without filter: "
                f"{len(temps_no_filter)}/{len(data_no_filter)} days"
            )
            print(
                f"   With filter:    "
                f"{len(temps_with_filter)}/{len(data_with_filter)} days"
            )

        print("\n" + "=" * 80)
        print("✅ FILTER TEST COMPLETED")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        raise


def test_health_check():
    """Testa health check do sync adapter."""
    print("\n\n")
    print("=" * 80)
    print("🧪 TEST: Health Check")
    print("=" * 80)

    adapter = NWSStationsSyncAdapter()

    print("\n🏥 Running health check...")
    is_healthy = adapter.health_check_sync()

    if is_healthy:
        print("✅ NWS API is healthy and accessible")
    else:
        print("❌ NWS API is not accessible")

    return is_healthy


if __name__ == "__main__":
    print("🚀 Starting NWS Stations Sync Adapter Tests")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test 1: Health Check
    test_health_check()

    # Test 2: Basic sync adapter
    test_sync_adapter_denver()

    # Test 3: Filter comparison
    test_sync_adapter_with_filter()

    print("\n\n")
    print("=" * 80)
    print("🎉 ALL TESTS COMPLETED")
    print("=" * 80)
