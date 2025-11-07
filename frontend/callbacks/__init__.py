"""
CORRIGIDO
Callbacks - Lógica de interação do Dash.
"""

# from .eto_callbacks import register_eto_callbacks
# from .world_map_callbacks import register_map_callbacks
# from .navigation_callbacks import register_navigation_callbacks

from .cache_callbacks import register_cache_callbacks
from .favorites_callbacks import register_favorites_callbacks
from .location_sync_callbacks import register_location_sync_callbacks
from .navigation_callbacks import register_navigation_callbacks
from .selection_info_callbacks import register_selection_info_callbacks
from .world_map_callbacks import register_world_map_callbacks

__all__ = [
    "register_cache_callbacks",
    "register_location_sync_callbacks",
    "register_selection_info_callbacks",
    "register_favorites_callbacks",
    "register_world_map_callbacks",
    "register_navigation_callbacks",
]
