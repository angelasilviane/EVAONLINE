"""
Testes para OpenTopoSyncAdapter.

Valida funcionalidade síncrona, auto-switching,
batch processing, e health checks.
"""

import pytest
from backend.api.services.opentopo.opentopo_sync_adapter import (
    OpenTopoSyncAdapter,
)


class TestOpenTopoSyncAdapter:
    """Testes para OpenTopoSyncAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create sync adapter instance."""
        return OpenTopoSyncAdapter()

    def test_adapter_initialization(self, adapter):
        """Test adapter initializes correctly."""
        assert adapter is not None
        assert adapter.config is not None
        assert adapter.config.default_dataset == "srtm30m"
        assert adapter.config.timeout == 15

    def test_get_elevation_sync_brasilia(self, adapter):
        """Test single elevation retrieval for Brasília (1172m)."""
        # Brasília coordinates: -15.7801, -47.9292
        location = adapter.get_elevation_sync(-15.7801, -47.9292)

        assert location is not None
        assert 1100 < location.elevation < 1250  # ~1172m
        assert location.lat is not None
        assert location.lon is not None
        assert location.dataset in ["srtm30m", "aster30m"]

    def test_get_elevation_sync_sao_paulo(self, adapter):
        """Test single elevation retrieval for São Paulo (829m)."""
        # São Paulo: -23.5505, -46.6333
        location = adapter.get_elevation_sync(-23.5505, -46.6333)

        assert location is not None
        assert 750 < location.elevation < 900  # ~829m
        assert location.dataset in ["srtm30m", "aster30m"]

    def test_get_elevation_sync_invalid_coords(self, adapter):
        """Test elevation retrieval with invalid coordinates."""
        location = adapter.get_elevation_sync(99.9999, 199.9999)
        assert location is None

    def test_is_in_coverage_sync_srtm_range(self, adapter):
        """Test coverage check for coordinates within SRTM range."""
        # Brasília is within SRTM range (-60 to +60)
        assert adapter.is_in_coverage_sync(-15.7801, -47.9292) is True

    def test_is_in_coverage_sync_outside_srtm(self, adapter):
        """Test coverage check for coordinates outside SRTM range."""
        # Latitude > 60 (outside SRTM, would trigger ASTER auto-switch)
        # Svalbard: 78.2232, 15.6267
        assert adapter.is_in_coverage_sync(78.2232, 15.6267) is False

    def test_get_elevations_batch_sync(self, adapter):
        """Test batch elevation retrieval."""
        locations = [
            (-15.7801, -47.9292),  # Brasília
            (-23.5505, -46.6333),  # São Paulo
        ]

        results = adapter.get_elevations_batch_sync(locations)

        assert len(results) == 2
        assert results[0].elevation > 0
        assert results[1].elevation > 0
        assert results[0].dataset in ["srtm30m", "aster30m"]

    def test_get_elevations_batch_sync_empty(self, adapter):
        """Test batch with empty locations list."""
        results = adapter.get_elevations_batch_sync([])
        assert results == []

    def test_health_check_sync(self, adapter):
        """Test health check."""
        is_healthy = adapter.health_check_sync()
        assert is_healthy is True

    def test_get_coverage_info(self, adapter):
        """Test coverage info retrieval."""
        info = adapter.get_coverage_info()

        assert "datasets" in info
        assert "srtm30m" in info["datasets"]
        assert "aster30m" in info["datasets"]
        assert "auto_switching" in info
        assert "rate_limits" in info
        assert "cache_strategy" in info

    def test_coverage_info_srtm_details(self, adapter):
        """Test SRTM dataset details in coverage info."""
        info = adapter.get_coverage_info()

        srtm = info["datasets"]["srtm30m"]
        assert srtm["coverage"]["lat_max"] == 60.0
        assert srtm["coverage"]["lat_min"] == -60.0
        assert srtm["default"] is True

    def test_coverage_info_aster_details(self, adapter):
        """Test ASTER dataset details in coverage info."""
        info = adapter.get_coverage_info()

        aster = info["datasets"]["aster30m"]
        assert aster["coverage"]["lat_max"] == 90.0
        assert aster["coverage"]["lat_min"] == -90.0
        assert aster["auto_fallback"] is True

    def test_coverage_info_auto_switching(self, adapter):
        """Test auto-switching info in coverage details."""
        info = adapter.get_coverage_info()

        auto_switch = info["auto_switching"]
        assert auto_switch["enabled"] is True
        assert "latitude > 60" in auto_switch["rule"]

    def test_coverage_info_rate_limits(self, adapter):
        """Test rate limit info in coverage details."""
        info = adapter.get_coverage_info()

        rate_limits = info["rate_limits"]
        assert rate_limits["requests_per_second"] == 1
        assert rate_limits["requests_per_day"] == 1000
        assert rate_limits["locations_per_request"] == 100

    def test_coverage_info_cache_strategy(self, adapter):
        """Test cache strategy info in coverage details."""
        info = adapter.get_coverage_info()

        cache = info["cache_strategy"]
        assert cache["ttl_seconds"] == 3600 * 24 * 30  # 30 days
        assert cache["precision_decimals"] == 6

    def test_coverage_info_fao56_calculations(self, adapter):
        """Test FAO-56 calculation information in coverage."""
        info = adapter.get_coverage_info()

        fao56 = info["fao56_calculations"]
        assert "atmospheric_pressure" in fao56
        assert "psychrometric_constant" in fao56
        assert "solar_radiation" in fao56
        assert "ElevationUtils" in fao56["location"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
