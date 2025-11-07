"""
Test Open-Meteo Archive API sync adapter.

Tests data download from Open-Meteo Archive (archive-api.open-meteo.com)
for different global locations, validating historical data quality and
coverage back to 1940.

Open-Meteo Archive Coverage:
- Global (all coordinates)
- Historical: 1940-01-01 to (today - 2 days)
- Variables: T, RH, Wind, Solar, Precipitation, ET0
- License: CC BY 4.0
"""

import pytest
from datetime import datetime, timedelta

from backend.api.services.openmeteo_archive_sync_adapter import (
    OpenMeteoArchiveSyncAdapter,
)


TEST_LOCATIONS = {
    "sao_paulo": {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333},
    "berlin": {"name": "Berlin", "lat": 52.5200, "lon": 13.4050},
    "tokyo": {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    "new_york": {"name": "New York", "lat": 40.7128, "lon": -74.0060},
}


@pytest.fixture
def archive_adapter():
    """Create Open-Meteo Archive sync adapter."""
    return OpenMeteoArchiveSyncAdapter()


class TestOpenMeteoArchiveBasic:
    """Test basic data download functionality."""

    @pytest.mark.parametrize("location_key", list(TEST_LOCATIONS.keys()))
    def test_download_one_week(self, archive_adapter, location_key):
        """Test downloading 1 week of historical data."""
        location = TEST_LOCATIONS[location_key]

        # Archive has 7-day delay, use 14-day old period
        end_date = datetime.now() - timedelta(days=14)
        start_date = end_date - timedelta(days=6)  # 7 days total

        print(f"\n📍 Testing {location['name']}")
        print(f"   Period: {start_date.date()} to {end_date.date()}")

        data = archive_adapter.get_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert data is not None
        assert len(data) >= 6, f"Expected >= 6 days, got {len(data)}"

        # Validate structure (data is list of dicts)
        first = data[0]
        assert isinstance(first, dict)
        assert "date" in first
        assert "temperature_2m_max" in first or "temp_max" in first
        assert "temperature_2m_min" in first or "temp_min" in first

        print(f"   ✅ Downloaded {len(data)} records")

    def test_download_historical_1940(self, archive_adapter):
        """Test downloading data from 1940 (earliest available)."""
        location = TEST_LOCATIONS["berlin"]

        start_date = datetime(1940, 6, 1)
        end_date = datetime(1940, 6, 7)

        print(f"\n📅 Testing {location['name']} - Historical 1940")

        data = archive_adapter.get_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) >= 6
        print(f"   ✅ 1940 data: {len(data)} records")

    def test_download_one_year(self, archive_adapter):
        """Test downloading 1 full year of data."""
        location = TEST_LOCATIONS["sao_paulo"]

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2020, 12, 31)

        print(f"\n📆 Testing {location['name']} - Full year 2020")

        data = archive_adapter.get_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        # 2020 is leap year (366 days)
        assert len(data) == 366, f"Expected 366 days, got {len(data)}"
        print(f"   ✅ Full year: {len(data)} records")


class TestOpenMeteoArchiveDateLimits:
    """Test date range validation."""

    def test_earliest_date_limit(self, archive_adapter):
        """Test that dates before 1940 are rejected."""
        location = TEST_LOCATIONS["tokyo"]

        start_date = datetime(1939, 12, 25)
        end_date = datetime(1939, 12, 31)

        print("\n⚠️  Testing earliest date limit (should fail before 1940)")

        with pytest.raises(ValueError, match="1940"):
            archive_adapter.get_data_sync(
                lat=location["lat"],
                lon=location["lon"],
                start_date=start_date,
                end_date=end_date,
            )

        print("   ✅ Correctly rejected data before 1940-01-01")

    def test_future_date_rejected(self, archive_adapter):
        """Test that future dates are rejected."""
        location = TEST_LOCATIONS["berlin"]

        # Try to get data from tomorrow
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=7)

        print("\n⚠️  Testing future date (should fail)")

        with pytest.raises(ValueError):
            archive_adapter.get_data_sync(
                lat=location["lat"],
                lon=location["lon"],
                start_date=start_date,
                end_date=end_date,
            )

        print("   ✅ Correctly rejected future dates")


class TestOpenMeteoArchiveDataQuality:
    """Test data quality validation."""

    def test_temperature_values(self, archive_adapter):
        """Test temperature ranges are reasonable."""
        location = TEST_LOCATIONS["new_york"]

        # Use safe historical period (14 days ago)
        end_date = datetime.now() - timedelta(days=14)
        start_date = end_date - timedelta(days=6)  # 7 days total

        data = archive_adapter.get_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        print(f"\n🌡️  Testing temperatures for {location['name']}")

        for record in data:
            # Get temperature values (dict keys)
            temp_max = record.get("temperature_2m_max") or record.get(
                "temp_max"
            )
            temp_min = record.get("temperature_2m_min") or record.get(
                "temp_min"
            )

            if temp_max is not None:
                assert -60 <= temp_max <= 60

            if temp_min is not None:
                assert -80 <= temp_min <= 50

            if temp_max is not None and temp_min is not None:
                assert temp_max >= temp_min

        print("   ✅ Temperature ranges valid")

    def test_has_extended_variables(self, archive_adapter):
        """Test that Open-Meteo provides extended variables."""
        location = TEST_LOCATIONS["sao_paulo"]

        # Use safe historical period (14 days ago)
        end_date = datetime.now() - timedelta(days=14)
        start_date = end_date - timedelta(days=2)  # 3 days

        data = archive_adapter.get_data_sync(
            lat=location["lat"],
            lon=location["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        print(f"\n📊 Testing extended variables for {location['name']}")

        first = data[0]

        # Check for Open-Meteo specific variables (dict keys)
        assert isinstance(first, dict)
        assert "date" in first
        # Check for at least some core weather variables
        has_temp = (
            "temperature_2m_max" in first
            or "temp_max" in first
            or "temperature_2m" in first
        )
        has_precip = "precipitation" in first or "rain" in first
        has_wind = "wind_speed" in first or "windspeed_10m" in first

        assert has_temp, f"No temp vars in: {list(first.keys())}"
        assert has_precip or has_wind, "Missing precipitation or wind data"
        print("   ✅ Extended variables present")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
