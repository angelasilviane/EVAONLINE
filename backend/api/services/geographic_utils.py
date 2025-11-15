"""
Utilidades geográficas centralizadas para detecção de região.

Este módulo centraliza TODAS as operações de geolocalização,
eliminando duplicação de código em múltiplos módulos.

SINGLE SOURCE OF TRUTH para:
- Detecção de coordenadas USA
- Detecção de coordenadas Nordic (MET Norway 1km)
- Detecção de coordenadas Global

Bounding Boxes:
- USA Continental: -125°W a -66°W, 24°N a 49°N (NWS coverage)
- Nordic Region: 4°E a 31°E, 54°N a 71.5°N (MET Norway 1km)
- Global: Qualquer coordenada dentro (-180, -90) a (180, 90)

Uso:
    from backend.api.services.geographic_utils import GeographicUtils

    if GeographicUtils.is_in_usa(lat, lon):
        # Use NWS
        pass
    elif GeographicUtils.is_in_nordic(lat, lon):
        # Use MET Norway com precipitação de alta qualidade
        pass
    else:
        # Use Open-Meteo ou NASA POWER (global)
        pass
"""

from datetime import datetime, timezone
from loguru import logger
from typing import Literal
from functools import wraps


class GeographicUtils:
    """Centraliza detecção geográfica com bounding boxes padronizadas."""

    # Bounding boxes: (lon_min, lat_min, lon_max, lat_max) = (W, S, E, N)

    USA_BBOX = (-125.0, 24.0, -66.0, 49.0)
    """
    Bounding box USA Continental (NWS coverage).

    Cobertura:
        Longitude: -125°W (Costa Oeste) a -66°W (Costa Leste)
        Latitude: 24°N (Sul da Flórida) a 49°N (Fronteira Canadá)

    Estados incluídos:
        Todos os 48 estados contíguos

    Excluídos:
        Alasca, Havaí, Porto Rico, territórios
    """

    NORDIC_BBOX = (4.0, 54.0, 31.0, 71.5)
    """
    Bounding box Região Nórdica (MET Norway 1km alta qualidade).

    Cobertura:
        Longitude: 4°E (Dinamarca Oeste) a 31°E (Finlândia/Bálticos)
        Latitude: 54°N (Dinamarca Sul) a 71.5°N (Noruega Norte)

    Países incluídos:
        Noruega, Dinamarca, Suécia, Finlândia, Estônia, Letônia, Lituânia

    Qualidade especial:
        - Resolução: 1 km (vs 9km global)
        - Atualizações: A cada hora (vs 4x/dia global)
        - Precipitação: Radar + crowdsourced (Netatmo)
        - Pós-processamento: Extensivo com bias correction
    """

    GLOBAL_BBOX = (-180.0, -90.0, 180.0, 90.0)
    """Bounding box Global (qualquer coordenada válida)."""

    @staticmethod
    def is_in_usa(lat: float, lon: float) -> bool:
        """
        Verifica se coordenadas estão nos EUA continental.

        Usa bounding box: (-125.0, 24.0, -66.0, 49.0)
        Cobertura: NWS API (National Weather Service)

        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)

        Returns:
            bool: True se dentro do bbox USA, False caso contrário

        Exemplo:
            if GeographicUtils.is_in_usa(39.7392, -104.9903):
                # Denver, CO - dentro dos USA
                pass
        """
        lon_min, lat_min, lon_max, lat_max = GeographicUtils.USA_BBOX
        in_usa = (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)

        if not in_usa:
            logger.debug(
                f"⚠️  Coordenadas ({lat:.4f}, {lon:.4f}) "
                f"FORA da cobertura USA Continental"
            )

        return in_usa

    @staticmethod
    def is_in_nordic(lat: float, lon: float) -> bool:
        """
        Verifica se coordenadas estão na região Nórdica.

        Usa bounding box: (4.0, 54.0, 31.0, 71.5)
        Cobertura: MET Norway 1km alta qualidade com radar

        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)

        Returns:
            bool: True se dentro do bbox Nordic, False caso contrário

        Exemplo:
            if GeographicUtils.is_in_nordic(60.1699, 24.9384):
                # Helsinki, Finland - dentro da região Nordic
                pass
        """
        lon_min, lat_min, lon_max, lat_max = GeographicUtils.NORDIC_BBOX
        in_nordic = (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)

        if in_nordic:
            logger.debug(
                f"✅ Coordenadas ({lat:.4f}, {lon:.4f}) "
                f"na região NORDIC (MET Norway 1km)"
            )

        return in_nordic

    @staticmethod
    def is_valid_coordinate(lat: float, lon: float) -> bool:
        """
        Verifica se coordenadas são válidas (dentro de (-180, -90) a (180, 90)).

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            bool: True se válido, False caso contrário
        """
        lon_min, lat_min, lon_max, lat_max = GeographicUtils.GLOBAL_BBOX
        return (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)

    @staticmethod
    def is_in_bbox(lat: float, lon: float, bbox: tuple) -> bool:
        """
        Verifica se coordenadas estão dentro de um bounding box.

        Args:
            lat: Latitude
            lon: Longitude
            bbox: Tupla (west, south, east, north)

        Returns:
            bool: True se dentro do bbox

        Exemplo:
            # Verificar se está na região USA
            if GeographicUtils.is_in_bbox(40.7, -74.0,
                                          GeographicUtils.USA_BBOX):
                # Dentro da região USA
                pass
        """
        if not GeographicUtils.is_valid_coordinate(lat, lon):
            return False

        west, south, east, north = bbox
        return (west <= lon <= east) and (south <= lat <= north)

    @staticmethod
    def get_region(
        lat: float, lon: float
    ) -> Literal["usa", "nordic", "global"]:
        """
        Detecta região geográfica com prioridade: USA > Nordic > Global.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            str: Uma de "usa", "nordic", "global"

        Exemplo:
            region = GeographicUtils.get_region(39.7392, -104.9903)
            # Retorna: "usa"

            region = GeographicUtils.get_region(60.1699, 24.9384)
            # Retorna: "nordic"

            region = GeographicUtils.get_region(-23.5505, -46.6333)
            # Retorna: "global"
        """
        if GeographicUtils.is_in_usa(lat, lon):
            return "usa"
        elif GeographicUtils.is_in_nordic(lat, lon):
            return "nordic"
        else:
            return "global"

    @staticmethod
    def get_recommended_sources(lat: float, lon: float) -> list[str]:
        """
        Retorna lista de fontes climáticas recomendadas por região,
        em ordem de prioridade.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            list[str]: Lista ordenada de nomes de fontes (API priority)

        Regiões:
            USA:
                1. nws_forecast (previsão alta qualidade)
                2. nws_stations (observações tempo real)
                3. openmeteo_forecast (fallback global)
                4. nasa_power (fallback histórico)

            Nordic:
                1. met_norway (previsão 1km com radar)
                2. openmeteo_forecast (fallback global)
                3. nasa_power (histórico)

            Global:
                1. openmeteo_forecast (recentrecent+previsão global)
                2. met_norway (previsão global, sem precipitação)
                3. nasa_power (histórico)

        Exemplo:
            sources = GeographicUtils.get_recommended_sources(
                39.7392, -104.9903
            )
            # Retorna: ["nws_forecast", "nws_stations", "openmeteo_forecast",
            #           "nasa_power"]
        """
        region = GeographicUtils.get_region(lat, lon)

        if region == "usa":
            return [
                "nws_forecast",  # Melhor para previsão
                "nws_stations",  # Observações tempo real
                "openmeteo_forecast",  # Fallback
                "openmeteo_archive",  # Histórico
                "nasa_power",  # Fallback universal
            ]
        elif region == "nordic":
            return [
                "met_norway",  # Melhor: 1km + radar
                "openmeteo_forecast",  # Fallback
                "openmeteo_archive",  # Histórico
                "nasa_power",  # Fallback universal
            ]
        else:  # global
            return [
                "openmeteo_forecast",  # Melhor global
                "met_norway",  # Previsão global (sem precip)
                "openmeteo_archive",  # Histórico
                "nasa_power",  # Fallback universal
            ]


