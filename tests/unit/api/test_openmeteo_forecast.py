"""
Testes para Open-Meteo Forecast Sync Adapter.

Open-Meteo Forecast:
- GLOBAL: Funciona em qualquer coordenada mundial
- Dados recentes: até 90 dias no passado
- Previsão: até 5 dias no futuro (padronizado)
- Dados diários com variáveis meteorológicas
- API gratuita e sem necessidade de autenticação

Documentação: https://open-meteo.com/en/docs

Author: AI Assistant
Date: November 4, 2025
"""

import pytest
from datetime import datetime, timedelta

from backend.api.services.openmeteo_forecast_sync_adapter import (
    OpenMeteoForecastSyncAdapter,
)


# ========================================================================
# FIXTURES
# ========================================================================


@pytest.fixture
def openmeteo_forecast_adapter():
    """Fixture do adapter Open-Meteo Forecast."""
    return OpenMeteoForecastSyncAdapter()


@pytest.fixture
def test_locations():
    """Localizações globais para teste."""
    return {
        # América do Sul
        "brasilia": {"lat": -15.7939, "lon": -47.8828, "name": "Brasília"},
        "buenos_aires": {
            "lat": -34.6037,
            "lon": -58.3816,
            "name": "Buenos Aires",
        },
        # Europa
        "paris": {"lat": 48.8566, "lon": 2.3522, "name": "Paris"},
        "berlin": {"lat": 52.5200, "lon": 13.4050, "name": "Berlin"},
        # Ásia
        "beijing": {"lat": 39.9042, "lon": 116.4074, "name": "Beijing"},
        # América do Norte
        "toronto": {"lat": 43.6532, "lon": -79.3832, "name": "Toronto"},
        # África
        "nairobi": {"lat": -1.2864, "lon": 36.8172, "name": "Nairobi"},
        # Oceania
        "wellington": {"lat": -41.2865, "lon": 174.7762, "name": "Wellington"},
    }


# ========================================================================
# TESTES BÁSICOS - Downloads de Previsões
# ========================================================================


