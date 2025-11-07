"""
Limites de datas e validações para cada fonte de dados climáticos.

Define ranges de datas válidos para cada API e funções de validação.
Padroniza o início de dados históricos em 01/01/1990 para garantir
disponibilidade em NASA POWER e Open-Meteo Archive.
"""

from datetime import date, timedelta
from typing import Dict, Tuple

# ==============================================================================
# CONSTANTES GLOBAIS
# ==============================================================================

# Data padrão de início para dados históricos (padronização)
HISTORICAL_START_DATE = date(1990, 1, 1)

# Limite de dias para processamento síncrono (tempo real)
REALTIME_MIN_DAYS = 7
REALTIME_MAX_DAYS = 30

# Limite de dias para processamento assíncrono (histórico)
HISTORICAL_MAX_DAYS = 90  # 3 meses

# Threshold para classificação automática de tipo de requisição
REQUEST_TYPE_THRESHOLD_DAYS = 30  # > 30 dias do passado = histórico


# ==============================================================================
# LIMITES DE DATAS POR API
# ==============================================================================

API_DATE_LIMITS: Dict[str, Dict] = {
    # NASA POWER: Dados históricos globais
    "nasa_power": {
        "start": date(1981, 1, 1),  # Início real da API
        "end_offset_days": -2,  # hoje - 2 dias
        "type": "historical",
        "description": "NASA POWER - Dados históricos globais",
        "coverage": "global",
        "min_padrao": HISTORICAL_START_DATE,  # Nosso padrão: 1990
    },
    # Open-Meteo Archive: Dados históricos desde 1940
    "openmeteo_archive": {
        "start": date(1940, 1, 1),  # Início real da API
        "end_offset_days": -5,  # hoje - 5 dias
        "type": "historical",
        "description": "Open-Meteo Archive - Dados históricos globais",
        "coverage": "global",
        "min_padrao": HISTORICAL_START_DATE,  # Nosso padrão: 1990
    },
    # Open-Meteo Forecast: Híbrido (passado recente + forecast)
    "openmeteo_forecast": {
        "start_offset_days": -30,  # hoje - 30 dias
        "end_offset_days": 16,  # hoje + 16 dias
        "type": "hybrid",
        "description": "Open-Meteo Forecast - Híbrido global",
        "coverage": "global",
    },
    # MET Norway: Forecast para região nórdica
    "met_norway": {
        "start_offset_days": 0,  # hoje
        "end_offset_days": 5,  # hoje + 5 dias
        "type": "forecast",
        "description": "MET Norway - Forecast nórdico alta qualidade",
        "coverage": "nordic",  # Noruega, Suécia, Finlândia, Dinamarca
    },
    # NWS Forecast: Previsão para USA
    "nws_forecast": {
        "start_offset_days": 0,  # hoje
        "end_offset_days": 7,  # hoje + 7 dias
        "type": "forecast",
        "description": "NWS Forecast - Previsão USA",
        "coverage": "usa",
    },
    # NWS Stations: Observações em tempo real USA
    "nws_stations": {
        "start_offset_days": -1,  # hoje - 1 dia
        "end_offset_days": 0,  # hoje
        "type": "current",
        "description": "NWS Stations - Real-time USA",
        "coverage": "usa",
    },
}


# ==============================================================================
# FUNÇÕES DE VALIDAÇÃO
# ==============================================================================


def get_api_date_range(source_api: str) -> Tuple[date, date]:
    """
    Retorna range de datas válido para a API.

    Args:
        source_api: Nome da API ('nasa_power', 'openmeteo_archive', etc.)

    Returns:
        Tupla (data_início, data_fim) válidas para a API

    Raises:
        ValueError: Se a API não for reconhecida

    Examples:
        >>> get_api_date_range('nasa_power')
        (datetime.date(1990, 1, 1), datetime.date(2025, 11, 4))

        >>> get_api_date_range('openmeteo_forecast')
        (datetime.date(2025, 10, 7), datetime.date(2025, 11, 22))
    """
    if source_api not in API_DATE_LIMITS:
        raise ValueError(
            f"API '{source_api}' não reconhecida. "
            f"APIs disponíveis: {list(API_DATE_LIMITS.keys())}"
        )

    limits = API_DATE_LIMITS[source_api]
    today = date.today()

    # Determina data de início
    if "start" in limits:
        # Para históricos: usa min_padrao (1990) se existir
        start_date = limits.get("min_padrao", limits["start"])
    else:
        # Para forecast/current: calcula a partir de hoje
        start_date = today + timedelta(days=limits["start_offset_days"])

    # Determina data de fim
    end_date = today + timedelta(days=limits["end_offset_days"])

    return start_date, end_date


