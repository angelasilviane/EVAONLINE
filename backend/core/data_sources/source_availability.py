"""
Detecta automaticamente fontes de dados disponíveis para localização e período.

Funções:
- get_available_sources(): Lista APIs disponíveis
- is_in_usa(): Verifica se coordenadas estão nos EUA
- is_in_nordic_region(): Verifica se está na região nórdica
- get_source_priority(): Retorna prioridade por qualidade regional
"""

from datetime import date
from typing import Dict, List, Tuple

from backend.core.data_sources.api_limits import validate_dates_for_source


# ==============================================================================
# DETECÇÃO DE REGIÃO GEOGRÁFICA
# ==============================================================================


def is_in_usa(latitude: float, longitude: float) -> bool:
    """
    Verifica se coordenadas estão nos Estados Unidos.

    Args:
        latitude: Latitude em graus decimais
        longitude: Longitude em graus decimais

    Returns:
        True se coordenadas estão nos EUA (incluindo Alaska e Havaí)

    Examples:
        >>> is_in_usa(40.7128, -74.0060)  # Nova York
        True
        >>> is_in_usa(-23.5505, -46.6333)  # São Paulo
        False
    """
    # USA continental: aproximadamente
    # Latitude: 24.5°N a 49.4°N
    # Longitude: -125°W a -66°W

    # Alaska: 51°N a 71°N, -180°W a -130°W
    # Havaí: 19°N a 22°N, -160°W a -154°W

    # USA Continental
    if 24.5 <= latitude <= 49.4 and -125.0 <= longitude <= -66.0:
        return True

    # Alaska
    if 51.0 <= latitude <= 71.0 and -180.0 <= longitude <= -130.0:
        return True

    # Havaí
    if 19.0 <= latitude <= 22.0 and -160.0 <= longitude <= -154.0:
        return True

    return False


def is_in_nordic_region(latitude: float, longitude: float) -> bool:
    """
    Verifica se coordenadas estão na região nórdica
    (alta cobertura MET Norway).

    Região: Noruega, Suécia, Finlândia, Dinamarca, Islândia

    Args:
        latitude: Latitude em graus decimais
        longitude: Longitude em graus decimais

    Returns:
        True se coordenadas estão na região nórdica

    Examples:
        >>> is_in_nordic_region(59.9139, 10.7522)  # Oslo, Noruega
        True
        >>> is_in_nordic_region(48.8566, 2.3522)  # Paris, França
        False
    """
    # Região Nórdica (aproximadamente):
    # Latitude: 54°N a 71°N (sul da Dinamarca ao norte da Noruega)
    # Longitude: -25°W a 31°E (Islândia ao leste da Finlândia)

    if 54.0 <= latitude <= 71.0 and -25.0 <= longitude <= 31.0:
        return True

    return False


def get_region_name(latitude: float, longitude: float) -> str:
    """
    Retorna nome da região para coordenadas.

    Args:
        latitude: Latitude
        longitude: Longitude

    Returns:
        'usa', 'nordic', ou 'global'
    """
    if is_in_usa(latitude, longitude):
        return "usa"
    elif is_in_nordic_region(latitude, longitude):
        return "nordic"
    else:
        return "global"


# ==============================================================================
# DISPONIBILIDADE DE FONTES
# ==============================================================================


def get_available_sources(
    latitude: float, longitude: float, start_date: date, end_date: date
) -> Dict[str, List[str]]:
    """
    Retorna fontes de dados disponíveis para localização e período.

    Args:
        latitude: Latitude em graus decimais
        longitude: Longitude em graus decimais
        start_date: Data inicial
        end_date: Data final

    Returns:
        Dict com 'historical', 'forecast', 'current' e 'recommended'

    Examples:
        # Dados históricos (qualquer lugar)
        >>> sources = get_available_sources(
        ...     -23.55, -46.63,
        ...     date(2020, 1, 1), date(2020, 12, 31)
        ... )
        >>> 'nasa_power' in sources['historical']
        True
        >>> sources['recommended']
        'nasa_power'

        # Forecast USA
        >>> sources = get_available_sources(
        ...     40.7128, -74.0060,  # Nova York
        ...     date.today(), date.today() + timedelta(days=5)
        ... )
        >>> 'nws_forecast' in sources['forecast']
        True
    """
    available = {
        "historical": [],
        "forecast": [],
        "current": [],
        "recommended": None,
    }

    region = get_region_name(latitude, longitude)

    # =========================================================================
    # DADOS HISTÓRICOS (sempre disponíveis globalmente)
    # =========================================================================
    try:
        if validate_dates_for_source(
            "nasa_power", start_date, end_date, raise_exception=False
        ):
            available["historical"].append("nasa_power")
    except Exception:
        pass

    try:
        if validate_dates_for_source(
            "openmeteo_archive", start_date, end_date, raise_exception=False
        ):
            available["historical"].append("openmeteo_archive")
    except Exception:
        pass

    # =========================================================================
    # FORECAST (depende da região)
    # =========================================================================

    # Open-Meteo Forecast: GLOBAL
    try:
        if validate_dates_for_source(
            "openmeteo_forecast", start_date, end_date, raise_exception=False
        ):
            available["forecast"].append("openmeteo_forecast")
    except Exception:
        pass

    # NWS Forecast: USA apenas
    if region == "usa":
        try:
            if validate_dates_for_source(
                "nws_forecast", start_date, end_date, raise_exception=False
            ):
                available["forecast"].append("nws_forecast")
        except Exception:
            pass

    # MET Norway: Região Nórdica
    if region == "nordic":
        try:
            if validate_dates_for_source(
                "met_norway", start_date, end_date, raise_exception=False
            ):
                available["forecast"].append("met_norway")
        except Exception:
            pass

    # =========================================================================
    # CURRENT (real-time)
    # =========================================================================

    # NWS Stations: USA apenas
    if region == "usa":
        try:
            if validate_dates_for_source(
                "nws_stations", start_date, end_date, raise_exception=False
            ):
                available["current"].append("nws_stations")
        except Exception:
            pass

    # =========================================================================
    # RECOMENDAÇÃO (melhor fonte para região/período)
    # =========================================================================
    available["recommended"] = get_recommended_source(
        latitude, longitude, start_date, end_date, available
    )

    return available


