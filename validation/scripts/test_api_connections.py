"""
Test EVAonline API connections before running full validation.

This script quickly tests connectivity to all 6 climate data sources
and OpenTopo elevation service.

Usage:
    python validation/scripts/test_api_connections.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

# Import EVAonline services
from validation_logic_eto.api.services.openmeteo_archive.openmeteo_archive_sync_adapter import (
    OpenMeteoArchiveSyncAdapter,
)
from validation_logic_eto.api.services.openmeteo_forecast.openmeteo_forecast_sync_adapter import (
    OpenMeteoForecastSyncAdapter,
)
from validation_logic_eto.api.services.nasa_power.nasa_power_sync_adapter import (
    NASAPowerSyncAdapter,
)
from validation_logic_eto.api.services.met_norway.met_norway_sync_adapter import (
    METNorwaySyncAdapter,
)
from validation_logic_eto.api.services.nws_forecast.nws_forecast_sync_adapter import (
    NWSDailyForecastSyncAdapter,
)
from validation_logic_eto.api.services.nws_stations.nws_stations_sync_adapter import (
    NWSStationsSyncAdapter,
)
from validation_logic_eto.api.services.opentopo.opentopo_sync_adapter import (
    OpenTopoSyncAdapter,
)

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)


def test_openmeteo_archive():
    """Test OpenMeteo Archive API (historical data)"""
    logger.info("\n1️⃣  Testing OpenMeteo Archive (Historical)...")
    try:
        adapter = OpenMeteoArchiveSyncAdapter()

        # Test with Barreiras/BA coordinates
        result = adapter.get_daily_data_sync(
            lat=-12.15,
            lon=-45.00,
            start_date="2023-01-01",
            end_date="2023-01-07",
        )

        if result and len(result) > 0:
            logger.success(f"   ✅ OpenMeteo Archive: OK ({len(result)} days)")
            return True
        else:
            logger.error("   ❌ OpenMeteo Archive: No data returned")
            return False

    except Exception as e:
        logger.error(f"   ❌ OpenMeteo Archive: {str(e)}")
        return False


def test_openmeteo_forecast():
    """Test OpenMeteo Forecast API"""
    logger.info("\n2️⃣  Testing OpenMeteo Forecast...")
    try:
        adapter = OpenMeteoForecastSyncAdapter()

        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        result = adapter.get_daily_data_sync(
            lat=-12.15,
            lon=-45.00,
            start_date=str(today),
            end_date=str(tomorrow),
        )

        if result and len(result) > 0:
            logger.success(
                f"   ✅ OpenMeteo Forecast: OK ({len(result)} days)"
            )
            return True
        else:
            logger.error("   ❌ OpenMeteo Forecast: No data returned")
            return False

    except Exception as e:
        logger.error(f"   ❌ OpenMeteo Forecast: {str(e)}")
        return False


def test_nasa_power():
    """Test NASA POWER API"""
    logger.info("\n3️⃣  Testing NASA POWER...")
    try:
        adapter = NASAPowerSyncAdapter()

        result = adapter.get_daily_data_sync(
            lat=-12.15,
            lon=-45.00,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 7),
        )

        if result and len(result) > 0:
            logger.success(f"   ✅ NASA POWER: OK ({len(result)} days)")
            return True
        else:
            logger.error("   ❌ NASA POWER: No data returned")
            return False

    except Exception as e:
        logger.error(f"   ❌ NASA POWER: {str(e)}")
        return False


def test_met_norway():
    """Test MET Norway API (Global coverage)"""
    logger.info("\n4️⃣  Testing MET Norway...")
    try:
        adapter = METNorwaySyncAdapter()

        # Test with Oslo coordinates (within coverage)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        result = adapter.get_daily_data_sync(
            lat=59.91,  # Oslo
            lon=10.75,
            start_date=today,
            end_date=tomorrow,
        )

        if result and len(result) > 0:
            logger.success(f"   ✅ MET Norway: OK ({len(result)} days)")
            return True
        else:
            logger.warning(
                "   ⚠️  MET Norway: No data (outside Nordic region?)"
            )
            return True  # Not a critical error

    except Exception as e:
        logger.warning(
            f"   ⚠️  MET Norway: {str(e)} (expected if outside coverage)"
        )
        return True  # Not a critical error


def test_nws_forecast():
    """Test NWS Forecast API (USA only)"""
    logger.info("\n5️⃣  Testing NWS Forecast...")
    try:
        adapter = NWSDailyForecastSyncAdapter()

        # Test with Des Moines, IA coordinates
        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        result = adapter.get_daily_data_sync(
            lat=41.59,  # Des Moines, IA
            lon=-93.62,
            start_date=today,
            end_date=tomorrow,
        )

        if result and len(result) > 0:
            logger.success(f"   ✅ NWS Forecast: OK ({len(result)} days)")
            return True
        else:
            logger.warning("   ⚠️  NWS Forecast: No data (outside USA?)")
            return True  # Not a critical error

    except Exception as e:
        logger.warning(
            f"   ⚠️  NWS Forecast: {str(e)} (expected if outside USA)"
        )
        return True  # Not a critical error


def test_nws_stations():
    """Test NWS Stations API (USA only, real-time observations)"""
    logger.info("\n6️⃣  Testing NWS Stations...")
    try:
        adapter = NWSStationsSyncAdapter()

        # Test with Des Moines, IA coordinates
        yesterday = datetime.now() - timedelta(days=1)
        today = datetime.now()

        result = adapter.get_daily_data_sync(
            lat=41.59,  # Des Moines, IA
            lon=-93.62,
            start_date=yesterday,
            end_date=today,
        )

        if result and len(result) > 0:
            logger.success(f"   ✅ NWS Stations: OK ({len(result)} days)")
            return True
        else:
            logger.warning(
                "   ⚠️  NWS Stations: No data (outside USA or no stations nearby?)"
            )
            return True  # Not a critical error

    except Exception as e:
        logger.warning(
            f"   ⚠️  NWS Stations: {str(e)} (expected if outside USA)"
        )
        return True  # Not a critical error


def test_opentopo():
    """Test OpenTopo elevation API"""
    logger.info("\n7️⃣  Testing OpenTopo (Elevation)...")
    try:
        adapter = OpenTopoSyncAdapter()

        # Test with Barreiras/BA coordinates
        result = adapter.get_elevation_sync(lat=-12.15, lon=-45.00)

        if result and hasattr(result, "elevation"):
            elevation = result.elevation
            dataset = result.dataset
            logger.success(
                f"   ✅ OpenTopo: OK "
                f"(elevation={elevation:.1f}m, dataset={dataset})"
            )
            return True
        else:
            logger.error("   ❌ OpenTopo: No elevation returned")
            return False

    except Exception as e:
        logger.error(f"   ❌ OpenTopo: {str(e)}")
        return False


def main():
    """Run all API connection tests"""
    logger.info("=" * 70)
    logger.info("🔌 EVAonline API Connection Tests")
    logger.info("=" * 70)
    logger.info(
        "Testing connectivity to all climate data sources and elevation service..."
    )

    results = {
        "OpenMeteo Archive": test_openmeteo_archive(),
        "OpenMeteo Forecast": test_openmeteo_forecast(),
        "NASA POWER": test_nasa_power(),
        "MET Norway": test_met_norway(),
        "NWS Forecast": test_nws_forecast(),
        "NWS Stations": test_nws_stations(),
        "OpenTopo": test_opentopo(),
    }

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 CONNECTION TEST SUMMARY")
    logger.info("=" * 70)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for api, status in results.items():
        icon = "✅" if status else "❌"
        logger.info(f"{icon} {api:25s}: {'OK' if status else 'FAILED'}")

    logger.info(
        f"\n📈 Success rate: {success_count}/{total_count} ({100*success_count/total_count:.0f}%)"
    )

    # Critical APIs check (OpenMeteo Archive, NASA POWER, OpenTopo)
    critical_apis = ["OpenMeteo Archive", "NASA POWER", "OpenTopo"]
    critical_failed = [api for api in critical_apis if not results[api]]

    if critical_failed:
        logger.error(
            f"\n❌ CRITICAL APIs FAILED: {', '.join(critical_failed)}"
        )
        logger.error("   Validation will NOT work without these services!")
        logger.info("\n💡 Troubleshooting:")
        logger.info("   1. Check your internet connection")
        logger.info("   2. Verify API endpoints are accessible")
        logger.info("   3. Check for rate limiting or API keys")
        return False
    else:
        logger.success("\n✅ All critical APIs are working!")
        logger.info("   You can proceed with validation:")
        logger.info(
            "   python validation/scripts/calculate_eto_validation.py --region brasil --max-cities 1"
        )
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
