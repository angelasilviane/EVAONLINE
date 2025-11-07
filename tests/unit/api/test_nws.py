"""
Test NWS (National Weather Service) APIs sync adapters.

Tests both NWS Forecast and NWS Stations APIs for USA locations,
validating coverage, data quality, and USA-specific functionality.

NWS Coverage:
- USA Continental only (-125°W to -66°W, 24°N to 49°N)
- Forecast: Up to 7 days
- Stations: ~1800 weather stations, real-time observations
- License: US Government Public Domain
"""

import pytest
from datetime import datetime, timedelta

from backend.api.services.nws_forecast_sync_adapter import (
    NWSDailyForecastSyncAdapter,
)
from backend.api.services.nws_stations_sync_adapter import NWSSyncAdapter


# Test locations within USA Continental bounds
USA_TEST_LOCATIONS = {
    "new_york": {
        "name": "New York, NY",
        "lat": 40.7128,
        "lon": -74.0060,
        "state": "New York",
    },
    "los_angeles": {
        "name": "Los Angeles, CA",
        "lat": 34.0522,
        "lon": -118.2437,
        "state": "California",
    },
    "chicago": {
        "name": "Chicago, IL",
        "lat": 41.8781,
        "lon": -87.6298,
        "state": "Illinois",
    },
    "miami": {
        "name": "Miami, FL",
        "lat": 25.7617,
        "lon": -80.1918,
        "state": "Florida",
    },
}

# Locations OUTSIDE USA (should be rejected)
NON_USA_LOCATIONS = {
    "london": {"name": "London, UK", "lat": 51.5074, "lon": -0.1278},
    "tokyo": {"name": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503},
    "sao_paulo": {
        "name": "São Paulo, Brazil",
        "lat": -23.5505,
        "lon": -46.6333,
    },
}


@pytest.fixture
def nws_forecast_adapter():
    """Create NWS Forecast sync adapter."""
    return NWSDailyForecastSyncAdapter()


@pytest.fixture
def nws_stations_adapter():
    """Create NWS Stations sync adapter."""
    return NWSSyncAdapter()


class TestNWSForecastBasic:
    """Test NWS Forecast API basic functionality."""

    @pytest.mark.parametrize("location_key", list(USA_TEST_LOCATIONS.keys()))
    def test_download_forecast(self, nws_forecast_adapter, location_key):
        """Test downloading forecast for USA locations."""
        location = USA_TEST_LOCATIONS[location_key]

        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=3)

        print(f"\n📍 Testing NWS Forecast: {location['name']}")
        print(f"   Period: {start_date.date()} to {end_date.date()}")

        data = nws_forecast_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert data is not None
        assert len(data) > 0, "Should get forecast data"

        # Validate structure
        first = data[0]
        assert hasattr(first, "date")
        assert hasattr(first, "temp_max")
        assert hasattr(first, "temp_min")

        print(f"   ✅ Downloaded {len(data)} forecast records")

    def test_forecast_seven_days(self, nws_forecast_adapter):
        """Test downloading 7-day forecast (NWS maximum)."""
        location = USA_TEST_LOCATIONS["chicago"]

        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=7)

        print(f"\n📅 Testing 7-day forecast for {location['name']}")

        data = nws_forecast_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0, "Should get 7-day forecast"
        print(f"   ✅ 7-day forecast: {len(data)} records")


class TestNWSStationsBasic:
    """Test NWS Stations API basic functionality."""

    @pytest.mark.parametrize("location_key", list(USA_TEST_LOCATIONS.keys()))
    def test_download_station_data(self, nws_stations_adapter, location_key):
        """Test downloading station observations."""
        location = USA_TEST_LOCATIONS[location_key]

        # Recent observations (last 24 hours)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)

        print(f"\n📍 Testing NWS Stations: {location['name']}")
        print(f"   Period: {start_date.date()} to {end_date.date()}")

        data = nws_stations_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert data is not None
        assert len(data) > 0, "Should get station observations"

        # Validate structure
        first = data[0]
        assert hasattr(first, "date")
        assert hasattr(first, "temp_max") or hasattr(first, "temp_mean")

        print(f"   ✅ Downloaded {len(data)} observation records")

    def test_download_week_observations(self, nws_stations_adapter):
        """Test downloading 1 week of station observations."""
        location = USA_TEST_LOCATIONS["miami"]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        print(f"\n📆 Testing 1-week observations for {location['name']}")

        data = nws_stations_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) >= 5, f"Expected >= 5 days, got {len(data)}"
        print(f"   ✅ 1-week data: {len(data)} records")


