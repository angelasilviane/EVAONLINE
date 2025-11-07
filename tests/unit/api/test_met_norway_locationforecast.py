"""
Testes para MET Norway LocationForecast Sync Adapter.

MET Norway LocationForecast:
- GLOBAL: Funciona em qualquer coordenada mundial
- Previsão: Dia atual (hoje) + próximos 5 dias (padronizado)
- Dados horários que são agregados em dados diários
- Variáveis para ETo FAO-56: temperatura, umidade, vento, precipitação
- Licença: CC-BY 4.0 (atribuição obrigatória)

Documentação: https://docs.api.met.no/doc/locationforecast/datamodel.html

Author: AI Assistant
Date: November 4, 2025
"""

import pytest
from datetime import datetime, timedelta

from backend.api.services.met_norway_sync_adapter import (
    METNorwayLocationForecastSyncAdapter,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def met_norway_adapter():
    """Fixture do adapter MET Norway LocationForecast."""
    return METNorwayLocationForecastSyncAdapter()


@pytest.fixture
def test_locations():
    """Localizações globais para teste."""
    return {
        # Brasil (América do Sul)
        "brasilia": {"lat": -15.7939, "lon": -47.8828, "name": "Brasília, BR"},
        "sao_paulo": {
            "lat": -23.5505,
            "lon": -46.6333,
            "name": "São Paulo, BR",
        },
        # Europa (onde MET Norway está baseado)
        "oslo": {"lat": 59.9139, "lon": 10.7522, "name": "Oslo, NO"},
        "london": {"lat": 51.5074, "lon": -0.1278, "name": "London, UK"},
        # Ásia
        "tokyo": {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo, JP"},
        # América do Norte
        "new_york": {"lat": 40.7128, "lon": -74.0060, "name": "New York, US"},
        # África
        "cairo": {"lat": 30.0444, "lon": 31.2357, "name": "Cairo, EG"},
        # Oceania
        "sydney": {"lat": -33.8688, "lon": 151.2093, "name": "Sydney, AU"},
    }


# ============================================================================
# TESTES BÁSICOS - Downloads em Múltiplas Localizações Globais
# ============================================================================


class TestMETNorwayLocationForecastBasic:
    """Testes básicos de download de dados."""

    @pytest.mark.parametrize(
        "location_key",
        ["brasilia", "oslo", "tokyo", "new_york"],
    )
    def test_download_forecast_global(
        self, met_norway_adapter, test_locations, location_key
    ):
        """
        Testa download de previsão para diferentes localizações globais.

        MET Norway LocationForecast é GLOBAL e deve funcionar em qualquer lugar.
        """
        loc = test_locations[location_key]

        # Período: hoje + próximos 5 dias (limite padronizado)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=5)

        # Download
        data = met_norway_adapter.get_daily_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        # Validações
        assert data is not None, f"Sem dados para {loc['name']}"
        assert len(data) > 0, f"Lista vazia para {loc['name']}"

        # MET Norway deve retornar pelo menos alguns dias
        # (podem ser menos que 5 dependendo da hora)
        assert len(data) >= 1, f"Esperado >= 1 dia para {loc['name']}"

        # Verificar primeiro registro
        first = data[0]
        assert hasattr(first, "date"), "Falta campo 'date'"
        assert hasattr(first, "temp_max"), "Falta campo 'temp_max'"
        assert hasattr(first, "temp_min"), "Falta campo 'temp_min'"
        assert hasattr(first, "temp_mean"), "Falta campo 'temp_mean'"

        print(f"\n✅ {loc['name']}: {len(data)} dias obtidos")
        print(f"   Primeiro dia: {first.date.date()}")
        print(f"   Temp: {first.temp_min}°C a {first.temp_max}°C")

    def test_forecast_ten_days(self, met_norway_adapter, test_locations):
        """
        Testa previsão de 5 dias (limite padronizado).

        Todas as APIs de forecast foram padronizadas para 5 dias.
        """
        loc = test_locations["brasilia"]

        # Período: hoje + próximos 5 dias
        start_date = datetime.now()
        end_date = start_date + timedelta(days=5)

        # Download
        data = met_norway_adapter.get_daily_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        # Validações
        assert data is not None
        assert len(data) > 0

        # Deve retornar dados (pode ser menos de 5 dias)
        assert len(data) >= 1, "Esperado pelo menos 1 dia de forecast"

        print(f"\n✅ Forecast 5 dias: {len(data)} dias obtidos")

    def test_southern_hemisphere(self, met_norway_adapter, test_locations):
        """
        Testa funcionamento no hemisfério sul (Brasil, Austrália).

        Garante que não há limitação geográfica.
        """
        locations = ["sao_paulo", "sydney"]

        for loc_key in locations:
            loc = test_locations[loc_key]

            start_date = datetime.now()
            end_date = start_date + timedelta(days=5)

            data = met_norway_adapter.get_daily_data_sync(
                lat=loc["lat"],
                lon=loc["lon"],
                start_date=start_date,
                end_date=end_date,
            )

            assert data is not None
            assert len(data) > 0, f"Sem dados para {loc['name']}"

            print(f"✅ {loc['name']}: {len(data)} dias (hemisfério sul)")


# ============================================================================
# TESTES DE QUALIDADE DE DADOS
# ============================================================================


class TestMETNorwayDataQuality:
    """Testes de qualidade e consistência dos dados."""

    def test_temperature_ranges(self, met_norway_adapter, test_locations):
        """Valida ranges de temperatura (°C)."""
        loc = test_locations["brasilia"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = met_norway_adapter.get_daily_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0

        for record in data:
            # Temperaturas devem estar em range razoável
            if record.temp_max is not None:
                assert (
                    -50 <= record.temp_max <= 60
                ), f"temp_max fora do range: {record.temp_max}°C"

            if record.temp_min is not None:
                assert (
                    -50 <= record.temp_min <= 60
                ), f"temp_min fora do range: {record.temp_min}°C"

            if record.temp_mean is not None:
                assert (
                    -50 <= record.temp_mean <= 60
                ), f"temp_mean fora do range: {record.temp_mean}°C"

            # temp_min <= temp_max
            if record.temp_min is not None and record.temp_max is not None:
                assert (
                    record.temp_min <= record.temp_max
                ), f"temp_min ({record.temp_min}) > temp_max ({record.temp_max})"

        print(f"\n✅ Ranges de temperatura validados para {len(data)} dias")

    def test_humidity_ranges(self, met_norway_adapter, test_locations):
        """Valida ranges de umidade relativa (%)."""
        loc = test_locations["oslo"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = met_norway_adapter.get_daily_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0

        for record in data:
            if record.humidity_mean is not None:
                assert (
                    0 <= record.humidity_mean <= 100
                ), f"humidity fora do range: {record.humidity_mean}%"

        print(f"\n✅ Ranges de umidade validados para {len(data)} dias")

    def test_wind_speed_ranges(self, met_norway_adapter, test_locations):
        """Valida ranges de velocidade do vento (m/s)."""
        loc = test_locations["london"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = met_norway_adapter.get_daily_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0

        for record in data:
            if record.wind_speed_mean is not None:
                assert (
                    0 <= record.wind_speed_mean <= 100
                ), f"wind_speed fora do range: {record.wind_speed_mean} m/s"

        print(f"\n✅ Ranges de vento validados para {len(data)} dias")

    def test_precipitation_non_negative(
        self, met_norway_adapter, test_locations
    ):
        """Valida que precipitação não é negativa."""
        loc = test_locations["cairo"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = met_norway_adapter.get_daily_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0

        for record in data:
            if record.precipitation_sum is not None:
                assert (
                    record.precipitation_sum >= 0
                ), f"Precipitação negativa: {record.precipitation_sum} mm"

        print(f"\n✅ Precipitação validada para {len(data)} dias")


# ============================================================================
# TESTES DE VARIÁVEIS PARA ETo FAO-56
# ============================================================================


class TestMETNorwayEToVariables:
    """Testa variáveis necessárias para cálculo de ETo FAO-56."""

    def test_eto_variables_presence(self, met_norway_adapter, test_locations):
        """
        Valida presença das variáveis necessárias para ETo FAO-56.

        Variáveis necessárias:
        - Temperatura (max, min, mean)
        - Umidade relativa
        - Velocidade do vento
        - Radiação solar (ou dados para estimar)
        - Precipitação
        """
        loc = test_locations["brasilia"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = met_norway_adapter.get_daily_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0

        # Contar quantos registros têm cada variável
        counts = {
            "temp_max": 0,
            "temp_min": 0,
            "temp_mean": 0,
            "humidity_mean": 0,
            "wind_speed_mean": 0,
            "precipitation_sum": 0,
        }

        for record in data:
            if record.temp_max is not None:
                counts["temp_max"] += 1
            if record.temp_min is not None:
                counts["temp_min"] += 1
            if record.temp_mean is not None:
                counts["temp_mean"] += 1
            if record.humidity_mean is not None:
                counts["humidity_mean"] += 1
            if record.wind_speed_mean is not None:
                counts["wind_speed_mean"] += 1
            if record.precipitation_sum is not None:
                counts["precipitation_sum"] += 1

        print(f"\n✅ Variáveis ETo FAO-56 (de {len(data)} dias):")
        for var, count in counts.items():
            pct = (count / len(data)) * 100
            print(f"   {var}: {count}/{len(data)} ({pct:.1f}%)")

        # Pelo menos temperatura deve estar presente
        assert counts["temp_max"] > 0, "Falta temp_max"
        assert counts["temp_min"] > 0, "Falta temp_min"


# ============================================================================
# TESTES DE LIMITES E EDGE CASES
# ============================================================================


class TestMETNorwayEdgeCases:
    """Testes de casos extremos e limites."""

    def test_invalid_coordinates(self, met_norway_adapter):
        """Testa rejeição de coordenadas inválidas."""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=1)

        # Latitude inválida
        with pytest.raises((ValueError, Exception)):
            met_norway_adapter.get_daily_data_sync(
                lat=91.0,  # > 90
                lon=0.0,
                start_date=start_date,
                end_date=end_date,
            )

        # Longitude inválida
        with pytest.raises((ValueError, Exception)):
            met_norway_adapter.get_daily_data_sync(
                lat=0.0,
                lon=181.0,  # > 180
                start_date=start_date,
                end_date=end_date,
            )

        print("\n✅ Coordenadas inválidas rejeitadas corretamente")

    def test_single_day_forecast(self, met_norway_adapter, test_locations):
        """Testa download de apenas 1 dia (hoje)."""
        loc = test_locations["brasilia"]

        today = datetime.now()

        data = met_norway_adapter.get_daily_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=today,
            end_date=today,
        )

        # Deve retornar pelo menos 1 dia
        assert data is not None
        assert len(data) >= 1

        print(f"\n✅ Single day forecast: {len(data)} dia(s) obtido(s)")

    def test_extreme_latitudes(self, met_norway_adapter):
        """
        Testa funcionamento em latitudes extremas.

        Ártico (>66°N) e Antártico (<-66°S).
        """
        locations = [
            {"lat": 70.0, "lon": 20.0, "name": "Ártico"},
            {"lat": -70.0, "lon": 20.0, "name": "Antártico"},
        ]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        for loc in locations:
            data = met_norway_adapter.get_daily_data_sync(
                lat=loc["lat"],
                lon=loc["lon"],
                start_date=start_date,
                end_date=end_date,
            )

            # Pode retornar dados ou lista vazia (dependendo da cobertura)
            assert data is not None
            print(f"✅ {loc['name']}: {len(data)} dias (latitude extrema)")


# ============================================================================
# TESTE DE HEALTH CHECK
# ============================================================================


class TestMETNorwayHealthCheck:
    """Testes de health check da API."""

    def test_health_check(self, met_norway_adapter):
        """Valida que a API está acessível."""
        is_healthy = met_norway_adapter.health_check_sync()

        assert is_healthy, "MET Norway LocationForecast API não está acessível"

        print("\n✅ MET Norway LocationForecast: API saudável")


# ============================================================================
# TESTES DE COBERTURA E INFORMAÇÕES
# ============================================================================


class TestMETNorwayCoverage:
    """Testes de informações de cobertura."""

    def test_coverage_info(self, met_norway_adapter):
        """Valida informações de cobertura global."""
        info = met_norway_adapter.get_coverage_info()

        assert info is not None
        assert info["coverage"] == "GLOBAL"
        assert info["bbox"]["lat_min"] == -90
        assert info["bbox"]["lat_max"] == 90
        assert info["bbox"]["lon_min"] == -180
        assert info["bbox"]["lon_max"] == 180

        print("\n✅ Cobertura: GLOBAL")
        print(f"   Licença: {info['license']}")
        print(f"   Atribuição: {info['attribution']}")


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])
