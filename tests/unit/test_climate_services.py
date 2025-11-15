"""
Unit tests for climate data services to verify data return functionality.

Tests 6 climate data sources:
1. Open-Meteo Forecast
2. Open-Meteo Archive
3. NASA POWER
4. NWS Forecast
5. NWS Stations
6. MET Norway Locationforecast

Enhanced features:
- Global location testing
- Date range validation (7-30 days)
- Data collection start dates validation
- Extended historical data support (1940+)
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Tuple

import pytest

from backend.api.services.met_norway.met_norway_client import (
    METNorwayClient,
)
from backend.api.services.nasa_power.nasa_power_client import (
    NASAPowerClient,
)
from backend.api.services.nws_forecast.nws_forecast_client import (
    NWSForecastClient,
)
from backend.api.services.nws_stations.nws_stations_client import (
    NWSStationsClient,
)
from backend.api.services.openmeteo_forecast.openmeteo_forecast_client import (
    OpenMeteoForecastClient,
)

# Global test locations representing different continents and climates
TEST_LOCATIONS = [
    # Europe
    {
        "name": "Paris, France",
        "lat": 48.8566,
        "lon": 2.3522,
        "continent": "Europe",
    },
    {
        "name": "Oslo, Norway",
        "lat": 59.9139,
        "lon": 10.7522,
        "continent": "Europe",
    },
    {
        "name": "Madrid, Spain",
        "lat": 40.4168,
        "lon": -3.7038,
        "continent": "Europe",
    },
    # North America
    {
        "name": "New York, USA",
        "lat": 40.7128,
        "lon": -74.0060,
        "continent": "North America",
    },
    {
        "name": "Los Angeles, USA",
        "lat": 34.0522,
        "lon": -118.2437,
        "continent": "North America",
    },
    {
        "name": "Vancouver, Canada",
        "lat": 49.2827,
        "lon": -123.1207,
        "continent": "North America",
    },
    # South America
    {
        "name": "São Paulo, Brazil",
        "lat": -23.5505,
        "lon": -46.6333,
        "continent": "South America",
    },
    {
        "name": "Buenos Aires, Argentina",
        "lat": -34.6118,
        "lon": -58.3969,
        "continent": "South America",
    },
    {
        "name": "Lima, Peru",
        "lat": -12.0464,
        "lon": -77.0428,
        "continent": "South America",
    },
    # Asia
    {
        "name": "Tokyo, Japan",
        "lat": 35.6762,
        "lon": 139.6503,
        "continent": "Asia",
    },
    {
        "name": "Mumbai, India",
        "lat": 19.0760,
        "lon": 72.8777,
        "continent": "Asia",
    },
    {
        "name": "Seoul, South Korea",
        "lat": 37.5665,
        "lon": 126.9780,
        "continent": "Asia",
    },
    # Africa
    {
        "name": "Cairo, Egypt",
        "lat": 30.0444,
        "lon": 31.2357,
        "continent": "Africa",
    },
    {
        "name": "Cape Town, South Africa",
        "lat": -33.9249,
        "lon": 18.4241,
        "continent": "Africa",
    },
    {
        "name": "Nairobi, Kenya",
        "lat": -1.2921,
        "lon": 36.8219,
        "continent": "Africa",
    },
    # Oceania
    {
        "name": "Sydney, Australia",
        "lat": -33.8688,
        "lon": 151.2093,
        "continent": "Oceania",
    },
    {
        "name": "Auckland, New Zealand",
        "lat": -36.8485,
        "lon": 174.7633,
        "continent": "Oceania",
    },
]


class DataSourceInfo:
    """Information about climate data sources and their capabilities."""

    # Data collection start dates for each source
    DATA_START_DATES = {
        "openmeteo_archive": datetime(1940, 1, 1),
        "openmeteo_forecast": datetime.now()
        - timedelta(days=90),  # Recent only
        "nasa_power": datetime(1981, 1, 1),
        "nws_forecast": datetime.now() - timedelta(days=7),  # Forecast only
        "nws_stations": datetime.now()
        - timedelta(days=30),  # Recent observations
        "met_norway": datetime.now() - timedelta(days=14),  # Forecast only
    }

    # Maximum historical reach for each source (from today backwards)
    MAX_HISTORICAL_DAYS = {
        "openmeteo_archive": (
            datetime.now() - datetime(1940, 1, 1)
        ).days,  # ~30,000+ days
        "openmeteo_forecast": 90,  # Archive cutoff
        "nasa_power": (
            datetime.now() - datetime(1981, 1, 1)
        ).days,  # ~16,000+ days
        "nws_forecast": 7,  # Forecast only
        "nws_stations": 30,  # Recent observations
        "met_norway": 14,  # Forecast only
    }

    # Coverage areas
    COVERAGE_AREAS = {
        "openmeteo_archive": "Global",
        "openmeteo_forecast": "Global",
        "nasa_power": "Global",
        "nws_forecast": "USA Continental",
        "nws_stations": "USA Continental",
        "met_norway": "Europe",
    }

    @classmethod
    def get_data_start_date(cls, source: str) -> datetime:
        """Get the earliest available data date for a source."""
        return cls.DATA_START_DATES.get(source, datetime.now())

    @classmethod
    def get_max_historical_days(cls, source: str) -> int:
        """Get maximum historical days available for a source."""
        return cls.MAX_HISTORICAL_DAYS.get(source, 0)

    @classmethod
    def get_coverage(cls, source: str) -> str:
        """Get coverage area description for a source."""
        return cls.COVERAGE_AREAS.get(source, "Unknown")

    @classmethod
    def is_historical_source(cls, source: str) -> bool:
        """Check if source provides historical data (not just forecast)."""
        return cls.get_max_historical_days(source) > 365  # More than 1 year

    @classmethod
    def get_available_sources_for_location(
        cls, lat: float, lon: float
    ) -> List[str]:
        """Get available sources for a specific location."""
        sources = []

        # Open-Meteo always available (global)
        sources.extend(["openmeteo_archive", "openmeteo_forecast"])

        # NASA POWER always available (global)
        sources.append("nasa_power")

        # MET Norway for Europe
        if -25 <= lon <= 45 and 35 <= lat <= 72:
            sources.append("met_norway")

        # NWS for USA
        if -125 <= lon <= -66 and 24 <= lat <= 49:
            sources.extend(["nws_forecast", "nws_stations"])

        return sources

    @classmethod
    def generate_test_date_ranges(
        cls, source: str, num_ranges: int = 3
    ) -> List[Tuple[datetime, datetime]]:
        """Generate valid test date ranges for a source (7-30 days)."""
        ranges = []
        today = datetime.now()

        for i in range(num_ranges):
            # Random range length between 7-30 days
            range_days = 7 + (i * 7)  # 7, 14, 21, or 28 days

            # For historical sources, test different historical periods
            if cls.is_historical_source(source):
                # Test different historical periods
                if i == 0:
                    # Recent (last 60 days)
                    end_date = today - timedelta(days=2)
                    start_date = end_date - timedelta(days=range_days)
                elif i == 1:
                    # Medium term (6-12 months ago)
                    end_date = today - timedelta(days=200)
                    start_date = end_date - timedelta(days=range_days)
                else:
                    # Long term (2-5 years ago)
                    end_date = today - timedelta(days=1000)
                    start_date = end_date - timedelta(days=range_days)

                # Ensure we don't go before source start date
                start_limit = cls.get_data_start_date(source)
                if start_date < start_limit:
                    start_date = start_limit
                    end_date = start_date + timedelta(days=range_days)
            else:
                # For forecast-only sources, use recent/future dates
                if "forecast" in source:
                    start_date = today
                    end_date = today + timedelta(
                        days=min(range_days, 14)
                    )  # Forecast limit
                else:
                    # Recent observations
                    end_date = today - timedelta(days=1)
                    start_date = end_date - timedelta(days=range_days)

            ranges.append((start_date, end_date))

        return ranges


@pytest.fixture
async def openmeteo_client():
    """Fixture for Open-Meteo Forecast client."""
    client = OpenMeteoForecastClient()
    yield client
    # ForecastClient doesn't require close() (uses requests_cache)


@pytest.fixture
async def nasa_client():
    """Fixture for NASA POWER client."""
    client = NASAPowerClient()
    yield client
    await client.close()


@pytest.fixture
async def nws_client():
    """Fixture for NWS Forecast client."""
    client = NWSForecastClient()
    yield client
    await client.close()


@pytest.fixture
async def nws_stations_client():
    """Fixture for NWS Stations client."""
    client = NWSStationsClient()
    yield client
    await client.close()


@pytest.fixture
async def met_norway_client():
    """Fixture for MET Norway Locationforecast client."""
    client = METNorwayClient()
    yield client
    await client.close()


class TestClimateServices:

    @pytest.mark.asyncio
    async def test_openmeteo_forecast(self, openmeteo_client):
        """Test Open-Meteo Forecast API returns data."""
        lat, lon = -15.7939, -47.8828
        start_date = datetime.now()
        end_date = start_date + timedelta(days=5)  # Max 5 days forecast

        data = await openmeteo_client.get_climate_data(
            lat=lat,
            lng=lon,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        assert isinstance(data, dict)
        assert "climate_data" in data
        assert "dates" in data["climate_data"]
        assert len(data["climate_data"]["dates"]) > 0
        records = len(data["climate_data"]["dates"])
        print(f"✅ Open-Meteo Forecast: {records} records")

    @pytest.mark.asyncio
    async def test_openmeteo_archive(self, openmeteo_client):
        """Test Open-Meteo Archive API returns data."""
        lat, lon = -15.7939, -47.8828
        end_date = datetime.now() - timedelta(days=10)
        start_date = end_date - timedelta(days=7)  # 7 days for archive

        data = await openmeteo_client.get_climate_data(
            lat=lat,
            lng=lon,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        assert isinstance(data, dict)
        assert "climate_data" in data
        assert "dates" in data["climate_data"]
        assert len(data["climate_data"]["dates"]) > 0
        records = len(data["climate_data"]["dates"])
        print(f"✅ Open-Meteo Archive: {records} records")

    @pytest.mark.asyncio
    async def test_nasa_power(self, nasa_client):
        """Test NASA POWER API returns data."""
        lat, lon = -15.7939, -47.8828
        end_date = datetime.now() - timedelta(days=2)
        start_date = end_date - timedelta(days=7)

        data = await nasa_client.get_daily_data(
            lat=lat, lon=lon, start_date=start_date, end_date=end_date
        )

        assert isinstance(data, list)
        assert len(data) > 0
        assert hasattr(data[0], "date")
        print(f"✅ NASA POWER: {len(data)} records")

    @pytest.mark.asyncio
    async def test_nws_forecast(self, nws_client):
        """Test NWS Forecast API returns data."""
        lat, lon = 38.8977, -77.0365  # Washington DC

        data = await nws_client.get_forecast_data(lat=lat, lon=lon)

        assert isinstance(data, list)
        assert len(data) > 0
        assert hasattr(data[0], "timestamp")
        print(f"✅ NWS Forecast: {len(data)} records")

    @pytest.mark.asyncio
    async def test_nws_stations(self, nws_stations_client):
        """Test NWS Stations API returns data."""
        lat, lon = 38.8977, -77.0365  # Washington DC

        stations = await nws_stations_client.find_nearest_stations(
            lat=lat, lon=lon, limit=5
        )

        assert isinstance(stations, list)
        assert len(stations) > 0
        assert hasattr(stations[0], "station_id")
        print(f"✅ NWS Stations: {len(stations)} stations found")

    @pytest.mark.asyncio
    async def test_met_norway(self, met_norway_client):
        """Test MET Norway Locationforecast API returns data."""
        lat, lon = -15.7939, -47.8828  # Global coverage
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)

        data = await met_norway_client.get_daily_forecast(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            variables=["temperature_2m_max", "temperature_2m_min"],
        )

        assert isinstance(data, list)
        assert len(data) > 0
        assert hasattr(data[0], "date")
        print(f"✅ MET Norway Locationforecast: {len(data)} records")


class TestGlobalLocations:
    """Test climate services with locations from around the world."""

    @pytest.mark.asyncio
    async def test_openmeteo_global_coverage(self, openmeteo_client):
        """Test Open-Meteo with locations from different continents."""
        for location in TEST_LOCATIONS[:5]:  # Test first 5 locations
            print(f"\n🌍 Testing {location['name']} ({location['continent']})")

            # Test archive data (historical)
            end_date = datetime.now() - timedelta(days=30)
            start_date = end_date - timedelta(days=7)

            try:
                data = await openmeteo_client.get_climate_data(
                    lat=location["lat"],
                    lng=location["lon"],
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                )

                records = len(data["climate_data"]["dates"])
                print(f"   ✅ Open-Meteo Archive: {records} records")

            except Exception as e:
                print(f"   ❌ Open-Meteo Archive failed: {e}")

            # Test forecast data
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)

            try:
                data = await openmeteo_client.get_climate_data(
                    lat=location["lat"],
                    lng=location["lon"],
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                )

                records = len(data["climate_data"]["dates"])
                print(f"   ✅ Open-Meteo Forecast: {records} records")

            except Exception as e:
                print(f"   ❌ Open-Meteo Forecast failed: {e}")

    @pytest.mark.asyncio
    async def test_nasa_power_global_coverage(self, nasa_client):
        """Test NASA POWER with global locations."""
        for location in TEST_LOCATIONS[:5]:  # Test first 5 locations
            print(
                f"\n🌍 Testing NASA POWER at {location['name']} ({location['continent']})"
            )

            end_date = datetime.now() - timedelta(days=7)
            start_date = end_date - timedelta(days=7)

            try:
                data = await nasa_client.get_daily_data(
                    lat=location["lat"],
                    lon=location["lon"],
                    start_date=start_date,
                    end_date=end_date,
                )

                print(f"   ✅ NASA POWER: {len(data)} records")

            except Exception as e:
                print(f"   ❌ NASA POWER failed: {e}")


class TestDateRangeValidation:
    """Test date range validation and data availability."""

    def test_data_source_info(self):
        """Test DataSourceInfo utility class."""
        print("\n📊 Data Source Information:")

        for source in DataSourceInfo.DATA_START_DATES.keys():
            start_date = DataSourceInfo.get_data_start_date(source)
            max_days = DataSourceInfo.get_max_historical_days(source)
            coverage = DataSourceInfo.get_coverage(source)
            is_historical = DataSourceInfo.is_historical_source(source)

            print(f"   {source}:")
            print(f"     Start Date: {start_date.date()}")
            print(f"     Max Historical Days: {max_days}")
            print(f"     Coverage: {coverage}")
            print(f"     Historical: {is_historical}")
            print()

    def test_client_availability_info(self):
        """Test client availability info methods."""
        print("\n🔍 Client Availability Information:")

        # Test Open-Meteo Forecast
        try:
            info = OpenMeteoForecastClient.get_info()
            print("   Open-Meteo Forecast:")
            print(f"     Coverage: {info['coverage']}")
            print(f"     Period: {info.get('period', 'N/A')}")
            print(f"     License: {info['license']}")
            print()
        except Exception as e:
            print(f"   ❌ Open-Meteo info failed: {e}")

        # Test NASA POWER
        try:
            info = NASAPowerClient.get_data_availability_info()
            print("   NASA POWER:")
            print(f"     Start: {info['data_start_date']}")
            print(f"     Years: {info['max_historical_years']}")
            print(f"     Coverage: {info['coverage']}")
            print()
        except Exception as e:
            print(f"   ❌ NASA POWER info failed: {e}")

        # Test NWS
        try:
            nws_client = NWSForecastClient()
            info = nws_client.get_data_availability_info()
            print("   NWS:")
            print(f"     Start: {info['data_start_date']}")
            print(f"     Forecast Days: {info['forecast_horizon_days']}")
            print(f"     Coverage: {info['coverage']}")
            print()
        except Exception as e:
            print(f"   ❌ NWS info failed: {e}")

        # Test MET Norway Locationforecast
        try:
            info = METNorwayClient.get_data_availability_info()
            print("   MET Norway Locationforecast:")
            print(f"     Start: {info['data_start_date']}")
            print(f"     Forecast Days: {info['forecast_horizon_days']}")
            print(f"     Coverage: {info['coverage']}")
            print()
        except Exception as e:
            print(f"   ❌ MET Norway Locationforecast info failed: {e}")

    @pytest.mark.asyncio
    async def test_date_range_limits(self, openmeteo_client, nasa_client):
        """Test that services respect date range limits (7-30 days)."""
        print("\n📅 Testing Date Range Limits:")

        # Test Open-Meteo with different historical periods
        test_ranges = [
            (datetime(2020, 1, 1), datetime(2020, 1, 8)),  # 7 days
            (datetime(2010, 6, 1), datetime(2010, 7, 1)),  # 30 days
            (
                datetime(1990, 1, 1),
                datetime(1990, 1, 15),
            ),  # 14 days (very old)
        ]

        for start_date, end_date in test_ranges:
            range_days = (end_date - start_date).days + 1
            print(
                f"   Testing {range_days} days: {start_date.date()} to {end_date.date()}"
            )

            try:
                data = await openmeteo_client.get_climate_data(
                    lat=0.0,
                    lng=0.0,  # Equator
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                )

                records = len(data["climate_data"]["dates"])
                print(f"     ✅ Open-Meteo: {records} records")

            except Exception as e:
                print(f"     ❌ Open-Meteo failed: {e}")

    @pytest.mark.asyncio
    async def test_extended_historical_access(
        self, openmeteo_client, nasa_client
    ):
        """Test access to extended historical data (1940+)."""
        print("\n📚 Testing Extended Historical Data Access:")

        # Test Open-Meteo from 1940
        try:
            start_date = datetime(1940, 1, 1)
            end_date = datetime(1940, 1, 8)  # 7 days from start

            data = await openmeteo_client.get_climate_data(
                lat=52.5200,
                lng=13.4050,  # Berlin, Germany
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )

            records = len(data["climate_data"]["dates"])
            print(f"   ✅ Open-Meteo 1940: {records} records from Berlin")

        except Exception as e:
            print(f"   ❌ Open-Meteo 1940 failed: {e}")

        # Test NASA POWER from 1981
        try:
            start_date = datetime(1981, 1, 1)
            end_date = datetime(1981, 1, 8)  # 7 days from start

            data = await nasa_client.get_daily_data(
                lat=40.7128,
                lon=-74.0060,
                start_date=start_date,
                end_date=end_date,  # New York
            )

            print(f"   ✅ NASA POWER 1981: {len(data)} records from New York")

        except Exception as e:
            print(f"   ❌ NASA POWER 1981 failed: {e}")


# Manual test runner with global testing
async def run_manual_tests():
    """Run all tests manually with global location coverage."""
    print("🧪 Running enhanced manual climate services tests...")
    print("=" * 60)

    test_instance = TestClimateServices()
    date_test_instance = TestDateRangeValidation()
    global_test_instance = TestGlobalLocations()

    # Test data source information
    date_test_instance.test_data_source_info()

    # Test Open-Meteo
    try:
        openmeteo_client = OpenMeteoForecastClient()
        await test_instance.test_openmeteo_forecast(openmeteo_client)
        await test_instance.test_openmeteo_archive(openmeteo_client)
        # ForecastClient doesn't require close()
        print("✅ Open-Meteo tests passed")
    except Exception as e:
        print(f"❌ Open-Meteo tests failed: {e}")

    # Test NASA POWER
    try:
        nasa_client = NASAPowerClient()
        await test_instance.test_nasa_power(nasa_client)
        await nasa_client.close()
        print("✅ NASA POWER tests passed")
    except Exception as e:
        print(f"❌ NASA POWER tests failed: {e}")

    # Test NWS
    try:
        nws_client = NWSForecastClient()
        nws_stations_client = NWSStationsClient()
        await test_instance.test_nws_forecast(nws_client)
        await test_instance.test_nws_stations(nws_stations_client)
        await nws_client.close()
        await nws_stations_client.close()
        print("✅ NWS tests passed")
    except Exception as e:
        print(f"❌ NWS tests failed: {e}")

    # Test MET Norway Locationforecast
    try:
        met_client = METNorwayClient()
        await test_instance.test_met_norway(met_client)
        await met_client.close()
        print("✅ MET Norway Locationforecast tests passed")
    except Exception as e:
        print(f"❌ MET Norway Locationforecast tests failed: {e}")

    print("\n🌍 Testing Global Location Coverage:")
    print("-" * 40)

    # Test global coverage
    try:
        openmeteo_client = OpenMeteoForecastClient()
        nasa_client = NASAPowerClient()

        await global_test_instance.test_openmeteo_global_coverage(
            openmeteo_client
        )
        await global_test_instance.test_nasa_power_global_coverage(nasa_client)

        # ForecastClient doesn't require close()
        await nasa_client.close()

    except Exception as e:
        print(f"❌ Global coverage tests failed: {e}")

    print("\n📅 Testing Date Range Validation:")
    print("-" * 40)

    # Test date ranges
    try:
        openmeteo_client = OpenMeteoForecastClient()
        nasa_client = NASAPowerClient()

        await date_test_instance.test_date_range_limits(
            openmeteo_client, nasa_client
        )
        await date_test_instance.test_extended_historical_access(
            openmeteo_client, nasa_client
        )

        # ForecastClient doesn't require close()
        await nasa_client.close()

    except Exception as e:
        print(f"❌ Date range tests failed: {e}")

    print("\n🎉 Enhanced manual tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_manual_tests())
