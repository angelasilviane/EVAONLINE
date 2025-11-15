"""
Testes unitários para validar as correções implementadas nos serviços climáticos.

Valida:
1. GeographicUtils como SINGLE SOURCE OF TRUTH
2. Método is_in_bbox para validação de bounding boxes
3. normalize_operation_mode para conversão consistente
4. _is_point_covered usando GeographicUtils
5. Eliminação de código duplicado
6. Consistência entre módulos climáticos
"""

import pytest

from backend.api.services.geographic_utils import GeographicUtils
from backend.api.services.climate_source_selector import (
    ClimateSourceSelector,
)
from backend.api.services.climate_source_manager import (
    ClimateSourceManager,
    normalize_operation_mode,
)
from backend.api.services.climate_source_availability import (
    OperationMode,
)
from backend.api.services.climate_validation import (
    ClimateValidationService,
)


class TestGeographicUtilsCorrections:
    """Testes para validar GeographicUtils como SINGLE SOURCE OF TRUTH."""

    def test_bbox_constants_defined(self):
        """Verifica que os bounding boxes estão definidos corretamente."""
        assert GeographicUtils.USA_BBOX == (-125.0, 24.0, -66.0, 49.0)
        assert GeographicUtils.NORDIC_BBOX == (4.0, 54.0, 31.0, 71.5)
        assert GeographicUtils.GLOBAL_BBOX == (-180.0, -90.0, 180.0, 90.0)

    def test_is_in_usa_detection(self):
        """Testa detecção de coordenadas USA."""
        # Dentro dos USA
        assert GeographicUtils.is_in_usa(40.7128, -74.0060)  # NYC
        assert GeographicUtils.is_in_usa(34.0522, -118.2437)  # LA
        assert GeographicUtils.is_in_usa(39.7392, -104.9903)  # Denver

        # Fora dos USA
        assert not GeographicUtils.is_in_usa(51.5074, -0.1278)  # London
        assert not GeographicUtils.is_in_usa(-15.7939, -47.8828)  # Brasília
        assert not GeographicUtils.is_in_usa(59.9139, 10.7522)  # Oslo

    def test_is_in_nordic_detection(self):
        """Testa detecção de coordenadas Nordic."""
        # Dentro da região Nórdica
        assert GeographicUtils.is_in_nordic(59.9139, 10.7522)  # Oslo
        assert GeographicUtils.is_in_nordic(60.1699, 24.9384)  # Helsinki
        assert GeographicUtils.is_in_nordic(55.6761, 12.5683)  # Copenhagen

        # Fora da região Nórdica
        assert not GeographicUtils.is_in_nordic(48.8566, 2.3522)  # Paris
        assert not GeographicUtils.is_in_nordic(40.7128, -74.0060)  # NYC
        assert not GeographicUtils.is_in_nordic(-15.7939, -47.8828)  # Brasília

    def test_is_valid_coordinate(self):
        """Testa validação de coordenadas globais."""
        # Coordenadas válidas
        assert GeographicUtils.is_valid_coordinate(0, 0)
        assert GeographicUtils.is_valid_coordinate(40.7, -74.0)
        assert GeographicUtils.is_valid_coordinate(-90, -180)
        assert GeographicUtils.is_valid_coordinate(90, 180)
        assert GeographicUtils.is_valid_coordinate(-23.5505, -46.6333)

        # Coordenadas inválidas
        assert not GeographicUtils.is_valid_coordinate(91, 0)
        assert not GeographicUtils.is_valid_coordinate(-91, 0)
        assert not GeographicUtils.is_valid_coordinate(0, 181)
        assert not GeographicUtils.is_valid_coordinate(0, -181)
        assert not GeographicUtils.is_valid_coordinate(200, 200)

    def test_is_in_bbox_new_method(self):
        """Testa novo método is_in_bbox para validação de bounding boxes."""
        # Dentro do bbox USA
        assert GeographicUtils.is_in_bbox(
            40.7128, -74.0060, GeographicUtils.USA_BBOX
        )
        assert GeographicUtils.is_in_bbox(
            34.0522, -118.2437, GeographicUtils.USA_BBOX
        )

        # Fora do bbox USA
        assert not GeographicUtils.is_in_bbox(
            51.5074, -0.1278, GeographicUtils.USA_BBOX
        )
        assert not GeographicUtils.is_in_bbox(
            -15.7939, -47.8828, GeographicUtils.USA_BBOX
        )

        # Dentro do bbox Nordic
        assert GeographicUtils.is_in_bbox(
            59.9139, 10.7522, GeographicUtils.NORDIC_BBOX
        )

        # Fora do bbox Nordic
        assert not GeographicUtils.is_in_bbox(
            48.8566, 2.3522, GeographicUtils.NORDIC_BBOX
        )

        # Coordenadas inválidas devem retornar False
        assert not GeographicUtils.is_in_bbox(
            200, 200, GeographicUtils.USA_BBOX
        )
        assert not GeographicUtils.is_in_bbox(
            -200, -200, GeographicUtils.NORDIC_BBOX
        )

    def test_get_region(self):
        """Testa detecção de região com prioridade."""
        assert GeographicUtils.get_region(40.7128, -74.0060) == "usa"
        assert GeographicUtils.get_region(59.9139, 10.7522) == "nordic"
        assert GeographicUtils.get_region(-15.7939, -47.8828) == "global"
        assert GeographicUtils.get_region(48.8566, 2.3522) == "global"


