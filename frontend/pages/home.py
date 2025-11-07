"""
Página inicial do ETO Calculator com mapa mundial interativo.
"""

import logging

import dash_bootstrap_components as dbc
from ..components.favorites_components import (
    create_calc_eto_button,
    create_clear_favorites_button,
    create_favorite_button,
)
from dash import dcc, html

logger = logging.getLogger(__name__)

# Layout da página inicial
home_layout = html.Div(
    [
        dbc.Container(
            [
                # Título e descrição
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(
                                    "ETO Calculator - Mapa Mundial",
                                    className="text-center mb-4",
                                    style={"color": "#2c3e50"},
                                ),
                                html.P(
                                    "Selecione locais no mapa para calcular "
                                    "Evapotranspiração de Referência (ETo)",
                                    className="text-center text-muted mb-5",
                                ),
                            ],
                            width=12,
                        )
                    ]
                ),
                # Card de instruções
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.H4(
                                                    "📋 Como usar o mapa",
                                                    className="mb-0",
                                                )
                                            ],
                                            className="bg-primary text-white",
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.ListGroup(
                                                    [
                                                        dbc.ListGroupItem(
                                                            [
                                                                html.Span(
                                                                    "1.",
                                                                    className="fw-bold me-2",
                                                                ),
                                                                "Clique em qualquer ponto do mapa para "
                                                                "selecionar coordenadas",
                                                            ]
                                                        ),
                                                        dbc.ListGroupItem(
                                                            [
                                                                html.Span(
                                                                    "2.",
                                                                    className="fw-bold me-2",
                                                                ),
                                                                "Use o botão de localização (📍) para "
                                                                "encontrar sua posição atual",
                                                            ]
                                                        ),
                                                        dbc.ListGroupItem(
                                                            [
                                                                html.Span(
                                                                    "3.",
                                                                    className="fw-bold me-2",
                                                                ),
                                                                "Clique em 'Salvar Favorito' para adicionar à "
                                                                "lista (máx. 10 pontos)",
                                                            ]
                                                        ),
                                                        dbc.ListGroupItem(
                                                            [
                                                                html.Span(
                                                                    "4.",
                                                                    className="fw-bold me-2",
                                                                ),
                                                                "Use 'Calcular ETo' para ir para a página "
                                                                "de cálculos",
                                                            ]
                                                        ),
                                                    ],
                                                    flush=True,
                                                )
                                            ]
                                        ),
                                    ],
                                    className="mb-4 shadow-sm",
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
                # Botões de ação
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "Ações Rápidas",
                                                    className="card-title mb-3",
                                                ),
                                                html.Div(
                                                    [
                                                        create_calc_eto_button(),
                                                        create_favorite_button(),
                                                        dbc.Badge(
                                                            "Selecione um ponto no mapa para habilitar",
                                                            color="secondary",
                                                            className="ms-2 align-middle",
                                                            id="selection-badge",
                                                        ),
                                                    ],
                                                    className=(
                                                        "d-flex align-items-center flex-wrap gap-2"
                                                    ),
                                                ),
                                            ]
                                        )
                                    ],
                                    className="mb-4 shadow-sm",
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
                # Mapa mundial
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.H5(
                                                    "🗺️ Mapa Mundial Interativo",
                                                    className="mb-0",
                                                )
                                            ]
                                        ),
                                        dbc.CardBody(
                                            [
                                                # Placeholder for map - will implement later
                                                html.Div(
                                                    "🗺️ Mapa em desenvolvimento...",
                                                    style={
                                                        "padding": "40px",
                                                        "textAlign": "center",
                                                        "backgroundColor": "#f8f9fa",
                                                        "border": "2px dashed #dee2e6",
                                                        "borderRadius": "8px",
                                                        "height": "400px",
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                        "color": "#6c757d",
                                                        "fontSize": "18px",
                                                    },
                                                ),
                                                # Informações do ponto selecionado
                                                html.Div(
                                                    id="current-selection-info",
                                                    className="mt-3",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="shadow-sm",
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
                # Lista de Favoritos
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.Div(
                                                    [
                                                        html.H5(
                                                            "⭐ Lista de Favoritos",
                                                            className="mb-0 d-inline",
                                                        ),
                                                        dbc.Badge(
                                                            "0/10",
                                                            color="info",
                                                            className="ms-2",
                                                            id="favorites-count-badge",
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center",
                                                )
                                            ]
                                        ),
                                        dbc.CardBody(
                                            [
                                                html.Div(
                                                    id="favorites-list-container",
                                                    className="mb-3",
                                                ),
                                                html.Div(
                                                    [
                                                        create_clear_favorites_button(),
                                                        dbc.Alert(
                                                            "Lista de favoritos vazia. Adicione pontos "
                                                            "clicando no mapa e depois em "
                                                            "'Salvar Favorito'.",
                                                            color="info",
                                                            id="empty-favorites-alert",
                                                            className="mt-3",
                                                        ),
                                                    ]
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="shadow-sm",
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
                # Stores específicos da home (se necessário)
                dcc.Store(id="home-favorites-count", data=0),
            ],
            fluid=True,
        )
    ]
)


logger.info("✅ Página inicial carregada com sucesso")
