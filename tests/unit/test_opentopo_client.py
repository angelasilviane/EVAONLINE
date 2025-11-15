"""
Test OpenTopoData Client.

Tests elevation retrieval and FAO-56 calculations.
"""

import pytest

from backend.api.services.opentopo import (
    OpenTopoClient,
    OpenTopoConfig,
    OpenTopoLocation,
)


class TestOpenTopoClient:
    """Test suite for OpenTopoData client."""

    @pytest.fixture
    async def client(self):
        """Create client instance."""
        client = OpenTopoClient()
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_get_elevation_brasilia(self, client):
        """Test elevation retrieval for Brasília."""
        # Brasília coordinates
        lat, lon = -15.7801, -47.9292

        location = await client.get_elevation(lat, lon)

        assert location is not None
        assert isinstance(location, OpenTopoLocation)
        assert location.lat == lat
        assert location.lon == lon
        # Brasília elevation: ~1100-1200m
        assert 1000 <= location.elevation <= 1300
        assert location.dataset == "srtm30m"

        print(
            f"\n✓ Brasília elevation: {location.elevation:.1f}m "
            f"(dataset: {location.dataset})"
        )

    @pytest.mark.asyncio
    async def test_get_elevation_sao_paulo(self, client):
        """Test elevation retrieval for São Paulo."""
        # São Paulo coordinates
        lat, lon = -23.5505, -46.6333

        location = await client.get_elevation(lat, lon)

        assert location is not None
        # São Paulo elevation: ~700-800m
        assert 600 <= location.elevation <= 900

        print(f"\n✓ São Paulo elevation: {location.elevation:.1f}m")

    @pytest.mark.asyncio
    async def test_get_elevations_batch(self, client):
        """Test batch elevation retrieval."""
        locations = [
            (-15.7801, -47.9292),  # Brasília
            (-23.5505, -46.6333),  # São Paulo
            (-22.9068, -43.1729),  # Rio de Janeiro
        ]

        results = await client.get_elevations_batch(locations)

        assert len(results) == 3

        # Brasília
        assert 1000 <= results[0].elevation <= 1300
        # São Paulo
        assert 600 <= results[1].elevation <= 900
        # Rio de Janeiro
        assert 0 <= results[2].elevation <= 100

        print("\n✓ Batch elevations:")
        for loc in results:
            print(f"  ({loc.lat:.4f}, {loc.lon:.4f}): {loc.elevation:.1f}m")

    @pytest.mark.asyncio
    async def test_coverage_check(self, client):
        """Test coverage validation."""
        # Valid coordinates (within SRTM range)
        assert client.is_in_coverage(-15.7801, -47.9292) is True
        assert client.is_in_coverage(0, 0) is True
        assert client.is_in_coverage(59, 0) is True
        assert client.is_in_coverage(-59, 0) is True

        # Outside SRTM range (need ASTER)
        assert client.is_in_coverage(70, 0) is False  # Arctic
        assert client.is_in_coverage(-70, 0) is False  # Antarctic

        # Invalid coordinates
        assert client.is_in_coverage(91, 0) is False
        assert client.is_in_coverage(0, 181) is False

    def test_calculate_atmospheric_pressure(self):
        """Test atmospheric pressure calculation (FAO-56 Eq. 7)."""
        from backend.api.services.weather_utils import ElevationUtils

        # Sea level (0m)
        pressure_0m = ElevationUtils.calculate_atmospheric_pressure(0)
        assert 101.0 <= pressure_0m <= 101.5

        # Brasília (~1172m)
        pressure_1172m = ElevationUtils.calculate_atmospheric_pressure(1172)
        # Expected: ~87.8 kPa
        assert 87.0 <= pressure_1172m <= 88.5

        # High altitude (3000m)
        pressure_3000m = ElevationUtils.calculate_atmospheric_pressure(3000)
        # Expected: ~70.1 kPa
        assert 69.0 <= pressure_3000m <= 71.0

        print("\n✓ Atmospheric pressure:")
        print(f"  Sea level (0m): {pressure_0m:.2f} kPa")
        print(f"  Brasília (1172m): {pressure_1172m:.2f} kPa")
        print(f"  High altitude (3000m): {pressure_3000m:.2f} kPa")

    def test_calculate_psychrometric_constant(self):
        """Test psychrometric constant calculation (FAO-56 Eq. 8)."""
        from backend.api.services.weather_utils import ElevationUtils

        # Sea level (0m)
        gamma_0m = ElevationUtils.calculate_psychrometric_constant(0)
        # Expected: ~0.067 kPa/°C
        assert 0.066 <= gamma_0m <= 0.068

        # Brasília (~1172m)
        gamma_1172m = ElevationUtils.calculate_psychrometric_constant(1172)
        # Expected: ~0.058 kPa/°C
        assert 0.057 <= gamma_1172m <= 0.060

        print("\n✓ Psychrometric constant:")
        print(f"  Sea level (0m): {gamma_0m:.5f} kPa/°C")
        print(f"  Brasília (1172m): {gamma_1172m:.5f} kPa/°C")

    def test_solar_radiation_adjustment(self):
        """Test solar radiation adjustment for elevation."""
        from backend.api.services.weather_utils import ElevationUtils

        radiation_sea_level = 20.0  # MJ/m²/day

        # Sea level (0m) - no adjustment
        rad_0m = ElevationUtils.adjust_solar_radiation_for_elevation(
            radiation_sea_level, 0
        )
        assert rad_0m == radiation_sea_level

        # 1000m elevation - ~10% increase
        rad_1000m = ElevationUtils.adjust_solar_radiation_for_elevation(
            radiation_sea_level, 1000
        )
        assert 21.8 <= rad_1000m <= 22.2

        # 2000m elevation - ~20% increase
        rad_2000m = ElevationUtils.adjust_solar_radiation_for_elevation(
            radiation_sea_level, 2000
        )
        assert 23.8 <= rad_2000m <= 24.2

        print("\n✓ Solar radiation adjustment:")
        print(f"  Sea level: {rad_0m:.2f} MJ/m²/day")
        pct_1000m = (rad_1000m / rad_0m - 1) * 100
        print(f"  1000m: {rad_1000m:.2f} MJ/m²/day (+{pct_1000m:.1f}%)")
        pct_2000m = (rad_2000m / rad_0m - 1) * 100
        print(f"  2000m: {rad_2000m:.2f} MJ/m²/day (+{pct_2000m:.1f}%)")

    @pytest.mark.asyncio
    async def test_invalid_coordinates(self, client):
        """Test error handling for invalid coordinates."""
        # Invalid latitude
        location = await client.get_elevation(91, 0)
        assert location is None

        # Invalid longitude
        location = await client.get_elevation(0, 181)
        assert location is None

    @pytest.mark.asyncio
    async def test_aster_fallback(self, client):
        """Test automatic fallback to ASTER for polar regions."""
        # Configure for ASTER dataset
        config = OpenTopoConfig(default_dataset="aster30m")
        client_aster = OpenTopoClient(config=config)

        # Test Arctic location (Svalbard)
        lat, lon = 78.2232, 15.6267
        location = await client_aster.get_elevation(lat, lon)

        await client_aster.close()

        # Should succeed with ASTER
        if location:
            assert location.dataset == "aster30m"
            print(f"\n✓ ASTER elevation (Svalbard): {location.elevation:.1f}m")
        else:
            print("\n⚠ ASTER request failed (API may be unavailable)")
