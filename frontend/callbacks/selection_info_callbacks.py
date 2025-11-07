"""
CORRIGIDO
Callbacks para exibir informações da seleção atual do usuário no mapa.

Features:
- Atualiza card de informações quando localização muda
- Feedback visual do estado de seleção
- Validações para habilitar/desabilitar botões
"""

import logging

import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output

logger = logging.getLogger(__name__)


def register_selection_info_callbacks(app):
    """
    Registra callbacks relacionados à exibição de informações de seleção
    """

    @app.callback(
        [Output("current-selection-info", "children"), Output("selection-badge", "children")],
        [Input("current-location", "data")],
    )
    def update_selection_info(current_location):
        """
        Atualiza o card de informações e badge baseado na
        localização selecionada
        """
        if not current_location or not current_location.get("lat"):
            # Nenhuma localização selecionada
            return (
                dbc.Alert(
                    [
                        html.I(className="bi bi-geo-alt me-2"),
                        "Nenhum ponto selecionado. ",
                        html.Strong("Clique em qualquer lugar do mapa"),
                        " para escolher uma localização ou use o botão de "
                        "localização (📍) para encontrar sua posição atual.",
                    ],
                    color="secondary",
                    className="d-flex align-items-center",
                ),
                "Selecione um ponto no mapa para habilitar",
            )
        # Localização válida selecionada - criar card informativo
        info_card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            [
                                html.I(className="bi bi-geo-alt-fill text-primary me-2"),
                                "📍 Localização Selecionada",
                            ],
                            className="d-flex align-items-center fw-bold",
                        )
                    ]
                ),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6("🌎 Coordenadas:", className="fw-bold mb-3"),
                                        html.Div(
                                            [
                                                html.Small("Latitude: ", className="text-muted"),
                                                html.Span(
                                                    current_location.get("lat_dms", "N/A"),
                                                    className="fw-bold text-primary",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Small("Longitude: ", className="text-muted"),
                                                html.Span(
                                                    current_location.get("lon_dms", "N/A"),
                                                    className="fw-bold text-primary",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Small("Decimal: ", className="text-muted"),
                                                (
                                                    f"({current_location.get('lat', 0):.6f}, "
                                                    f"{current_location.get('lon', 0):.6f})"
                                                ),
                                            ],
                                            className="mt-1 text-muted small",
                                        ),
                                    ],
                                    width=4,
                                    className="border-end",
                                ),
                                dbc.Col(
                                    [
                                        html.H6("🕐 Fuso Horário:", className="fw-bold mb-3"),
                                        html.Div(
                                            [
                                                html.I(className="bi bi-clock me-2"),
                                                html.Span(
                                                    current_location.get("timezone", "N/A"),
                                                    className="text-success fw-bold",
                                                ),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                    ],
                                    width=4,
                                    className="border-end",
                                ),
                                dbc.Col(
                                    [
                                        html.H6("📌 Localização:", className="fw-bold mb-3"),
                                        html.Div(
                                            [
                                                html.I(className="bi bi-geo me-2"),
                                                html.Span(
                                                    current_location.get(
                                                        "location_info", "Local não identificado"
                                                    ),
                                                    className="small",
                                                ),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                    ],
                                    width=4,
                                ),
                            ]
                        )
                    ]
                ),
            ],
            color="primary",
            outline=True,
            className="border-primary",
        )
        return info_card, "✅ Ponto selecionado"

    @app.callback(Output("selection-badge", "color"), [Input("current-location", "data")])
    def update_selection_badge_color(current_location):
        """
        Atualiza a cor do badge baseado no estado de seleção
        """
        if not current_location or not current_location.get("lat"):
            return "secondary"  # Cinza - não selecionado
        return "success"  # Verde - selecionado

    @app.callback(
        Output("current-selection-info", "className"), [Input("current-location", "data")]
    )
    def animate_selection_info(current_location):
        """
        Adiciona animação sutil quando uma nova localização é selecionada
        """
        base_class = "mt-3"
        if current_location and current_location.get("lat"):
            return f"{base_class} animate__animated animate__fadeIn"
        return base_class