class TestNormalizeOperationMode:
    """Testes para função normalize_operation_mode centralizada."""

    def test_normalize_historical_variants(self):
        """Testa normalização de variantes históricas."""
        assert (
            normalize_operation_mode("historical")
            == OperationMode.HISTORICAL_EMAIL
        )
        assert (
            normalize_operation_mode("historical_email")
            == OperationMode.HISTORICAL_EMAIL
        )
        assert (
            normalize_operation_mode("HISTORICAL")
            == OperationMode.HISTORICAL_EMAIL
        )

    def test_normalize_dashboard_variants(self):
        """Testa normalização de variantes dashboard."""
        assert (
            normalize_operation_mode("dashboard")
            == OperationMode.DASHBOARD_CURRENT
        )
        assert (
            normalize_operation_mode("dashboard_current")
            == OperationMode.DASHBOARD_CURRENT
        )
        assert (
            normalize_operation_mode("DASHBOARD")
            == OperationMode.DASHBOARD_CURRENT
        )

    def test_normalize_forecast_variants(self):
        """Testa normalização de variantes forecast."""
        assert (
            normalize_operation_mode("forecast")
            == OperationMode.DASHBOARD_FORECAST
        )
        assert (
            normalize_operation_mode("dashboard_forecast")
            == OperationMode.DASHBOARD_FORECAST
        )
        assert (
            normalize_operation_mode("FORECAST")
            == OperationMode.DASHBOARD_FORECAST
        )

    def test_normalize_none_default(self):
        """Testa normalização com None retorna default."""
        assert (
            normalize_operation_mode(None) == OperationMode.DASHBOARD_CURRENT
        )

    def test_normalize_invalid_default(self):
        """Testa normalização com valor inválido retorna default."""
        assert (
            normalize_operation_mode("invalid")
            == OperationMode.DASHBOARD_CURRENT
        )
        assert normalize_operation_mode("") == OperationMode.DASHBOARD_CURRENT
        assert (
            normalize_operation_mode("unknown_mode")
            == OperationMode.DASHBOARD_CURRENT
        )