def validate_dates_for_source(
    source_api: str,
    start_date: date,
    end_date: date,
    raise_exception: bool = True,
) -> bool:
    """
    Valida se datas são compatíveis com a API.

    Args:
        source_api: Nome da API
        start_date: Data inicial solicitada
        end_date: Data final solicitada
        raise_exception: Se True, lança exceção; se False, retorna bool

    Returns:
        True se datas são válidas, False caso contrário

    Raises:
        ValueError: Se datas forem inválidas (apenas se raise_exception=True)

    Examples:
        >>> validate_dates_for_source(
        ...     'nasa_power',
        ...     date(2020, 1, 1),
        ...     date(2020, 12, 31)
        ... )
        True

        >>> validate_dates_for_source(
        ...     'nasa_power',
        ...     date(1970, 1, 1),  # Antes de 1990
        ...     date(2020, 12, 31)
        ... )
        ValueError: Data inicial deve ser >= 01/01/1990
    """
    api_start, api_end = get_api_date_range(source_api)
    limits = API_DATE_LIMITS[source_api]

    # Valida data inicial
    if start_date < api_start:
        msg = (
            f"{source_api}: Data inicial deve ser >= "
            f"{api_start.strftime('%d/%m/%Y')}. "
            f"(Padronizamos início histórico em 1990 para garantir "
            f"dados de NASA POWER e Open-Meteo Archive)"
        )
        if raise_exception:
            raise ValueError(msg)
        return False

    # Valida data final
    if end_date > api_end:
        offset = limits.get("end_offset_days", 0)
        msg = (
            f"{source_api}: Data final deve ser <= "
            f"{api_end.strftime('%d/%m/%Y')}. "
            f"(Dados disponíveis até hoje{offset:+d} dias)"
        )
        if raise_exception:
            raise ValueError(msg)
        return False

    # Valida ordem das datas
    if start_date > end_date:
        msg = "Data inicial deve ser anterior à data final"
        if raise_exception:
            raise ValueError(msg)
        return False

    return True


def validate_period_duration(
    start_date: date, end_date: date, is_historical: bool = False
) -> None:
    """
    Valida duração do período conforme tipo de requisição.

    Args:
        start_date: Data inicial
        end_date: Data final
        is_historical: Se True, valida como histórico; se False, como real-time

    Raises:
        ValueError: Se duração for inválida

    Examples:
        # Real-time: mínimo 7 dias, máximo 30 dias
        >>> validate_period_duration(
        ...     date.today() - timedelta(days=7),
        ...     date.today(),
        ...     is_historical=False
        ... )
        # OK

        # Histórico: máximo 90 dias
        >>> validate_period_duration(
        ...     date(2020, 1, 1),
        ...     date(2020, 6, 1),
        ...     is_historical=True
        ... )
        ValueError: Limite de 90 dias para downloads históricos
    """
    days = (end_date - start_date).days + 1

    if is_historical:
        # Validação para processamento assíncrono
        if days > HISTORICAL_MAX_DAYS:
            raise ValueError(
                f"Limite de {HISTORICAL_MAX_DAYS} dias (3 meses) para "
                f"downloads históricos. Período solicitado: {days} dias. "
                f"Para períodos maiores, faça múltiplas requisições."
            )
    else:
        # Validação para dashboard em tempo real
        if days < REALTIME_MIN_DAYS:
            raise ValueError(
                f"Período mínimo: {REALTIME_MIN_DAYS} dias para "
                f"análise estatística adequada. "
                f"Período solicitado: {days} dias."
            )

        if days > REALTIME_MAX_DAYS:
            raise ValueError(
                f"Período máximo para tempo real: {REALTIME_MAX_DAYS} dias. "
                f"Período solicitado: {days} dias. "
                f"Para períodos maiores, use download histórico assíncrono."
            )


def classify_request_type(start_date: date, end_date: date) -> str:
    """
    Classifica automaticamente o tipo de requisição.

    Args:
        start_date: Data inicial
        end_date: Data final

    Returns:
        'historical' ou 'current'

    Logic:
        - Se data_inicial > hoje - 30 dias: 'current' (tempo real)
        - Caso contrário: 'historical' (processamento assíncrono)

    Examples:
        >>> classify_request_type(date(2020, 1, 1), date(2020, 12, 31))
        'historical'

        >>> classify_request_type(
        ...     date.today() - timedelta(days=7),
        ...     date.today()
        ... )
        'current'
    """
    days_from_today = (date.today() - start_date).days

    if days_from_today > REQUEST_TYPE_THRESHOLD_DAYS:
        return "historical"
    else:
        return "current"


def get_available_sources_for_period(
    start_date: date, end_date: date
) -> Dict[str, list]:
    """
    Retorna fontes disponíveis para o período solicitado.

    Args:
        start_date: Data inicial
        end_date: Data final

    Returns:
        Dict com 'historical', 'forecast' e 'current'

    Examples:
        >>> get_available_sources_for_period(
        ...     date(2020, 1, 1),
        ...     date(2020, 12, 31)
        ... )
        {
            'historical': ['nasa_power', 'openmeteo_archive'],
            'forecast': [],
            'current': []
        }
    """
    available = {"historical": [], "forecast": [], "current": []}

    for api_name, limits in API_DATE_LIMITS.items():
        try:
            if validate_dates_for_source(
                api_name, start_date, end_date, raise_exception=False
            ):
                api_type = limits["type"]
                available[api_type].append(api_name)
        except Exception:
            continue

    return available


def get_api_info(source_api: str) -> Dict:
    """
    Retorna informações sobre uma API.

    Args:
        source_api: Nome da API

    Returns:
        Dicionário com informações da API

    Examples:
        >>> get_api_info('nasa_power')
        {
            'name': 'nasa_power',
            'description': 'NASA POWER - Dados históricos globais',
            'type': 'historical',
            'coverage': 'global',
            'start_date': datetime.date(1990, 1, 1),
            'end_date': datetime.date(2025, 11, 4)
        }
    """
    if source_api not in API_DATE_LIMITS:
        raise ValueError(f"API '{source_api}' não reconhecida")

    limits = API_DATE_LIMITS[source_api]
    start_date, end_date = get_api_date_range(source_api)

    return {
        "name": source_api,
        "description": limits["description"],
        "type": limits["type"],
        "coverage": limits["coverage"],
        "start_date": start_date,
        "end_date": end_date,
    }