class TestNWSCoverageValidation:
    """Test USA coverage validation."""

    @pytest.mark.parametrize("location_key", list(NON_USA_LOCATIONS.keys()))
    def test_non_usa_rejected_forecast(
        self, nws_forecast_adapter, location_key
    ):
        """Test that non-USA locations are rejected by Forecast API."""
        location = NON_USA_LOCATIONS[location_key]

        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=3)

        print(f"\n⚠️  Testing non-USA location: {location['name']}")
        print("   (should be rejected)")

        with pytest.raises(ValueError, match="USA|coverage|cobertura"):
            nws_forecast_adapter.get_daily_data_sync(
                lat=location["lat"],
                lon=location["lon"],
                start_date=start_date,
                end_date=end_date,
            )

        print("   ✅ Correctly rejected non-USA location")

    @pytest.mark.parametrize("location_key", list(NON_USA_LOCATIONS.keys()))
    def test_non_usa_rejected_stations(
        self, nws_stations_adapter, location_key
    ):
        """Test that non-USA locations are rejected by Stations API."""
        location = NON_USA_LOCATIONS[location_key]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)

        print(f"\n⚠️  Testing non-USA station: {location['name']}")
        print("   (should be rejected)")

        with pytest.raises(ValueError, match="USA|coverage|cobertura"):
            nws_stations_adapter.get_daily_data_sync(
                lat=location["lat"],
                lon=location["lon"],
                start_date=start_date,
                end_date=end_date,
            )

        print("   ✅ Correctly rejected non-USA location")

    def test_alaska_hawaii_coverage(self, nws_forecast_adapter):
        """Test that Alaska and Hawaii might have limited coverage."""
        # Alaska
        print("\n🗺️  Testing Alaska coverage")

        # Note: NWS coverage is primarily Continental USA
        # Alaska/Hawaii may or may not work depending on NWS implementation
        try:
            data = nws_forecast_adapter.get_daily_data_sync(
                lat=61.2181,  # Anchorage, Alaska
                lon=-149.9003,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=1),
            )
            print(f"   ℹ️  Alaska: {len(data)} records (coverage available)")
        except ValueError as e:
            print(f"   ℹ️  Alaska: Not in coverage area (expected)")


class TestNWSDataQuality:
    """Test NWS data quality."""

    def test_forecast_temperature_ranges(self, nws_forecast_adapter):
        """Test forecast temperatures are reasonable."""
        location = USA_TEST_LOCATIONS["new_york"]

        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=3)

        data = nws_forecast_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        print(f"\n🌡️  Testing forecast temps for {location['name']}")

        for record in data:
            if record.temp_max is not None:
                assert -50 <= record.temp_max <= 55
            if record.temp_min is not None:
                assert -60 <= record.temp_min <= 50

        print("   ✅ Forecast temperatures valid")

    def test_stations_real_observations(self, nws_stations_adapter):
        """Test that station observations look realistic."""
        location = USA_TEST_LOCATIONS["los_angeles"]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)

        data = nws_stations_adapter.get_daily_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        print(f"\n📊 Testing station observations for {location['name']}")

        assert len(data) > 0, "Should have observations"

        # Check for reasonable values
        for record in data:
            if hasattr(record, "temp_mean") and record.temp_mean:
                assert -50 <= record.temp_mean <= 55

            if hasattr(record, "humidity") and record.humidity:
                assert 0 <= record.humidity <= 100

        print("   ✅ Station observations look realistic")


class TestNWSHealthCheck:
    """Test health check functionality."""

    def test_forecast_health_check(self, nws_forecast_adapter):
        """Test NWS Forecast health check."""
        print("\n🏥 Testing NWS Forecast health check")

        is_healthy = nws_forecast_adapter.health_check_sync()

        assert is_healthy is True, "NWS Forecast should be healthy"
        print("   ✅ NWS Forecast health check passed")

    def test_stations_health_check(self, nws_stations_adapter):
        """Test NWS Stations health check."""
        print("\n🏥 Testing NWS Stations health check")

        is_healthy = nws_stations_adapter.health_check_sync()

        assert is_healthy is True, "NWS Stations should be healthy"
        print("   ✅ NWS Stations health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
