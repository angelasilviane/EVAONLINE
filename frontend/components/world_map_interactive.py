"""
Componente do mapa mundial interativo para o ETO Calculator.

Features:
- Mapa Leaflet com OpenStreetMap
- Controles de localização do usuário
- Controle de escala
- Suporte a marcadores dinâmicos
- Integração com sistema de favoritos
"""

import logging

import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import html

logger = logging.getLogger(__name__)


def create_world_map():
    """
    Cria o mapa mundial interativo com todos os controles.
    Returns:
        html.Div: Container do mapa com controles
    """
    logger.debug("🗺️ Criando mapa mundial interativo")
    try:
        map_component = html.Div(
            [
                dl.Map(
                    [
                        # Camada base do mapa (OpenStreetMap)
                        dl.TileLayer(
                            url=("https://{s}.tile.openstreetmap.org/" "{z}/{x}/{y}.png"),
                            attribution=(
                                '&copy; <a href="https://www.openstreetmap.org/'
                                'copyright">OpenStreetMap</a> contributors'
                            ),
                            maxZoom=19,
                            minZoom=2,
                        ),
                        # Controle de localização do usuário
                        dl.LocateControl(
                            locateOptions={
                                "enableHighAccuracy": True,
                                "maxZoom": 16,
                                "timeout": 10000,
                                "watch": True,
                            },
                            flyTo=True,
                            keepCurrentZoomLevel=False,
                            drawCircle=True,
                            showPopup=False,
                            returnToPrevBounds=True,
                            id="locate-control",
                        ),
                        # Controle de escala
                        dl.ScaleControl(
                            position="bottomleft", imperial=False, metric=True, maxWidth=200
                        ),
                        # Controles de zoom
                        dl.ZoomControl(position="topright"),
                        # Camada para marcadores dinâmicos
                        dl.LayerGroup(id="map-layer"),
                        # Camada para popups dinâmicos
                        dl.LayerGroup(id="map-popup"),
                        # Camada para tooltips (opcional)
                        dl.LayerGroup(id="map-tooltip"),
                    ],
                    center=[-15, -55],  # Centro no Brasil
                    zoom=4,
                    style={
                        "width": "100%",
                        "height": "60vh",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                        "border": "1px solid #dee2e6",
                    },
                    id="world-map",
                    # Configurações de interação
                    dragging=True,
                    touchZoom=True,
                    scrollWheelZoom=True,
                    doubleClickZoom=True,
                    boxZoom=True,
                    keyboard=True,
                    # Configurações de performance
                    zoomAnimation=True,
                    fadeAnimation=True,
                    markerZoomAnimation=True,
                ),
                # Loading indicator para operações do mapa
                dbc.Spinner(
                    html.Div(id="map-loading-output"),
                    color="primary",
                    type="grow",
                    size="sm",
                    spinner_class_name="mt-2",
                ),
            ],
            className="mb-4",
        )
        logger.info("✅ Mapa mundial criado com sucesso")
        return map_component
    except Exception as e:
        logger.error(f"❌ Erro ao criar mapa: {e}")
        return _create_fallback_map()


