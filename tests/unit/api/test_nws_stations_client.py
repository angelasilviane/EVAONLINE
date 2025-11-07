"""
Test script para NWS Stations Client.

Valida:
1. Health check
2. Busca de estações próximas
3. Observações históricas (últimas 24h)
4. Observação mais recente
5. Observação por timestamp específico
6. Detection de known issues (delays, nulls, rounding)

Estação de teste: KJFK (JFK Airport, New York)
"""

import asyncio
from datetime import datetime, timedelta

from loguru import logger

from nws_stations_client import (
    NWSStationsClient,
    create_nws_stations_client,
)


async def test_health_check():
    """Test 1: Verifica se API está acessível."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Health Check")
    logger.info("=" * 70)

    client = create_nws_stations_client()

    try:
        is_healthy = await client.health_check()
        logger.info(f"✅ Health check result: {is_healthy}")

        if is_healthy:
            logger.success("✅ TEST 1 PASSED: API is healthy")
        else:
            logger.error("❌ TEST 1 FAILED: API is not healthy")

        return is_healthy

    finally:
        await client.close()


async def test_find_nearest_stations():
    """Test 2: Busca estações próximas."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Find Nearest Stations")
    logger.info("=" * 70)

    # New York City coordinates
    lat, lon = 40.7128, -74.0060
    logger.info(f"📍 Searching near: ({lat}, {lon}) - New York City")

    client = create_nws_stations_client()

    try:
        stations = await client.find_nearest_stations(lat, lon, limit=5)

        logger.info(f"\n📊 Found {len(stations)} stations:")
        for i, station in enumerate(stations, 1):
            logger.info(f"\n  {i}. {station.name}")
            logger.info(f"     ID: {station.station_id}")
            logger.info(
                f"     Location: ({station.latitude}, {station.longitude})"
            )
            logger.info(f"     Elevation: {station.elevation_m}m")
            logger.info(f"     Timezone: {station.timezone}")

        if len(stations) > 0:
            logger.success(f"✅ TEST 2 PASSED: Found {len(stations)} stations")
            return stations
        else:
            logger.error("❌ TEST 2 FAILED: No stations found")
            return []

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}")
        return []

    finally:
        await client.close()