class TestClimateSourceManagerCorrections:
    """Testes para ClimateSourceManager após correções."""

    def test_initialization(self):
        """Testa inicialização do manager."""
        manager = ClimateSourceManager()
        assert len(manager.enabled_sources) > 0
        assert "nws_forecast" in manager.enabled_sources
        assert "nws_stations" in manager.enabled_sources
        assert "met_norway" in manager.enabled_sources
        assert "nasa_power" in manager.enabled_sources

    def test_bbox_consistency_with_geographic_utils(self):
        """Verifica que manager usa GeographicUtils.USA_BBOX."""
        manager = ClimateSourceManager()

        # NWS Forecast deve usar GeographicUtils.USA_BBOX
        nws_forecast_bbox = manager.enabled_sources["nws_forecast"]["bbox"]
        assert nws_forecast_bbox == GeographicUtils.USA_BBOX

        # NWS Stations deve usar GeographicUtils.USA_BBOX
        nws_stations_bbox = manager.enabled_sources["nws_stations"]["bbox"]
        assert nws_stations_bbox == GeographicUtils.USA_BBOX

    def test_is_point_covered_global(self):
        """Testa _is_point_covered para cobertura global."""
        manager = ClimateSourceManager()
        metadata_global = {"bbox": None}

        # Coordenadas válidas devem estar cobertas
        assert manager._is_point_covered(0, 0, metadata_global)
        assert manager._is_point_covered(40.7, -74.0, metadata_global)
        assert manager._is_point_covered(-23.5, -46.6, metadata_global)

        # Coordenadas inválidas não devem estar cobertas
        assert not manager._is_point_covered(200, 200, metadata_global)

    def test_is_point_covered_usa_bbox(self):
        """Testa _is_point_covered com USA bbox usando GeographicUtils."""
        manager = ClimateSourceManager()
        metadata_usa = {"bbox": GeographicUtils.USA_BBOX}

        # Dentro do bbox USA
        assert manager._is_point_covered(40.7128, -74.0060, metadata_usa)
        assert manager._is_point_covered(34.0522, -118.2437, metadata_usa)

        # Fora do bbox USA
        assert not manager._is_point_covered(51.5074, -0.1278, metadata_usa)
        assert not manager._is_point_covered(-15.7939, -47.8828, metadata_usa)

        # Coordenadas inválidas
        assert not manager._is_point_covered(200, 200, metadata_usa)

    def test_is_point_covered_nordic_bbox(self):
        """Testa _is_point_covered com Nordic bbox."""
        manager = ClimateSourceManager()
        metadata_nordic = {"bbox": GeographicUtils.NORDIC_BBOX}

        # Dentro do bbox Nordic
        assert manager._is_point_covered(59.9139, 10.7522, metadata_nordic)
        assert manager._is_point_covered(60.1699, 24.9384, metadata_nordic)

        # Fora do bbox Nordic
        assert not manager._is_point_covered(48.8566, 2.3522, metadata_nordic)
        assert not manager._is_point_covered(
            40.7128, -74.0060, metadata_nordic
        )

    def test_get_available_sources(self):
        """Testa obtenção de fontes disponíveis para localização."""
        manager = ClimateSourceManager()

        # NYC - deve ter NWS + fontes globais
        sources_nyc = manager.get_available_sources(40.7128, -74.0060)
        assert len(sources_nyc) >= 4
        source_ids = [s["id"] for s in sources_nyc]
        assert "nws_forecast" in source_ids
        assert "nws_stations" in source_ids

        # Oslo - deve ter fontes globais (não USA)
        sources_oslo = manager.get_available_sources(59.9139, 10.7522)
        assert len(sources_oslo) >= 3
        source_ids = [s["id"] for s in sources_oslo]
        assert "nws_forecast" not in source_ids