def create_location_marker(lat, lon, timezone, location_info):
    """
    Cria um marcador para a localização selecionada.
    Args:
        lat (float): Latitude
        lon (float): Longitude
        timezone (str): Fuso horário
        location_info (str): Informações da localização
    Returns:
        dl.Marker: Marcador para a localização
    """
    try:
        marker = dl.Marker(
            position=[lat, lon],
            children=[
                dl.Tooltip(
                    f"📍 {location_info or 'Local selecionado'}\n"
                    f"Lat: {lat:.4f}, Lon: {lon:.4f}\n"
                    f"Fuso: {timezone or 'N/A'}",
                    direction="top",
                    offset=[0, -10],
                    opacity=0.8,
                ),
                dl.Popup(
                    [
                        html.Div(
                            [
                                html.H5(
                                    "📍 Localização Selecionada",
                                    style={"marginBottom": "10px", "color": "#2d5016"},
                                ),
                                html.P(
                                    [html.Strong("Coordenadas: "), f"{lat:.6f}, {lon:.6f}"],
                                    style={"marginBottom": "5px"},
                                ),
                                html.P(
                                    [html.Strong("Fuso Horário: "), timezone or "Não identificado"],
                                    style={"marginBottom": "5px"},
                                ),
                                html.P(
                                    [
                                        html.Strong("Local: "),
                                        location_info or "Local não identificado",
                                    ],
                                    style={"marginBottom": "10px", "fontSize": "12px"},
                                ),
                                html.Hr(style={"margin": "10px 0"}),
                                html.Small(
                                    "Clique em Salvar Favorito para adicionar à lista",
                                    style={"color": "#666", "fontStyle": "italic"},
                                ),
                            ],
                            style={"minWidth": "200px"},
                        )
                    ]
                ),
            ],
            icon=dl.Icon(
                iconUrl=(
                    "https://raw.githubusercontent.com/pointhi/"
                    "leaflet-color-markers/master/img/"
                    "marker-icon-2x-red.png"
                ),
                shadowUrl=(
                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/"
                    "0.7.7/images/marker-shadow.png"
                ),
                iconSize=[25, 41],
                iconAnchor=[12, 41],
                popupAnchor=[1, -34],
                shadowSize=[41, 41],
            ),
            id="selected-location-marker",
        )
        logger.debug(f"📌 Marcador criado para: {lat:.4f}, {lon:.4f}")
        return marker
    except Exception as e:
        logger.error(f"❌ Erro ao criar marcador de localização: {e}")
        return dl.Marker(position=[lat, lon])


def create_user_location_marker(lat, lon):
    """
    Cria um marcador especial para a localização do usuário.
    Args:
        lat (float): Latitude
        lon (float): Longitude
    Returns:
        dl.Marker: Marcador para localização do usuário
    """
    try:
        marker = dl.Marker(
            position=[lat, lon],
            children=[
                dl.Tooltip(
                    "👤 Sua localização atual", direction="top", offset=[0, -10], opacity=0.8
                ),
                dl.Popup(
                    [
                        html.Div(
                            [
                                html.H5(
                                    "👤 Sua Localização",
                                    style={"marginBottom": "10px", "color": "#0d6efd"},
                                ),
                                html.P(f"Latitude: {lat:.6f}"),
                                html.P(f"Longitude: {lon:.6f}"),
                                html.P("Localização detectada automaticamente"),
                                html.Hr(style={"margin": "10px 0"}),
                                html.Small(
                                    "Esta é sua posição atual",
                                    style={"color": "#666", "fontStyle": "italic"},
                                ),
                            ],
                            style={"minWidth": "200px"},
                        )
                    ]
                ),
            ],
            icon=dl.Icon(
                iconUrl=(
                    "https://raw.githubusercontent.com/pointhi/"
                    "leaflet-color-markers/master/img/"
                    "marker-icon-2x-blue.png"
                ),
                shadowUrl=(
                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/"
                    "0.7.7/images/marker-shadow.png"
                ),
                iconSize=[25, 41],
                iconAnchor=[12, 41],
                popupAnchor=[1, -34],
                shadowSize=[41, 41],
            ),
            id="user-location-marker",
        )
        logger.debug(f"👤 Marcador de usuário criado para: {lat:.4f}, {lon:.4f}")
        return marker
    except Exception as e:
        logger.error(f"❌ Erro ao criar marcador de usuário: {e}")
        return dl.Marker(position=[lat, lon])