async def test_station_observations():
    """Test 3: Observações históricas (últimas 24h)."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Station Observations (Last 24h)")
    logger.info("=" * 70)

    station_id = "KJFK"  # JFK Airport
    logger.info(f"📡 Station: {station_id} (JFK Airport, New York)")

    # Últimas 24 horas
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)

    logger.info(f"📅 Period: {start_date.date()} to {end_date.date()}")

    client = create_nws_stations_client()

    try:
        observations = await client.get_station_observations(
            station_id=station_id,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(f"\n📊 Retrieved {len(observations)} observations")

        if len(observations) > 0:
            # Mostrar primeiras 5 observações
            logger.info("\n🔍 Sample observations (first 5):")
            for i, obs in enumerate(observations[:5], 1):
                logger.info(f"\n  {i}. {obs.timestamp}")
                logger.info(f"     Temperature: {obs.temp_celsius}°C")
                logger.info(f"     Humidity: {obs.humidity_percent}%")
                logger.info(f"     Wind Speed: {obs.wind_speed_ms} m/s")
                logger.info(
                    f"     Precipitation: {obs.precipitation_1h_mm} mm"
                )
                logger.info(f"     Delayed: {obs.is_delayed}")

            # Estatísticas
            temps = [
                o.temp_celsius
                for o in observations
                if o.temp_celsius is not None
            ]
            humids = [
                o.humidity_percent
                for o in observations
                if o.humidity_percent is not None
            ]
            precips = [
                o.precipitation_1h_mm
                for o in observations
                if o.precipitation_1h_mm is not None
            ]
            delayed_count = sum(1 for o in observations if o.is_delayed)

            logger.info("\n📈 Statistics:")
            if temps:
                logger.info(
                    f"   Temperature: {min(temps):.1f}°C to {max(temps):.1f}°C (mean: {sum(temps)/len(temps):.1f}°C)"
                )
            if humids:
                logger.info(
                    f"   Humidity: {min(humids):.1f}% to {max(humids):.1f}% (mean: {sum(humids)/len(humids):.1f}%)"
                )
            if precips:
                total_precip = sum(precips)
                logger.info(f"   Total Precipitation: {total_precip:.1f} mm")
            logger.info(
                f"   Delayed Observations: {delayed_count}/{len(observations)} ({delayed_count/len(observations)*100:.1f}%)"
            )

            logger.success(
                f"✅ TEST 3 PASSED: Retrieved {len(observations)} observations"
            )
            return observations

        else:
            logger.warning("⚠️  TEST 3: No observations found")
            return []

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}")
        return []

    finally:
        await client.close()


async def test_latest_observation():
    """Test 4: Observação mais recente."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Latest Observation")
    logger.info("=" * 70)

    station_id = "KJFK"
    logger.info(f"📡 Station: {station_id} (JFK Airport)")

    client = create_nws_stations_client()

    try:
        obs = await client.get_latest_observation(station_id)

        if obs:
            logger.info("\n📊 Latest observation:")
            logger.info(f"   Timestamp: {obs.timestamp}")
            logger.info(f"   Temperature: {obs.temp_celsius}°C")
            logger.info(f"   Dewpoint: {obs.dewpoint_celsius}°C")
            logger.info(f"   Humidity: {obs.humidity_percent}%")
            logger.info(f"   Wind Speed: {obs.wind_speed_ms} m/s")
            logger.info(f"   Wind Direction: {obs.wind_direction}°")
            logger.info(f"   Pressure: {obs.pressure_hpa} hPa")
            logger.info(f"   Visibility: {obs.visibility_m} m")
            logger.info(f"   Precipitation (1h): {obs.precipitation_1h_mm} mm")
            logger.info(f"   Is Delayed: {obs.is_delayed}")

            # Calcular delay atual
            now = datetime.utcnow()
            if obs.timestamp.tzinfo:
                now = now.replace(tzinfo=obs.timestamp.tzinfo)
            delay_minutes = (now - obs.timestamp).total_seconds() / 60

            logger.info(f"\n⏱️  Current delay: {delay_minutes:.1f} minutes")

            logger.success("✅ TEST 4 PASSED: Latest observation retrieved")
            return obs

        else:
            logger.error("❌ TEST 4 FAILED: No observation available")
            return None

    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {e}")
        return None

    finally:
        await client.close()


