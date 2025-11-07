"""
Tabs do Mapa Mundial seguindo EXATAMENTE documentação oficial dbc.Tabs.
Ref: https://www.dash-bootstrap-components.com/docs/components/tabs/

Padrão: Card > CardHeader(Tabs) > CardBody(id) + Callback
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from loguru import logger


def create_world_tabs_card():
    """
    Cria Card com tabs seguindo EXATAMENTE a documentação oficial.

    Estrutura:
        dbc.Card([
            dbc.CardHeader(dbc.Tabs([...])),
            dbc.CardBody(id="map-tab-content")
        ])

    O conteúdo é inserido via callback (ver world_map_tabs_callback.py)
    """
    logger.info("🎨 Criando tabs do mapa (padrão oficial dbc)")

    return dbc.Card(
        [
            # ✅ Tabs no CardHeader (seguindo documentação oficial)
            dbc.CardHeader(
                dbc.Tabs(
                    id="map-tabs",
                    active_tab="tab-calculate",
                    children=[
                        # Tabs SEM children (conteúdo via callback)
                        dbc.Tab(label="📍 Calcular ETo", tab_id="tab-calculate"),
                        dbc.Tab(label="🗺️ Explorar Cidades", tab_id="tab-explore"),
                    ],
                )
            ),
            # ✅ CardBody com ID para callback preencher
            dbc.CardBody(id="map-tab-content", className="p-3"),
        ],
        className="mb-4 shadow-sm",
    )


def create_world_real_map():
    """
    Layout completo do mapa mundial com tabs, geoloc e favoritos.
    """
    logger.info("🎨 Criando layout completo do mapa mundial")

    return html.Div(
        [
            # Componente de geolocalização
            dcc.Geolocation(
                id="geolocation",
                update_now=False,
                high_accuracy=True,
                maximum_age=0,
                timeout=10000,
                show_alert=True,
            ),
            # Modal para resultados
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
                    dbc.ModalBody(id="modal-body"),
                    dbc.ModalFooter(dbc.Button("Fechar", id="close-modal", className="ms-auto")),
                ],
                id="result-modal",
                size="lg",
                is_open=False,
            ),
            # Título
            html.Div(
                [
                    html.H3(
                        [
                            html.I(className="fas fa-globe me-2", style={"color": "#2d5016"}),
                            "Mapa Mundial - Cálculo de ETo com Fusão de Dados",
                        ],
                        className="text-esalq mb-2",
                    ),
                    html.P(
                        [
                            html.I(className="fas fa-filter me-2"),
                            "Fusão via Ensemble Kalman Filter (EnKF) | ",
                            html.I(className="fas fa-earth-americas me-2"),
                            "Clique em qualquer ponto do mapa para calcular ETo",
                        ],
                        className="text-muted mb-3",
                        style={"fontSize": "14px"},
                    ),
                ]
            ),
            # ✅ Card com Tabs (padrão oficial)
            create_world_tabs_card(),
            # Instruções colapsáveis
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            html.Div(
                                [
                                    html.P(
                                        [
                                            html.I(
                                                className="fas fa-location-dot me-2 text-danger"
                                            ),
                                            html.Strong("Sua localização: "),
                                            "Clique no botão de localização",
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.I(className="fas fa-map-pin me-2 text-primary"),
                                            html.Strong("Pontos de interesse: "),
                                            "Clique no mapa para adicionar até 9 pontos",
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.I(className="fas fa-star me-2 text-warning"),
                                            html.Strong("Favoritos: "),
                                            "Salve até 20 localizações favoritas",
                                        ],
                                        className="mb-0",
                                    ),
                                ]
                            )
                        ],
                        title=[html.I(className="fas fa-info-circle me-2"), "Como usar o mapa"],
                    )
                ],
                start_collapsed=True,
                flush=True,
                className="mb-3",
            ),
            # Favoritos
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            html.Div(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.P(
                                                        [
                                                            html.I(
                                                                className="fas fa-star me-2 text-warning"
                                                            ),
                                                            html.Strong(
                                                                id="favorites-count",
                                                                children="0 favoritos",
                                                            ),
                                                        ],
                                                        className="mb-2",
                                                    )
                                                ],
                                                width=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Button(
                                                        [
                                                            html.I(className="fas fa-trash me-2"),
                                                            "Limpar Tudo",
                                                        ],
                                                        id="clear-all-favorites-btn",
                                                        color="danger",
                                                        size="sm",
                                                        outline=True,
                                                        disabled=True,
                                                        className="float-end",
                                                    )
                                                ],
                                                width=6,
                                            ),
                                        ]
                                    ),
                                    # Store para página atual
                                    dcc.Store(id="favorites-current-page", data=1),
                                    # Controles de paginação (topo)
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Itens por página:", className="small me-2"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="favorites-page-size",
                                                        options=[
                                                            {"label": "5", "value": 5},
                                                            {"label": "10", "value": 10},
                                                            {"label": "20", "value": 20},
                                                        ],
                                                        value=5,
                                                        clearable=False,
                                                        searchable=False,
                                                        style={
                                                            "width": "80px",
                                                            "display": "inline-block",
                                                        },
                                                    ),
                                                ],
                                                width=12,
                                                className="mb-2",
                                            )
                                        ]
                                    ),
                                    # Lista de favoritos
                                    html.Div(
                                        id="favorites-list", className="favorites-scroll mb-3"
                                    ),
                                    # Navegação de páginas
                                    html.Div(
                                        [
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        [html.I(className="fas fa-chevron-left")],
                                                        id="favorites-prev-page",
                                                        size="sm",
                                                        outline=True,
                                                        disabled=True,
                                                    ),
                                                    dbc.Button(
                                                        id="favorites-pagination-info",
                                                        size="sm",
                                                        color="light",
                                                        disabled=True,
                                                        style={"minWidth": "100px"},
                                                    ),
                                                    dbc.Button(
                                                        [html.I(className="fas fa-chevron-right")],
                                                        id="favorites-next-page",
                                                        size="sm",
                                                        outline=True,
                                                        disabled=True,
                                                    ),
                                                ],
                                                id="favorites-pagination",
                                                className="d-flex justify-content-center",
                                            )
                                        ],
                                        className="text-center",
                                    ),
                                ]
                            )
                        ],
                        title=[html.I(className="fas fa-star me-2"), "Localizações Favoritas"],
                    )
                ],
                start_collapsed=True,
                flush=True,
                className="mb-3",
            ),
            # Modal de confirmação de limpeza
            dbc.Modal(
                [
                    dbc.ModalHeader("Confirmar Exclusão"),
                    dbc.ModalBody(
                        [
                            html.P(
                                [
                                    html.I(
                                        className="fas fa-exclamation-triangle me-2 text-warning"
                                    ),
                                    "Tem certeza que deseja excluir ",
                                ]
                            ),
                            html.P(id="clear-favorites-count", className="text-center fw-bold"),
                            html.P(
                                "Esta ação não pode ser desfeita.", className="text-muted small"
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancelar", id="cancel-clear-favorites", outline=True),
                            dbc.Button(
                                "Excluir Tudo", id="confirm-clear-favorites", color="danger"
                            ),
                        ]
                    ),
                ],
                id="clear-favorites-modal",
                is_open=False,
            ),
        ]
    )  # ← Fecha o html.Div principal do return
