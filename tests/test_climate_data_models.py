"""
Testes para modelo ClimateData, APIVariables e funções de validação.

Testa:
- Modelo ClimateData (armazenamento flexível JSONB)
- Modelo APIVariables (mapeamento de variáveis)
- Validação de datas por API (api_limits)
- Harmonização de dados (data_storage)
- Salvamento e consulta de dados
"""

import pytest
from datetime import date, datetime, timedelta
from backend.database.models import ClimateData, APIVariables
from backend.core.data_sources.api_limits import (
    API_DATE_LIMITS,
    HISTORICAL_START_DATE,
    get_api_date_range,
    validate_dates_for_source,
    validate_period_duration,
    classify_request_type,
    get_available_sources_for_period,
)


# ==============================================================================
# TESTES DE CONSTANTES
# ==============================================================================


def test_historical_start_date():
    """Testa que data padrão de início é 01/01/1990."""
    assert HISTORICAL_START_DATE == date(1990, 1, 1)


def test_api_date_limits_structure():
    """Testa estrutura do dicionário API_DATE_LIMITS."""
    expected_apis = [
        "nasa_power",
        "openmeteo_archive",
        "openmeteo_forecast",
        "met_norway",
        "nws_forecast",
        "nws_stations",
    ]

    for api in expected_apis:
        assert api in API_DATE_LIMITS
        limits = API_DATE_LIMITS[api]
        assert "type" in limits
        assert "description" in limits
        assert "coverage" in limits


# ==============================================================================
# TESTES DE get_api_date_range()
# ==============================================================================


def test_get_api_date_range_nasa_power():
    """Testa range de datas para NASA POWER."""
    start, end = get_api_date_range("nasa_power")

    # Deve usar padrão 1990 (não 1981)
    assert start == date(1990, 1, 1)

    # Deve ser hoje - 2 dias
    expected_end = date.today() - timedelta(days=2)
    assert end == expected_end


def test_get_api_date_range_openmeteo_archive():
    """Testa range de datas para Open-Meteo Archive."""
    start, end = get_api_date_range("openmeteo_archive")

    # Deve usar padrão 1990
    assert start == date(1990, 1, 1)

    # Deve ser hoje - 5 dias
    expected_end = date.today() - timedelta(days=5)
    assert end == expected_end


def test_get_api_date_range_openmeteo_forecast():
    """Testa range de datas para Open-Meteo Forecast."""
    start, end = get_api_date_range("openmeteo_forecast")

    # Deve ser hoje - 30 dias
    expected_start = date.today() - timedelta(days=30)
    assert start == expected_start

    # Deve ser hoje + 16 dias
    expected_end = date.today() + timedelta(days=16)
    assert end == expected_end


def test_get_api_date_range_invalid_api():
    """Testa erro para API inválida."""
    with pytest.raises(ValueError, match="não reconhecida"):
        get_api_date_range("api_invalida")


# ==============================================================================
# TESTES DE validate_dates_for_source()
# ==============================================================================


def test_validate_dates_nasa_power_valid():
    """Testa validação com datas válidas para NASA POWER."""
    start = date(2020, 1, 1)
    end = date(2020, 12, 31)

    # Não deve lançar exceção
    result = validate_dates_for_source("nasa_power", start, end)
    assert result is True


def test_validate_dates_nasa_power_before_1990():
    """Testa erro quando data é anterior a 1990."""
    start = date(1980, 1, 1)  # Antes do padrão
    end = date(1980, 12, 31)

    with pytest.raises(ValueError, match="deve ser >= 01/01/1990"):
        validate_dates_for_source("nasa_power", start, end)


def test_validate_dates_nasa_power_future():
    """Testa erro quando data final é no futuro."""
    start = date(2020, 1, 1)
    end = date.today() + timedelta(days=10)  # Futuro

    with pytest.raises(ValueError, match="Data final deve ser <="):
        validate_dates_for_source("nasa_power", start, end)


def test_validate_dates_inverted():
    """Testa erro quando data inicial > data final."""
    start = date(2020, 12, 31)
    end = date(2020, 1, 1)  # Invertido

    with pytest.raises(ValueError, match="anterior à data final"):
        validate_dates_for_source("nasa_power", start, end)


def test_validate_dates_no_exception():
    """Testa modo sem exceção (retorna False)."""
    start = date(1980, 1, 1)
    end = date(1980, 12, 31)

    result = validate_dates_for_source(
        "nasa_power", start, end, raise_exception=False
    )

    assert result is False


# ==============================================================================
# TESTES DE validate_period_duration()
# ==============================================================================