class TestIntegrationConsistency:
    """Testes de integração para verificar consistência entre módulos."""

    def test_geographic_detection_consistency(self):
        """Verifica consistência de detecção geográfica entre módulos."""
        # NYC
        lat, lon = 40.7128, -74.0060

        # GeographicUtils
        in_usa = GeographicUtils.is_in_usa(lat, lon)
        region = GeographicUtils.get_region(lat, lon)

        # ClimateSourceSelector
        source = ClimateSourceSelector.select_source(lat, lon)

        # Consistência: se está nos USA, fonte deve ser NWS
        assert in_usa is True
        assert region == "usa"
        assert source == "nws_forecast"

    def test_nordic_detection_consistency(self):
        """Verifica consistência de detecção Nordic entre módulos."""
        # Oslo
        lat, lon = 59.9139, 10.7522

        # GeographicUtils
        in_nordic = GeographicUtils.is_in_nordic(lat, lon)
        region = GeographicUtils.get_region(lat, lon)

        # ClimateSourceSelector
        source = ClimateSourceSelector.select_source(lat, lon)

        # Consistência: se está no Nordic, fonte deve ser MET Norway
        assert in_nordic is True
        assert region == "nordic"
        assert source == "met_norway"

    def test_global_detection_consistency(self):
        """Verifica consistência de detecção global entre módulos."""
        # Brasília
        lat, lon = -15.7939, -47.8828

        # GeographicUtils
        in_usa = GeographicUtils.is_in_usa(lat, lon)
        in_nordic = GeographicUtils.is_in_nordic(lat, lon)
        region = GeographicUtils.get_region(lat, lon)

        # ClimateSourceSelector
        source = ClimateSourceSelector.select_source(lat, lon)

        # Consistência: se não está em USA/Nordic, fonte deve ser global
        assert in_usa is False
        assert in_nordic is False
        assert region == "global"
        assert source == "openmeteo_forecast"

    def test_bbox_consistency_across_modules(self):
        """Verifica que todos os módulos usam os mesmos bounding boxes."""
        manager = ClimateSourceManager()

        # Verificar que NWS usa GeographicUtils.USA_BBOX
        nws_forecast_bbox = manager.enabled_sources["nws_forecast"]["bbox"]
        nws_stations_bbox = manager.enabled_sources["nws_stations"]["bbox"]

        assert nws_forecast_bbox == GeographicUtils.USA_BBOX
        assert nws_stations_bbox == GeographicUtils.USA_BBOX

        # Verificar consistência
        assert nws_forecast_bbox == nws_stations_bbox

    def test_validation_with_geographic_utils(self):
        """Testa que validação usa GeographicUtils corretamente."""
        # Coordenadas válidas
        valid, details = ClimateValidationService.validate_coordinates(
            40.7128, -74.0060
        )
        assert valid is True

        # Verificar com GeographicUtils
        assert GeographicUtils.is_valid_coordinate(40.7128, -74.0060)

        # Coordenadas inválidas
        invalid, details = ClimateValidationService.validate_coordinates(
            200, 200
        )
        assert invalid is False

        # Verificar com GeographicUtils
        assert not GeographicUtils.is_valid_coordinate(200, 200)


class TestCodeDuplicationElimination:
    """Testes para verificar que código duplicado foi eliminado."""

    def test_no_hardcoded_usa_bbox(self):
        """Verifica que não há USA_BBOX hardcoded em climate_source_manager."""
        manager = ClimateSourceManager()

        # Todos os bboxes USA devem vir de GeographicUtils
        for source_id, metadata in manager.enabled_sources.items():
            if metadata.get("coverage") == "usa":
                bbox = metadata.get("bbox")
                if bbox:
                    # Deve ser igual a GeographicUtils.USA_BBOX
                    assert bbox == GeographicUtils.USA_BBOX

    def test_is_point_covered_uses_geographic_utils(self):
        """Verifica que _is_point_covered usa GeographicUtils.is_in_bbox."""
        manager = ClimateSourceManager()

        # Teste com bbox USA
        metadata = {"bbox": GeographicUtils.USA_BBOX}
        result_manager = manager._is_point_covered(40.7128, -74.0060, metadata)
        result_geo = GeographicUtils.is_in_bbox(
            40.7128, -74.0060, GeographicUtils.USA_BBOX
        )

        # Resultados devem ser consistentes
        assert result_manager == result_geo

    def test_operation_mode_centralized(self):
        """Verifica que normalize_operation_mode está centralizado."""
        # Função deve estar disponível no módulo
        assert callable(normalize_operation_mode)

        # Deve retornar OperationMode enum
        result = normalize_operation_mode("historical")
        assert isinstance(result, OperationMode)
        assert result == OperationMode.HISTORICAL_EMAIL


class TestOperationModeConsistency:
    """Testes para verificar consistência de OperationMode."""

    def test_operation_mode_enum_values(self):
        """Verifica valores do enum OperationMode."""
        assert OperationMode.HISTORICAL_EMAIL.value == "historical_email"
        assert OperationMode.DASHBOARD_CURRENT.value == "dashboard_current"
        assert OperationMode.DASHBOARD_FORECAST.value == "dashboard_forecast"

    def test_validation_uses_operation_mode(self):
        """Verifica que validação usa OperationMode enum."""
        # Validar modo histórico
        valid, details = ClimateValidationService.validate_request_mode(
            "historical_email", "2024-01-01", "2024-01-10"
        )
        assert valid is True
        assert details["mode"] == OperationMode.HISTORICAL_EMAIL.value


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--durations=10"])