def get_recommended_source(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    available_sources: Dict[str, List[str]],
) -> str:
    """
    Retorna fonte recomendada baseada em qualidade regional.

    Prioridade:
    1. Real-time regional (NWS Stations)
    2. Forecast regional de alta qualidade (MET Norway, NWS)
    3. Forecast global (Open-Meteo)
    4. Histórico de qualidade (NASA POWER, Open-Meteo Archive)

    Args:
        latitude: Latitude
        longitude: Longitude
        start_date: Data inicial
        end_date: Data final
        available_sources: Dict de fontes disponíveis

    Returns:
        Nome da fonte recomendada ou 'data_fusion'
    """
    region = get_region_name(latitude, longitude)

    # Prioridade 1: Real-time USA
    if "nws_stations" in available_sources["current"]:
        return "nws_stations"

    # Prioridade 2: Forecast regional alta qualidade
    if region == "nordic" and "met_norway" in available_sources["forecast"]:
        return "met_norway"

    if region == "usa" and "nws_forecast" in available_sources["forecast"]:
        return "nws_forecast"

    # Prioridade 3: Forecast global
    if "openmeteo_forecast" in available_sources["forecast"]:
        return "openmeteo_forecast"

    # Prioridade 4: Histórico
    if "nasa_power" in available_sources["historical"]:
        return "nasa_power"

    if "openmeteo_archive" in available_sources["historical"]:
        return "openmeteo_archive"

    # Fallback: data fusion se múltiplas fontes disponíveis
    total_sources = (
        len(available_sources["historical"])
        + len(available_sources["forecast"])
        + len(available_sources["current"])
    )

    if total_sources >= 2:
        return "data_fusion"

    return "nasa_power"  # Fallback global


def get_source_priority(
    latitude: float, longitude: float
) -> List[Tuple[str, int]]:
    """
    Retorna lista de fontes ordenadas por prioridade (score de qualidade).

    Score baseado em:
    - Qualidade regional (MET Norway para Nordic, NWS para USA)
    - Resolução temporal
    - Cobertura de variáveis
    - Confiabilidade histórica

    Args:
        latitude: Latitude
        longitude: Longitude

    Returns:
        Lista de tuplas (source_name, quality_score) ordenada

    Examples:
        >>> get_source_priority(59.9139, 10.7522)  # Oslo
        [('met_norway', 95), ('openmeteo_forecast', 85), ...]
    """
    region = get_region_name(latitude, longitude)
    priorities = []

    if region == "usa":
        priorities = [
            ("nws_stations", 95),  # Real-time USA
            ("nws_forecast", 90),  # Forecast USA oficial
            ("openmeteo_forecast", 85),  # Forecast global
            ("nasa_power", 80),  # Histórico global
            ("openmeteo_archive", 75),  # Histórico global
        ]
    elif region == "nordic":
        priorities = [
            ("met_norway", 95),  # Forecast Nordic alta qualidade
            ("openmeteo_forecast", 85),  # Forecast global
            ("nasa_power", 80),  # Histórico global
            ("openmeteo_archive", 75),  # Histórico global
        ]
    else:  # Global
        priorities = [
            ("openmeteo_forecast", 85),  # Forecast global
            ("nasa_power", 80),  # Histórico global
            ("openmeteo_archive", 75),  # Histórico global
        ]

    return priorities


# ==============================================================================
# METADADOS DE FONTES
# ==============================================================================

SOURCE_METADATA = {
    "nasa_power": {
        "name": "NASA POWER",
        "type": "historical",
        "coverage": "global",
        "quality": "high",
        "resolution": "daily",
        "variables": ["temp", "humidity", "wind", "radiation", "precip"],
    },
    "openmeteo_archive": {
        "name": "Open-Meteo Archive",
        "type": "historical",
        "coverage": "global",
        "quality": "high",
        "resolution": "hourly",
        "variables": [
            "temp",
            "humidity",
            "wind",
            "radiation",
            "precip",
            "eto",
        ],
    },
    "openmeteo_forecast": {
        "name": "Open-Meteo Forecast",
        "type": "forecast",
        "coverage": "global",
        "quality": "medium-high",
        "resolution": "hourly",
        "variables": [
            "temp",
            "humidity",
            "wind",
            "radiation",
            "precip",
            "eto",
        ],
    },
    "met_norway": {
        "name": "MET Norway",
        "type": "forecast",
        "coverage": "nordic",
        "quality": "very-high",
        "resolution": "hourly",
        "variables": ["temp", "humidity", "wind", "radiation", "precip"],
    },
    "nws_forecast": {
        "name": "NWS Forecast",
        "type": "forecast",
        "coverage": "usa",
        "quality": "high",
        "resolution": "hourly",
        "variables": ["temp", "dewpoint", "wind", "precip_prob"],
    },
    "nws_stations": {
        "name": "NWS Stations",
        "type": "current",
        "coverage": "usa",
        "quality": "very-high",
        "resolution": "real-time",
        "variables": ["temp", "dewpoint", "humidity", "wind", "pressure"],
    },
}


def get_source_metadata(source_api: str) -> Dict:
    """Retorna metadados de uma fonte."""
    return SOURCE_METADATA.get(source_api, {})