def test_validate_period_realtime_valid():
    """Testa período válido para tempo real (7-30 dias)."""
    start = date.today() - timedelta(days=10)
    end = date.today()

    # Não deve lançar exceção
    validate_period_duration(start, end, is_historical=False)


def test_validate_period_realtime_too_short():
    """Testa erro para período < 7 dias."""
    start = date.today() - timedelta(days=3)
    end = date.today()

    with pytest.raises(ValueError, match="Período mínimo: 7 dias"):
        validate_period_duration(start, end, is_historical=False)


def test_validate_period_realtime_too_long():
    """Testa erro para período > 30 dias."""
    start = date.today() - timedelta(days=40)
    end = date.today()

    with pytest.raises(ValueError, match="máximo para tempo real: 30 dias"):
        validate_period_duration(start, end, is_historical=False)


def test_validate_period_historical_valid():
    """Testa período válido para histórico (até 90 dias)."""
    start = date(2020, 1, 1)
    end = date(2020, 3, 31)  # 90 dias

    # Não deve lançar exceção
    validate_period_duration(start, end, is_historical=True)


def test_validate_period_historical_too_long():
    """Testa erro para período > 90 dias."""
    start = date(2020, 1, 1)
    end = date(2020, 6, 1)  # > 90 dias

    with pytest.raises(ValueError, match="Limite de 90 dias"):
        validate_period_duration(start, end, is_historical=True)


# ==============================================================================
# TESTES DE classify_request_type()
# ==============================================================================


def test_classify_request_type_historical():
    """Testa classificação como histórico."""
    start = date(2020, 1, 1)  # Mais de 30 dias atrás
    end = date(2020, 12, 31)

    result = classify_request_type(start, end)
    assert result == "historical"


def test_classify_request_type_current():
    """Testa classificação como atual."""
    start = date.today() - timedelta(days=10)  # Menos de 30 dias
    end = date.today()

    result = classify_request_type(start, end)
    assert result == "current"


def test_classify_request_type_boundary():
    """Testa classificação no limite (30 dias)."""
    start = date.today() - timedelta(days=30)
    end = date.today()

    result = classify_request_type(start, end)
    # Exatamente 30 dias: deve ser 'current'
    assert result == "current"

    # 31 dias: deve ser 'historical'
    start = date.today() - timedelta(days=31)
    result = classify_request_type(start, end)
    assert result == "historical"


# ==============================================================================
# TESTES DE get_available_sources_for_period()
# ==============================================================================


def test_get_available_sources_historical():
    """Testa fontes disponíveis para período histórico."""
    start = date(2020, 1, 1)
    end = date(2020, 12, 31)

    available = get_available_sources_for_period(start, end)

    # Deve ter apenas históricos
    assert "nasa_power" in available["historical"]
    assert "openmeteo_archive" in available["historical"]
    assert len(available["forecast"]) == 0
    assert len(available["current"]) == 0


def test_get_available_sources_forecast():
    """Testa fontes disponíveis para período futuro."""
    start = date.today()
    end = date.today() + timedelta(days=5)

    available = get_available_sources_for_period(start, end)

    # Deve ter forecast
    assert "openmeteo_forecast" in available["forecast"]
    # Pode ter met_norway e nws_forecast dependendo da data


# ==============================================================================
# TESTES DE MODELOS (necessitam banco de dados)
# ==============================================================================


@pytest.mark.skip(reason="Requer banco de dados configurado")
def test_climate_data_model():
    """Testa criação de objeto ClimateData."""
    climate = ClimateData(
        source_api="nasa_power",
        latitude=-23.55,
        longitude=-46.63,
        elevation=760.0,
        timezone="America/Sao_Paulo",
        date=datetime(2020, 1, 1),
        raw_data={"T2M_MAX": 28.5},
        harmonized_data={"temp_max_c": 28.5},
        eto_mm_day=4.5,
    )

    assert climate.source_api == "nasa_power"
    assert climate.latitude == -23.55
    assert climate.eto_mm_day == 4.5


@pytest.mark.skip(reason="Requer banco de dados configurado")
def test_api_variables_model():
    """Testa criação de objeto APIVariables."""
    var = APIVariables(
        source_api="nasa_power",
        variable_name="T2M_MAX",
        standard_name="temp_max_c",
        unit="°C",
        description="Temperatura máxima",
        is_required_for_eto=True,
    )

    assert var.source_api == "nasa_power"
    assert var.variable_name == "T2M_MAX"
    assert var.is_required_for_eto is True


# ==============================================================================
# EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
