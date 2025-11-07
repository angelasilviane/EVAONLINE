"""
CORRIGIDO
Callbacks para sincronização de localização entre componentes Dash.
"""

import logging

from dash.dependencies import Input, Output

logger = logging.getLogger(__name__)


def register_location_sync_callbacks(app):

    @app.callback(
        Output("selected-location", "data"),
        Input("current-location", "data"),
        prevent_initial_call=True,
    )
    def sync_current_to_selected_location(current_location):
        """Sincroniza localização atual para o sistema de cache"""
        if not current_location or not current_location.get("lat"):
            return None

        logger.info(
            f"🔄 Sincronizando localização para cache: {current_location.get('location_info', 'Unknown')}"
        )

        return {
            "id": f"lat_{current_location['lat']:.6f}_lon_{current_location['lon']:.6f}",
            "lat": current_location["lat"],
            "lon": current_location["lon"],
            "timezone": current_location.get("timezone"),
            "location_info": current_location.get("location_info"),
            "lat_dms": current_location.get("lat_dms"),
            "lon_dms": current_location.get("lon_dms"),
        }
