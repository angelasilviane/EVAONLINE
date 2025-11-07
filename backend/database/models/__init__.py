"""
Exporta todos os modelos de banco de dados.
"""

from .admin_user import AdminUser
from .api_variables import APIVariables
from .climate_data import ClimateData
from .user_cache import CacheMetadata, UserSessionCache
from .user_favorites import FavoriteLocation, UserFavorites
from .visitor_stats import VisitorStats

__all__ = [
    "AdminUser",
    "APIVariables",
    "ClimateData",
    "UserSessionCache",
    "CacheMetadata",
    "UserFavorites",
    "FavoriteLocation",
    "VisitorStats",
]
