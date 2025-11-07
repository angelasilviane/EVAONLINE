"""
Teste simples de Tabs usando dcc.Tabs (Dash Core Components).
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_simple_tabs_test():
    """Teste com dcc.Tabs - mais estável que dbc.Tabs."""
    return html.Div(
        [
            html.H3("🧪 TESTE COM dcc.Tabs (Dash Core)", className="text-success mb-3"),
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5("📌 Card está renderizando!", className="text-primary mb-3"),
                            # ✅ Usando dcc.Tabs ao invés de dbc.Tabs
                            dcc.Tabs(
                                id="test-tabs",
                                value="tab-1",
                                style={"border": "3px solid red", "backgroundColor": "#ffffcc"},
                                children=[
                                    dcc.Tab(
                                        label="🔴 TAB 1 CLIQUE AQUI",
                                        value="tab-1",
                                        style={
                                            "padding": "15px",
                                            "fontSize": "18px",
                                            "fontWeight": "bold",
                                        },
                                        selected_style={
                                            "backgroundColor": "#ccffcc",
                                            "border": "3px solid green",
                                            "fontWeight": "bold",
                                        },
                                        children=[
                                            html.Div(
                                                [
                                                    html.H4(
                                                        "✅ TAB 1 FUNCIONOU!",
                                                        className="text-success p-4",
                                                    )
                                                ]
                                            )
                                        ],
                                    ),
                                    dcc.Tab(
                                        label="🔵 TAB 2 CLIQUE AQUI",
                                        value="tab-2",
                                        style={
                                            "padding": "15px",
                                            "fontSize": "18px",
                                            "fontWeight": "bold",
                                        },
                                        selected_style={
                                            "backgroundColor": "#ffffcc",
                                            "border": "3px solid purple",
                                            "fontWeight": "bold",
                                        },
                                        children=[
                                            html.Div(
                                                [
                                                    html.H4(
                                                        "✅ TAB 2 FUNCIONOU!",
                                                        className="text-info p-4",
                                                    )
                                                ]
                                            )
                                        ],
                                    ),
                                ],
                            ),
                        ]
                    )
                ],
                className="mb-3",
            ),
            html.P(
                "🔍 Se os BOTÕES aparecem agora, o problema era dbc.Tabs!", className="text-danger"
            ),
        ]
    )
