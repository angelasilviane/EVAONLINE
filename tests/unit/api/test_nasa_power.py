"""
Test NASA POWER API sync adapter.

Tests data download from NASA POWER (power.larc.nasa.gov) for different
global locations, validating data quality, coverage, and historical limits.

NASA POWER Coverage:
- Global (all coordinates)
- Historical: 1981-01-01 to present (2-7 day delay)
- Variables: T, RH, Wind, Solar Radiation, Precipitation
- License: Public Domain (NASA)
"""

import pytest
from datetime import datetime, timedelta

from backend.api.services.nasa_power_sync_adapter import (
    NASAPowerSyncAdapter,
)


# Test locations covering different continents and climates
TEST_LOCATIONS = {
    "sao_paulo": {
        "name": "São Paulo, Brazil",
        "lat": -23.5505,
        "lon": -46.6333,
        "continent": "South America",
    },
    "berlin": {
        "name": "Berlin, Germany",
        "lat": 52.5200,
        "lon": 13.4050,
        "continent": "Europe",
    },
    "tokyo": {
        "name": "Tokyo, Japan",
        "lat": 35.6762,
        "lon": 139.6503,
        "continent": "Asia",
    },
    "new_york": {
        "name": "New York, USA",
        "lat": 40.7128,
        "lon": -74.0060,
        "continent": "North America",
    },
    "sydney": {
        "name": "Sydney, Australia",
        "lat": -33.8688,
        "lon": 151.2093,
        "continent": "Oceania",
    },
    "cairo": {
        "name": "Cairo, Egypt",
        "lat": 30.0444,
        "lon": 31.2357,
        "continent": "Africa",
    },
}


@pytest.fixture
def nasa_adapter():
    """Create NASA POWER sync adapter."""
    return NASAPowerSyncAdapter()


class TestNASAPowerBasicDownload:
    """Test basic data download functionality."""

    @pytest.mark.parametrize("location_key", list(TEST_LOCATIONS.keys()))
    def test_download_one_week(self, nasa_adapter, location_key):
        """Test downloading 1 week of data for each location."""
        location = TEST_LOCATIONS[location_key]

        # Recent 1-week period
        end_date = datetime.now() - timedelta(days=7)  # Avoid NASA delay
        start_date = end_date - timedelta(days=7)

        print(f"\n📍 Testing {location['name']} ({location['continent']})")
        print(f"   Period: {start_date.date()} to {end_date.date()}")

        # Download data
        data = nasa_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        # Validate response
        assert data is not None, "Data should not be None"
        assert len(data) > 0, "Data should contain records"
        assert len(data) >= 6, f"Should have at least 6 days (got {len(data)})"

        # Validate data structure
        first_record = data[0]
        assert hasattr(first_record, "date"), "Record should have date"
        assert hasattr(first_record, "temp_max"), "Record should have temp_max"
        assert hasattr(first_record, "temp_min"), "Record should have temp_min"
        assert hasattr(
            first_record, "solar_radiation"
        ), "Record should have solar_radiation"
        assert hasattr(
            first_record, "precipitation"
        ), "Record should have precipitation"

        print(f"   ✅ Downloaded {len(data)} records successfully")

    def test_download_one_month(self, nasa_adapter):
        """Test downloading 30 days (NASA POWER limit) for São Paulo."""
        location = TEST_LOCATIONS["sao_paulo"]

        # 30 days period (NASA POWER limit, avoiding 7-day delay)
        end_date = datetime.now() - timedelta(days=7)
        start_date = end_date - timedelta(days=29)  # 30 days inclusive

        print(f"\n📍 Testing {location['name']} - 30 days")

        data = nasa_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert (
            len(data) >= 28
        ), f"Should have at least 28 days (got {len(data)})"
        print(f"   ✅ Downloaded {len(data)} records for 30 days")

    def test_download_historical(self, nasa_adapter):
        """Test downloading historical data from 2020."""
        location = TEST_LOCATIONS["berlin"]

        start_date = datetime(2020, 6, 1)
        end_date = datetime(2020, 6, 30)

        print(f"\n📍 Testing {location['name']} - Historical (2020)")

        data = nasa_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert (
            len(data) == 30
        ), f"Should have exactly 30 days (got {len(data)})"
        print(f"   ✅ Historical data: {len(data)} records")


class TestNASAPowerDataQuality:
    """Test data quality and variable validation."""

    def test_temperature_range(self, nasa_adapter):
        """Test that temperatures are within reasonable bounds."""
        location = TEST_LOCATIONS["sao_paulo"]

        end_date = datetime.now() - timedelta(days=7)
        start_date = end_date - timedelta(days=7)

        data = nasa_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        print(f"\n🌡️  Testing temperature ranges for {location['name']}")

        for record in data:
            if record.temp_max is not None:
                assert (
                    -60 <= record.temp_max <= 60
                ), f"T_max out of range: {record.temp_max}°C"

            if record.temp_min is not None:
                assert (
                    -80 <= record.temp_min <= 50
                ), f"T_min out of range: {record.temp_min}°C"

            if record.temp_mean is not None:
                assert (
                    -70 <= record.temp_mean <= 55
                ), f"T_mean out of range: {record.temp_mean}°C"

            # T_max should be >= T_min
            if record.temp_max and record.temp_min:
                assert (
                    record.temp_max >= record.temp_min
                ), f"T_max < T_min: {record.temp_max} < {record.temp_min}"

        print("   ✅ All temperatures within valid ranges")

    def test_solar_radiation_positive(self, nasa_adapter):
        """Test that solar radiation is non-negative."""
        location = TEST_LOCATIONS["tokyo"]

        end_date = datetime.now() - timedelta(days=7)
        start_date = end_date - timedelta(days=7)

        data = nasa_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        print(f"\n☀️  Testing solar radiation for {location['name']}")

        for record in data:
            if record.solar_radiation is not None:
                assert (
                    record.solar_radiation >= 0
                ), f"Solar radiation negative: {record.solar_radiation}"
                assert (
                    record.solar_radiation <= 50
                ), f"Solar radiation too high: {record.solar_radiation}"

        print("   ✅ Solar radiation values valid")

    def test_precipitation_non_negative(self, nasa_adapter):
        """Test that precipitation is non-negative."""
        location = TEST_LOCATIONS["new_york"]

        end_date = datetime.now() - timedelta(days=7)
        start_date = end_date - timedelta(days=7)

        data = nasa_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        print(f"\n🌧️  Testing precipitation for {location['name']}")

        for record in data:
            if record.precipitation is not None:
                assert (
                    record.precipitation >= 0
                ), f"Precipitation negative: {record.precipitation}"

        print("   ✅ Precipitation values valid")


class TestNASAPowerDateLimits:
    """Test date range validation."""

    def test_earliest_date_limit(self, nasa_adapter):
        """Test that dates before 1981 are rejected."""
        location = TEST_LOCATIONS["sao_paulo"]

        # Try to download data from 1980 (before NASA POWER start)
        # Use 7 days to avoid range limit error
        start_date = datetime(1980, 1, 1)
        end_date = datetime(1980, 1, 7)

        print("\n⚠️  Testing earliest date limit (should fail before 1981)")

        with pytest.raises((ValueError, Exception)):
            # API may reject with ValueError (local) or HTTPStatusError (API)
            nasa_adapter.get_daily_data_sync(
                lat=location["lat"],
                lon=location["lon"],
                start_date=start_date,
                end_date=end_date,
            )

        print("   ✅ Correctly rejected data before 1981-01-01")

    def test_valid_earliest_date(self, nasa_adapter):
        """Test that 1981-01-01 (earliest valid date) works."""
        location = TEST_LOCATIONS["berlin"]

        start_date = datetime(1981, 1, 1)
        end_date = datetime(1981, 1, 7)

        print("\n✅ Testing earliest valid date (1981-01-01)")

        data = nasa_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) >= 6, "Should get data from 1981-01-01"
        print(f"   ✅ Successfully downloaded {len(data)} records from 1981")


class TestNASAPowerEdgeCases:
    """Test edge cases and error handling."""

    def test_single_day_download(self, nasa_adapter):
        """Test minimum 7-day download (NASA POWER requirement)."""
        location = TEST_LOCATIONS["cairo"]

        end_date = datetime.now() - timedelta(days=10)
        start_date = end_date - timedelta(days=6)  # 7 days total

        print(f"\n📅 Testing 7-day download for {location['name']}")

        data = nasa_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) >= 7, f"Should get at least 7 days (got {len(data)})"
        print(f"   ✅ Minimum period download successful ({len(data)} days)")

    def test_extreme_coordinates(self, nasa_adapter):
        """Test extreme latitude coordinates."""
        # Arctic
        print("\n🧭 Testing extreme coordinates (Arctic)")

        end_date = datetime.now() - timedelta(days=7)
        start_date = end_date - timedelta(days=7)

        data_arctic = nasa_adapter.get_daily_data_sync(
            lat=78.0,  # Svalbard, Norway
            lon=15.0,
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data_arctic) > 0, "Should get data for Arctic location"
        print(f"   ✅ Arctic: {len(data_arctic)} records")

        # Antarctic
        print("   Testing Antarctic")
        data_antarctic = nasa_adapter.get_daily_data_sync(
            lat=-75.0,  # Near Antarctic coast
            lon=0.0,
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data_antarctic) > 0, "Should get data for Antarctic"
        print(f"   ✅ Antarctic: {len(data_antarctic)} records")

    def test_health_check(self, nasa_adapter):
        """Test health check functionality."""
        print("\n🏥 Testing NASA POWER health check")

        is_healthy = nasa_adapter.health_check_sync()

        assert is_healthy is True, "NASA POWER API should be healthy"
        print("   ✅ Health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