async def test_observation_by_time():
    """Test 5: Observação por timestamp específico."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Observation by Specific Time")
    logger.info("=" * 70)

    station_id = "KJFK"
    # Timestamp de 6 horas atrás (hora cheia)
    target_time = datetime.utcnow().replace(
        minute=0, second=0, microsecond=0
    ) - timedelta(hours=6)

    logger.info(f"📡 Station: {station_id}")
    logger.info(f"🕐 Target time: {target_time}")

    client = create_nws_stations_client()

    try:
        obs = await client.get_observation_by_time(station_id, target_time)

        if obs:
            logger.info("\n📊 Observation at target time:")
            logger.info(f"   Actual Timestamp: {obs.timestamp}")
            logger.info(f"   Temperature: {obs.temp_celsius}°C")
            logger.info(f"   Humidity: {obs.humidity_percent}%")
            logger.info(f"   Precipitation: {obs.precipitation_1h_mm} mm")
            logger.info(f"   Is Delayed: {obs.is_delayed}")

            # Verificar se timestamp é próximo ao solicitado
            time_diff = abs(
                (
                    obs.timestamp.replace(tzinfo=None) - target_time
                ).total_seconds()
            )
            logger.info(f"\n⏱️  Time difference: {time_diff/60:.1f} minutes")

            logger.success("✅ TEST 5 PASSED: Observation by time retrieved")
            return obs

        else:
            logger.warning("⚠️  TEST 5: No observation at that time")
            return None

    except Exception as e:
        logger.error(f"❌ TEST 5 FAILED: {e}")
        return None

    finally:
        await client.close()


async def test_data_availability():
    """Test 6: Informações de disponibilidade."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: Data Availability Info")
    logger.info("=" * 70)

    info = NWSStationsClient.get_data_availability_info()

    logger.info("\n📋 NWS Stations API Information:")
    logger.info(f"   Source: {info['source']}")
    logger.info(f"   Coverage: {info['coverage']}")
    logger.info(f"   Stations: {info['stations']}")
    logger.info(f"   Data Type: {info['data_type']}")
    logger.info(f"   Resolution: {info['temporal_resolution']}")
    logger.info(f"   Update Frequency: {info['update_frequency']}")
    logger.info(f"   Typical Delay: {info['typical_delay']}")
    logger.info(f"   License: {info['license']}")

    logger.info("\n⚠️  Known Issues:")
    for key, value in info["known_issues"].items():
        logger.info(f"   • {key}: {value}")

    logger.info(f"\n🌍 Coverage Bbox:")
    bbox = info["bbox"]
    logger.info(f"   Longitude: {bbox['lon_min']}° to {bbox['lon_max']}°")
    logger.info(f"   Latitude: {bbox['lat_min']}° to {bbox['lat_max']}°")

    logger.success("✅ TEST 6 PASSED: Data availability info retrieved")
    return info


async def test_coverage_check():
    """Test 7: Verificação de cobertura."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 7: Coverage Check")
    logger.info("=" * 70)

    client = create_nws_stations_client()

    test_locations = [
        (40.7128, -74.0060, "New York City (inside coverage)"),
        (64.8378, -147.7164, "Fairbanks, Alaska (inside extended coverage)"),
        (21.3099, -157.8581, "Honolulu, Hawaii (inside extended coverage)"),
        (51.5074, -0.1278, "London, UK (outside coverage)"),
    ]

    results = []
    for lat, lon, name in test_locations:
        in_coverage = client.is_in_coverage(lat, lon)
        logger.info(f"   {name}: {'✅ IN' if in_coverage else '❌ OUT'}")
        results.append(in_coverage)

    await client.close()

    # Espera-se: True, True, True, False
    expected = [True, True, True, False]
    if results == expected:
        logger.success("✅ TEST 7 PASSED: Coverage check working correctly")
    else:
        logger.error(f"❌ TEST 7 FAILED: Expected {expected}, got {results}")

    return results == expected


async def run_all_tests():
    """Executa todos os testes."""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 NWS STATIONS CLIENT - TEST SUITE")
    logger.info("=" * 70)
    logger.info(f"📅 Test Date: {datetime.now()}")
    logger.info("")

    results = {}

    # Test 1: Health Check
    results["health_check"] = await test_health_check()

    # Test 2: Find Stations
    stations = await test_find_nearest_stations()
    results["find_stations"] = len(stations) > 0

    # Test 3: Historical Observations
    observations = await test_station_observations()
    results["observations"] = len(observations) > 0

    # Test 4: Latest Observation
    latest = await test_latest_observation()
    results["latest"] = latest is not None

    # Test 5: Observation by Time
    by_time = await test_observation_by_time()
    results["by_time"] = by_time is not None

    # Test 6: Data Availability
    info = await test_data_availability()
    results["availability"] = info is not None

    # Test 7: Coverage Check
    results["coverage"] = await test_coverage_check()

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")

    logger.info("")
    logger.info(
        f"   Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)"
    )
    logger.info("=" * 70)

    if passed == total:
        logger.success("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        logger.warning(f"\n⚠️  {total - passed} test(s) failed")

    return results


if __name__ == "__main__":
    # Executar testes
    asyncio.run(run_all_tests())
