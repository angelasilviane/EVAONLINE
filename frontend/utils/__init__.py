"""
Utils package for ETO Calculator application.
"""

from .coordinate_utils import (
    are_coordinates_similar,
    calculate_distance,
    decimal_to_dms,
    parse_coordinate_string,
)
from .timezone_utils import format_coordinates, get_location_info, get_timezone
from .user_geolocation import (
    calculate_geolocation_accuracy,
    get_fallback_location,
    is_valid_coordinate_range,
    validate_geolocation_permission,
)

__all__ = [
    # timezone_utils
    "get_timezone",
    "get_location_info",
    "format_coordinates",
    # user_geolocation
    "validate_geolocation_permission",
    "calculate_geolocation_accuracy",
    "get_fallback_location",
    "is_valid_coordinate_range",
    # coordinate_utils
    "decimal_to_dms",
    "calculate_distance",
    "are_coordinates_similar",
    "parse_coordinate_string",
]