class TestOpenMeteoForecastBasic:
    """Testes básicos de download de previsões."""

    @pytest.mark.parametrize(
        "location_key",
        ["brasilia", "paris", "beijing", "toronto"],
    )
    def test_download_forecast_global(
        self, openmeteo_forecast_adapter, test_locations, location_key
    ):
        """
        Testa download de previsão para diferentes localizações globais.

        Open-Meteo Forecast é GLOBAL e deve funcionar em qualquer lugar.
        """
        loc = test_locations[location_key]

        # Período: hoje + próximos 5 dias (limite padronizado)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=5)

        # Download
        data = openmeteo_forecast_adapter.get_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        # Validações
        assert data is not None, f"Sem dados para {loc['name']}"
        assert len(data) > 0, f"Lista vazia para {loc['name']}"

        # Deve retornar pelo menos alguns dias
        assert len(data) >= 1, f"Esperado >= 1 dia para {loc['name']}"

        # Verificar primeiro registro
        first = data[0]
        assert "date" in first, "Falta campo 'date'"

        print(f"\n✅ {loc['name']}: {len(data)} dias obtidos")
        print(f"   Primeiro dia: {first['date']}")

    def test_forecast_16_days(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """
        Testa previsão de 5 dias (limite padronizado).

        Todas as APIs de forecast foram padronizadas para 5 dias.
        """
        loc = test_locations["brasilia"]

        # Período: hoje + próximos 5 dias
        start_date = datetime.now()
        end_date = start_date + timedelta(days=5)

        # Download
        data = openmeteo_forecast_adapter.get_data_sync(
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

    def test_recent_data_past_week(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """
        Testa download de dados recentes (última semana).

        Open-Meteo Forecast suporta até 90 dias no passado.
        """
        loc = test_locations["brasilia"]

        # Período: últimos 5 dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)

        # Download
        data = openmeteo_forecast_adapter.get_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        # Validações
        assert data is not None
        assert len(data) > 0

        print(f"\n✅ Dados recentes (última semana): {len(data)} dias")

    def test_southern_hemisphere(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """
        Testa funcionamento no hemisfério sul.
        """
        locations = ["brasilia", "buenos_aires", "wellington"]

        for loc_key in locations:
            loc = test_locations[loc_key]

            start_date = datetime.now()
            end_date = start_date + timedelta(days=5)

            data = openmeteo_forecast_adapter.get_data_sync(
                lat=loc["lat"],
                lon=loc["lon"],
                start_date=start_date,
                end_date=end_date,
            )

            assert data is not None
            assert len(data) > 0, f"Sem dados para {loc['name']}"

            print(f"✅ {loc['name']}: {len(data)} dias (hemisfério sul)")


# ========================================================================
# TESTES DE QUALIDADE DE DADOS
# ========================================================================


class TestOpenMeteoForecastDataQuality:
    """Testes de qualidade e consistência dos dados."""

    def test_data_structure(self, openmeteo_forecast_adapter, test_locations):
        """Valida estrutura básica dos dados retornados."""
        loc = test_locations["paris"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = openmeteo_forecast_adapter.get_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0

        # Verificar que cada registro é um dicionário
        for record in data:
            assert isinstance(record, dict), "Registro deve ser dict"
            assert "date" in record, "Falta campo 'date'"

        print(f"\n✅ Estrutura de dados validada para {len(data)} dias")

    def test_temperature_data_presence(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """Valida presença de dados de temperatura."""
        loc = test_locations["berlin"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = openmeteo_forecast_adapter.get_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0

        # Contar quantos registros têm dados de temperatura
        temp_count = 0
        for record in data:
            # Open-Meteo pode ter diferentes nomes de campos
            if any(
                key in record
                for key in [
                    "temperature_2m_max",
                    "temperature_max",
                    "temp_max",
                ]
            ):
                temp_count += 1

        # Pelo menos alguns registros devem ter temperatura
        assert temp_count > 0, "Nenhum registro com dados de temperatura"

        print(f"\n✅ Temperatura presente em {temp_count}/{len(data)} dias")

    def test_non_null_dates(self, openmeteo_forecast_adapter, test_locations):
        """Valida que todas as datas são válidas."""
        loc = test_locations["beijing"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = openmeteo_forecast_adapter.get_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert len(data) > 0

        for record in data:
            assert record.get("date") is not None, "Data não pode ser null"

        print(f"\n✅ Todas as datas válidas para {len(data)} dias")


# ========================================================================
# TESTES DE LIMITES E EDGE CASES
# ========================================================================


class TestOpenMeteoForecastEdgeCases:
    """Testes de casos extremos e limites."""

    def test_single_day_forecast(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """Testa download de apenas 1 dia (hoje)."""
        loc = test_locations["brasilia"]

        today = datetime.now()

        data = openmeteo_forecast_adapter.get_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=today,
            end_date=today,
        )

        # Deve retornar pelo menos 1 dia
        assert data is not None
        assert len(data) >= 1

        print(f"\n✅ Single day forecast: {len(data)} dia(s) obtido(s)")

    def test_date_range_adjustment(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """
        Testa ajuste automático de datas fora do limite.

        Open-Meteo Forecast: -90 dias a +16 dias
        """
        loc = test_locations["toronto"]

        # Tentar período muito antigo (mais de 90 dias)
        start_date = datetime.now() - timedelta(days=100)
        end_date = datetime.now()

        # Deve ajustar automaticamente ou retornar dados
        data = openmeteo_forecast_adapter.get_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        # Pode retornar dados ajustados ou lista vazia
        assert data is not None
        print(f"\n✅ Ajuste de datas: {len(data)} dias retornados")

    def test_extreme_latitudes(self, openmeteo_forecast_adapter):
        """
        Testa funcionamento em latitudes extremas.
        """
        locations = [
            {"lat": 70.0, "lon": 20.0, "name": "Ártico"},
            {"lat": -70.0, "lon": 20.0, "name": "Antártico"},
        ]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        for loc in locations:
            data = openmeteo_forecast_adapter.get_data_sync(
                lat=loc["lat"],
                lon=loc["lon"],
                start_date=start_date,
                end_date=end_date,
            )

            # Pode retornar dados ou lista vazia
            assert data is not None
            print(f"✅ {loc['name']}: {len(data)} dias (latitude extrema)")

    def test_equator_crossing(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """
        Testa funcionamento em locais próximos ao equador.
        """
        loc = test_locations["nairobi"]

        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        data = openmeteo_forecast_adapter.get_data_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            start_date=start_date,
            end_date=end_date,
        )

        assert data is not None
        assert len(data) > 0

        print(f"\n✅ Equador: {len(data)} dias obtidos")


# ========================================================================
# TESTES DE HEALTH CHECK E MÉTODOS AUXILIARES
# ========================================================================


class TestOpenMeteoForecastHealth:
    """Testes de health check e métodos auxiliares."""

    def test_health_check(self, openmeteo_forecast_adapter):
        """Valida que a API está acessível."""
        is_healthy = openmeteo_forecast_adapter.health_check_sync()

        assert is_healthy, "Open-Meteo Forecast API não está acessível"

        print("\n✅ Open-Meteo Forecast: API saudável")

    def test_get_info(self, openmeteo_forecast_adapter):
        """Valida método get_info."""
        info = openmeteo_forecast_adapter.get_info()

        assert info is not None
        assert isinstance(info, dict)

        print("\n✅ Informações da API obtidas")
        print(f"   Nome: {info.get('name', 'N/A')}")

    def test_get_forecast_method(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """Testa método get_forecast_sync (atalho para previsões)."""
        loc = test_locations["brasilia"]

        # Pegar previsão dos próximos 5 dias (limite padronizado)
        data = openmeteo_forecast_adapter.get_forecast_sync(
            lat=loc["lat"],
            lon=loc["lon"],
            days=5,
        )

        assert data is not None
        assert len(data) > 0

        print(f"\n✅ get_forecast_sync: {len(data)} dias obtidos")


# ========================================================================
# TESTES DE INTEGRAÇÃO COM MÚLTIPLAS LOCALIZAÇÕES
# ========================================================================


class TestOpenMeteoForecastMultiLocation:
    """Testes com múltiplas localizações simultaneamente."""

    def test_multiple_locations_sequential(
        self, openmeteo_forecast_adapter, test_locations
    ):
        """
        Testa download sequencial para múltiplas localizações.
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)

        results = {}

        for loc_key in ["brasilia", "paris", "beijing"]:
            loc = test_locations[loc_key]

            data = openmeteo_forecast_adapter.get_data_sync(
                lat=loc["lat"],
                lon=loc["lon"],
                start_date=start_date,
                end_date=end_date,
            )

            results[loc_key] = len(data) if data else 0

        # Todas devem ter retornado dados
        for loc_key, count in results.items():
            assert count > 0, f"Sem dados para {loc_key}"

        print("\n✅ Múltiplas localizações:")
        for loc_key, count in results.items():
            print(f"   {loc_key}: {count} dias")


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])
