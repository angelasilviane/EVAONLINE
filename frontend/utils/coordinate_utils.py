"""
Utilitários para manipulação e conversão de coordenadas.

Features:
- Conversão entre formatos de coordenadas
- Cálculo de distâncias
- Validação de coordenadas
"""

import logging
import math
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def decimal_to_dms(decimal_degrees: float, is_latitude: bool) -> Tuple[int, int, float, str]:
    """
    Converte graus decimais para graus, minutos, segundos.
    Args:
        decimal_degrees: Graus em formato decimal
        is_latitude: True se é latitude, False se é longitude
    Returns:
        tuple: (graus, minutos, segundos, direção)
    """
    try:
        # Determina a direção
        if is_latitude:
            direction = "N" if decimal_degrees >= 0 else "S"
        else:
            direction = "E" if decimal_degrees >= 0 else "W"
        # Converte para valor absoluto
        abs_degrees = abs(decimal_degrees)
        # Calcula graus, minutos e segundos
        degrees = int(abs_degrees)
        minutes_decimal = (abs_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        logger.debug(
            f"🧭 Convertido {decimal_degrees}° para "
            f"{degrees}°{minutes}′{seconds:.2f}″ {direction}"
        )
        return degrees, minutes, seconds, direction
    except Exception as e:
        logger.error(f"❌ Erro na conversão DMS: {e}")
        return 0, 0, 0.0, "N" if is_latitude else "E"


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância em km entre duas coordenadas usando fórmula
    de Haversine.
    Args:
        lat1, lon1: Primeira coordenada
        lat2, lon2: Segunda coordenada
    Returns:
        float: Distância em quilômetros
    """
    try:
        # Raio da Terra em km
        R = 6371.0
        # Converte para radianos
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        # Diferenças
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        # Fórmula de Haversine
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        logger.debug(
            f"📏 Distância calculada: {distance:.2f} km entre "
            f"({lat1:.4f}, {lon1:.4f}) e ({lat2:.4f}, {lon2:.4f})"
        )
        return distance
    except Exception as e:
        logger.error(f"❌ Erro no cálculo de distância: {e}")
        return 0.0


def are_coordinates_similar(
    lat1: float, lon1: float, lat2: float, lon2: float, threshold_km: float = 1.0
) -> bool:
    """
    Verifica se duas coordenadas são similares (dentro de um threshold).
    Args:
        lat1, lon1: Primeira coordenada
        lat2, lon2: Segunda coordenada
        threshold_km: Threshold em km para considerar similar
    Returns:
        bool: True se as coordenadas são similares
    """
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    similar = distance <= threshold_km
    if similar:
        logger.debug(f"📍 Coordenadas similares: {distance:.3f} km <= {threshold_km} km")
    else:
        logger.debug(f"📍 Coordenadas diferentes: {distance:.3f} km > {threshold_km} km")
    return similar


def parse_coordinate_string(coord_str: str) -> Optional[Tuple[float, float]]:
    """
    Tenta parsear uma string de coordenada em vários formatos.
    Args:
        coord_str: String da coordenada (ex: "-23.5505, -46.6333")
    Returns:
        tuple: (lat, lon) ou None se inválido
    """
    try:
        # Remove espaços e divide por vírgula
        cleaned = coord_str.strip().replace(" ", "")
        parts = cleaned.split(",")
        if len(parts) != 2:
            return None
        lat = float(parts[0])
        lon = float(parts[1])
        # Valida os ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None
        logger.debug(f"✅ Coordenada parseada: ({lat}, {lon})")
        return lat, lon
    except (ValueError, AttributeError) as e:
        logger.warning(f"⚠️ Não foi possível parsear coordenada: {coord_str} - {e}")
        return None


logger.info("✅ Utilitários de coordenadas carregados com sucesso")
