"""
Registro centralizado de todos callbacks.
"""

import logging

logger = logging.getLogger(__name__)


def register_all_callbacks(app):
    """Registra todos callbacks."""
    try:
        # Import and register home callbacks
        from .home_callbacks import register_home_callbacks

        register_home_callbacks(app)

        # Temporarily disabled other callbacks to isolate issue
        # register_world_map_callbacks(app)
        # register_eto_callbacks(app)
        # register_favorites_callbacks(app)
        # register_navigation_callbacks(app)
        # register_cache_callbacks(app)
        # register_selection_info_callbacks(app)
        # register_location_sync_callbacks(app)
        logger.info("✅ Todos callbacks registrados!")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise
