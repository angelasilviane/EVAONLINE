"""
Callbacks para o mapa mundial interativo.

Features:
- Localização automática do usuário
- Cliques no mapa para selecionar coordenadas
- Cálculo automático de fuso horário
- Marcadores dinâmicos para localizações
- Integração com sistema de favoritos
"""

import logging

import dash_leaflet as dl
from ..components.world_map_interactive import (
    create_favorite_markers,
    create_location_marker,
    create_user_location_marker,
)
from dash import callback_context, html
from dash.dependencies import Input, Output, State

from ..utils.coordinate_utils import are_coordinates_similar
from ..utils.timezone_utils import (
    format_coordinates,
    get_location_info,
    get_timezone,
)
from ..utils.user_geolocation import is_valid_coordinate_range

logger = logging.getLogger(__name__)


def register_world_map_callbacks(app):
    """
    Registra todos os callbacks relacionados ao mapa mundial
    """

    # 1. Callback para atualizar localização baseada em cliques ou geolocalização
    @app.callback(
        [
            Output("current-location", "data"),
            Output("favorite-button", "disabled"),
            Output("map-layer", "children"),
            Output("map-popup", "children"),
        ],
        [
            Input("world-map", "click_lat_lng"),
            Input("locate-control", "locate_lat_lng"),
        ],
        [State("current-location", "data"), State("favorites-store", "data")],
    )
    def update_location(
        click_lat_lng, locate_lat_lng, current_data, favorites
    ):
        """
        Atualiza a localização atual baseada em cliques no mapa
        ou geolocalização
        """
        ctx = callback_context
        if not ctx.triggered:
            return current_data, True, [], None
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        markers = []
        # Determinar coordenadas baseado no trigger
        if trigger_id == "world-map" and click_lat_lng:
            lat, lon = click_lat_lng
            marker_type = "click"
            logger.info(f"🗺️ Usuário clicou no mapa: {lat:.4f}, {lon:.4f}")
        elif trigger_id == "locate-control" and locate_lat_lng:
            lat, lon = locate_lat_lng
            marker_type = "user"
            logger.info(f"📍 Geolocalização detectada: {lat:.4f}, {lon:.4f}")
        else:
            return current_data, True, [], None
        # ✅ VALIDAR COORDENADAS (MOVIDO PARA O LUGAR CORRETO)
        if not is_valid_coordinate_range(lat, lon):
            logger.error("❌ Coordenadas inválidas recebidas")
            return current_data, True, [], None
        if current_data and current_data.get("lat"):
            similar = are_coordinates_similar(
                current_data["lat"],
                current_data["lon"],
                lat,
                lon,
                threshold_km=0.1,
            )
            if similar:
                logger.info("📍 Coordenada similar à atual - ignorando")
                # ❌ CORREÇÃO: 'markers' e 'popup' não existem aqui ainda
                # ✅ CORREÇÃO: Retornar os dados atuais
                return current_data, False, [], None
        # ✅ CALCULAR FUSO HORÁRIO AUTOMÁTICO e informações
        timezone = get_timezone(lat, lon)
        location_info = get_location_info(lat, lon)
        lat_dms, lon_dms = format_coordinates(lat, lon)
        # Atualizar dados da localização atual
        new_data = {
            "lat": lat,
            "lon": lon,
            "timezone": timezone,
            "lat_dms": lat_dms,
            "lon_dms": lon_dms,
            "location_info": location_info,
        }
        # Criar marcador apropriado
        if marker_type == "user":
            marker = create_user_location_marker(lat, lon)
            logger.info(f"👤 Marcador de usuário criado para: {location_info}")
        else:
            marker = create_location_marker(lat, lon, timezone, location_info)
            logger.info(f"📌 Marcador de clique criado para: {location_info}")
        markers.append(marker)
        # Adicionar marcadores de favoritos se existirem
        if favorites:
            favorite_markers = create_favorite_markers(favorites)
            markers.extend(favorite_markers)
            logger.debug(
                f"⭐ {len(favorite_markers)} marcadores de favoritos "
                f"adicionados"
            )
        # Criar popup para a localização selecionada
        popup = dl.Popup(
            html.Div(
                [
                    html.H5(
                        "📍 Informações do Local",
                        style={"marginBottom": "10px", "color": "#2d5016"},
                    ),
                    html.P(
                        [
                            html.Strong("Coordenadas: "),
                            f"{lat_dms}, {lon_dms}",
                        ],
                        style={"marginBottom": "5px"},
                    ),
                    html.P(
                        [html.Strong("Decimal: "), f"{lat:.6f}, {lon:.6f}"],
                        style={
                            "marginBottom": "5px",
                            "fontSize": "12px",
                            "color": "#666",
                        },
                    ),
                    html.P(
                        [html.Strong("Fuso Horário: "), timezone],
                        style={"marginBottom": "5px"},
                    ),
                    html.P(
                        [html.Strong("Localização: "), location_info],
                        style={"marginBottom": "10px", "fontSize": "12px"},
                    ),
                    html.Hr(
                        style={"margin": "10px 0", "borderColor": "#e9ecef"}
                    ),
                    html.Small(
                        "Use os botões acima do mapa para salvar ou calcular ETo",
                        style={"color": "#666", "fontStyle": "italic"},
                    ),
                ],
                style={"minWidth": "250px"},
            ),
            lat=lat,
            lon=lon,
        )
        logger.info(f"✅ Localização atualizada: {location_info}")
        return new_data, False, markers, popup

    # 2. Callback para atualizar marcadores quando favoritos mudam
    @app.callback(
        Output("map-layer", "children", allow_duplicate=True),
        [Input("favorites-store", "data")],
        [State("current-location", "data")],
        prevent_initial_call=True,
    )
    def update_favorite_markers(favorites, current_location):
        """
        Atualiza marcadores quando a lista de favoritos muda
        """
        markers = []
        # Adicionar marcador da localização atual se existir
        if current_location and current_location.get("lat"):
            marker = create_location_marker(
                current_location["lat"],
                current_location["lon"],
                current_location.get("timezone"),
                current_location.get("location_info"),
            )
            markers.append(marker)
            logger.debug("📍 Marcador de localização atual mantido")
        # Adicionar marcadores de favoritos
        if favorites:
            favorite_markers = create_favorite_markers(favorites)
            markers.extend(favorite_markers)
            logger.info(
                f"🔄 {len(favorite_markers)} marcadores de favoritos "
                f"atualizados"
            )
        return markers

    # 3. Callback para configurar opções do controle de localização
    @app.callback(
        Output("locate-control", "options"),
        [Input("world-map", "id")],  # Quando o mapa é inicializado
    )
    def configure_locate_control(map_id):
        """
        Configura opções do controle de localização
        """
        return {
            "locateOptions": {
                "enableHighAccuracy": True,
                "maxZoom": 16,
                "timeout": 10000,
                "watch": True,
            },
            "flyTo": True,
            "keepCurrentZoomLevel": False,
            "drawCircle": True,
            "showPopup": False,
            "returnToPrevBounds": True,
        }

    # 4. Callback para ajustar viewport do mapa quando localização muda
    @app.callback(
        Output("world-map", "viewport"),
        [Input("current-location", "data")],
        prevent_initial_call=True,
    )
    def adjust_map_viewport(current_location):
        """
        Ajusta a viewport do mapa quando uma nova localização é selecionada
        """
        if current_location and current_location.get("lat"):
            return {
                "center": [current_location["lat"], current_location["lon"]],
                "zoom": 12,
                "transition": "flyTo",
                "transitionDuration": 1000,
            }
        return None

    # 5.Callback para debug de interações (remover em produção)
    @app.callback(
        Output("map-loading-output", "children"),
        [
            Input("world-map", "click_lat_lng"),
            Input("locate-control", "locate_lat_lng"),
        ],
        prevent_initial_call=True,
    )
    def debug_map_interactions(click_lat_lng, locate_lat_lng):
        """
        Callback para debug de interações no mapa.
        """
        ctx = callback_context
        if not ctx.triggered:
            return ""
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "world-map" and click_lat_lng:
            lat, lon = click_lat_lng
            logger.debug(f"🗺️ Click no mapa: {lat:.4f}, {lon:.4f}")
            return f"Debug: Click em {lat:.4f}, {lon:.4f}"
        elif trigger_id == "locate-control" and locate_lat_lng:
            lat, lon = locate_lat_lng
            logger.debug(f"📍 Geolocalização: {lat:.4f}, {lon:.4f}")
            return f"Debug: Geolocalização em {lat:.4f}, {lon:.4f}"
        return ""

    # Final do registro de callbacks
    logger.info("✅ Callbacks do mapa mundial registrados com sucesso")