class TimezoneUtils:
    """
    Utilitários para manipulação consistente de timezone.

    Garante comparações corretas entre datetimes com/sem timezone.
    Centralizado aqui para evitar importação circular com weather_utils.
    """

    @staticmethod
    def ensure_naive(dt) -> "datetime":
        """
        Converte datetime para naive (sem timezone).

        Args:
            dt: Datetime possivelmente timezone-aware

        Returns:
            Datetime naive (sem timezone)
        """
        from datetime import datetime

        if isinstance(dt, datetime) and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt

    @staticmethod
    def ensure_utc(dt) -> "datetime":
        """
        Converte datetime para UTC timezone-aware.

        Args:
            dt: Datetime possivelmente naive

        Returns:
            Datetime UTC timezone-aware
        """
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return dt

    @staticmethod
    def compare_dates_safe(dt1, dt2, comparison: str = "lt") -> bool:
        """
        Compara duas datas de forma segura (ignorando timezone).

        Args:
            dt1: Primeira data
            dt2: Segunda data
            comparison: 'lt', 'le', 'gt', 'ge', 'eq'

        Returns:
            Resultado da comparação
        """
        from datetime import datetime

        date1 = dt1.date() if isinstance(dt1, datetime) else dt1
        date2 = dt2.date() if isinstance(dt2, datetime) else dt2

        if comparison == "lt":
            return date1 < date2
        elif comparison == "le":
            return date1 <= date2
        elif comparison == "gt":
            return date1 > date2
        elif comparison == "ge":
            return date1 >= date2
        elif comparison == "eq":
            return date1 == date2
        else:
            raise ValueError(f"Invalid comparison: {comparison}")


def validate_coordinates(func):
    """
    Decorador para validar coordenadas antes de executar função.

    Valida que lat/lon são floats válidos dentro de (-180, -90) a (180, 90).
    Levanta ValueError se inválidas.

    Uso:
        @validate_coordinates
        def get_weather(lat: float, lon: float):
            # lat/lon já validadas aqui
            pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extrair lat/lon dos argumentos
        if len(args) >= 3:  # self, lat, lon
            lat, lon = args[1], args[2]
        elif "lat" in kwargs and "lon" in kwargs:
            lat, lon = kwargs["lat"], kwargs["lon"]
        else:
            raise ValueError("Function must have 'lat' and 'lon' parameters")

        # Validar coordenadas
        if not GeographicUtils.is_valid_coordinate(lat, lon):
            raise ValueError(
                f"Invalid coordinates: lat={lat}, lon={lon}. "
                "Must be within (-180, -90) to (180, 90)"
            )

        return func(*args, **kwargs)

    return wrapper
