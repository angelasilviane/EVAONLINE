import logging

from geopy.geocoders import Nominatim
from timezonefinderL import TimezoneFinder

# Initialize services
tf = TimezoneFinder()
geolocator = Nominatim(user_agent="eto_calculator")

# Configurar logger específico para este módulo
logger = logging.getLogger(__name__)


def get_timezone(lat, lon):
    """Get timezone for given coordinates usando TimezoneFinder"""
    try:
        # Cálculo do fuso horário
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        logger.debug(f"🌍 Fuso horário detectado: {timezone_str} " f"para ({lat:.4f}, {lon:.4f})")
        return timezone_str if timezone_str else "UTC"
    except Exception as e:
        logger.error(f"❌ Erro ao obter fuso horário para ({lat:.4f}, {lon:.4f}): {e}")
        return "UTC"


def get_location_info(lat, lon):
    """Get location information using geopy"""
    try:
        location = geolocator.reverse((lat, lon), language="pt")
        address = location.address if location else "Localização não encontrada"
        return address
    except Exception as e:
        logger.error(
            f"❌ Erro ao obter informações de localização para " f"({lat:.4f}, {lon:.4f}): {e}"
        )
        return "Localização não disponível"


def format_coordinates(lat, lon):
    """Format coordinates to degrees, minutes, seconds"""

    def to_dms(coord, is_lat):
        if is_lat:
            direction = "N" if coord >= 0 else "S"
        else:
            direction = "E" if coord >= 0 else "O"
        coord = abs(coord)
        degrees = int(coord)
        minutes = int((coord - degrees) * 60)
        seconds = (coord - degrees - minutes / 60) * 3600
        return f"{degrees}°{minutes}′{seconds:.0f}″ {direction}"

    lat_dms = to_dms(lat, True)
    lon_dms = to_dms(lon, False)
    logger.debug(f"🧭 Coordenadas formatadas: {lat_dms}, {lon_dms}")
    return lat_dms, lon_dms


# Log de inicialização bem-sucedida
logger.info("✅ Utilitários de timezone carregados com sucesso")