def create_favorite_markers(favorites):
    """
    Cria marcadores para todos os favoritos salvos.
    Args:
        favorites (list): Lista de favoritos
    Returns:
        list: Lista de marcadores de favoritos
    """
    markers = []
    if not favorites:
        return markers
    try:
        for fav in favorites:
            marker = dl.Marker(
                position=[fav.get("lat", 0), fav.get("lon", 0)],
                children=[
                    dl.Tooltip(
                        f"⭐ {fav.get('location_info', 'Local favorito')}",
                        direction="top",
                        offset=[0, -10],
                        opacity=0.8,
                    ),
                    dl.Popup(
                        [
                            html.Div(
                                [
                                    html.H5(
                                        "⭐ Local Favorito",
                                        style={"marginBottom": "10px", "color": "#ffc107"},
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Coordenadas: "),
                                            f"{fav.get('lat_dms', 'N/A')}, "
                                            f"{fav.get('lon_dms', 'N/A')}",
                                        ],
                                        style={"marginBottom": "5px"},
                                    ),
                                    html.P(
                                        [html.Strong("Fuso Horário: "), fav.get("timezone", "N/A")],
                                        style={"marginBottom": "5px"},
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Local: "),
                                            fav.get("location_info", "Local não identificado"),
                                        ],
                                        style={"marginBottom": "10px", "fontSize": "12px"},
                                    ),
                                    html.Hr(style={"margin": "10px 0"}),
                                    html.Small(
                                        "Salvo na lista de favoritos",
                                        style={"color": "#666", "fontStyle": "italic"},
                                    ),
                                ],
                                style={"minWidth": "220px"},
                            )
                        ]
                    ),
                ],
                icon=dl.Icon(
                    iconUrl=(
                        "https://raw.githubusercontent.com/pointhi/"
                        "leaflet-color-markers/master/img/"
                        "marker-icon-2x-gold.png"
                    ),
                    shadowUrl=(
                        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/"
                        "0.7.7/images/marker-shadow.png"
                    ),
                    iconSize=[25, 41],
                    iconAnchor=[12, 41],
                    popupAnchor=[1, -34],
                    shadowSize=[41, 41],
                ),
                id=f"favorite-marker-{fav.get('id', 'unknown')}",
            )
            markers.append(marker)
        logger.info(f"⭐ Criados {len(markers)} marcadores de favoritos")
        return markers
    except Exception as e:
        logger.error(f"❌ Erro ao criar marcadores de favoritos: {e}")
        return []


def create_click_help_tooltip():
    """
    Cria um tooltip de ajuda para cliques no mapa.
    Returns:
        dl.Tooltip: Tooltip de ajuda
    """
    return dl.Tooltip(
        "Clique em qualquer lugar do mapa para selecionar coordenadas",
        permanent=False,
        direction="top",
        opacity=0.8,
        className="help-tooltip",
    )


def _create_fallback_map():
    """
    Cria mapa de fallback em caso de erro.
    Returns:
        html.Div: Mapa de fallback
    """
    logger.warning("🔄 Criando mapa de fallback")
    return html.Div(
        [
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle me-2"),
                    "Mapa temporariamente indisponível. ",
                    "Recarregue a página ou tente novamente mais tarde.",
                ],
                color="warning",
                className="my-3",
            ),
            html.Div(
                "🗺️ Mapa Mundial (carregando...)",
                style={
                    "width": "100%",
                    "height": "400px",
                    "backgroundColor": "#f8f9fa",
                    "border": "1px solid #dee2e6",
                    "borderRadius": "8px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "color": "#6c757d",
                },
            ),
        ],
        className="mb-4",
    )


# Funções de utilidade para o mapa
def get_map_bounds(center_lat, center_lon, zoom_level):
    """
    Calcula os bounds do mapa baseado no centro e zoom.
    Args:
        center_lat (float): Latitude do centro
        center_lon (float): Longitude do centro
        zoom_level (int): Nível de zoom
    Returns:
        dict: Bounds do mapa
    """
    try:
        # Cálculo simplificado dos bounds
        lat_offset = 180 / (2**zoom_level)
        lon_offset = 360 / (2**zoom_level)
        return {
            "north": center_lat + lat_offset,
            "south": center_lat - lat_offset,
            "east": center_lon + lon_offset,
            "west": center_lon - lon_offset,
        }
    except Exception as e:
        logger.error(f"❌ Erro ao calcular bounds do mapa: {e}")
        return None


def validate_coordinates(lat, lon):
    """
    Valida se as coordenadas são válidas.
    Args:
        lat (float): Latitude
        lon (float): Longitude
    Returns:
        bool: True se coordenadas são válidas
    """
    try:
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)
    except (TypeError, ValueError):
        return False


logger.info("✅ Componente do mapa mundial carregado com sucesso")
