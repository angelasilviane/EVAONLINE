"""
Página de cálculo ETo do ETO Calculator.

Features:
- Exibe informações completas da localização selecionada
- Interface para cálculo de Evapotranspiração
- Integração com sistema de cache
- Design responsivo e intuitivo
"""

import logging
from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import dcc, html

logger = logging.getLogger(__name__)

# Layout da página ETo
eto_layout = html.Div(
    [
        dbc.Container(
            [
                # Cabeçalho da página
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(
                                    "📊 Calculadora ETo",
                                    className="text-center mb-3",
                                    style={"color": "#2c3e50", "fontWeight": "bold"},
                                ),
                                html.P(
                                    "Calcule a Evapotranspiração de Referência para a "
                                    "localização selecionada",
                                    className="text-center lead text-muted mb-4",
                                ),
                            ],
                            width=12,
                        )
                    ]
                ),
                # Informações da localização (atualizadas via callback)
                html.Div(id="eto-location-info", className="mb-4"),
                # Card principal de cálculo
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                # Card: Configurações do Cálculo
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.H5(
                                                    "⚙️ Configurações do Cálculo", className="mb-0"
                                                )
                                            ]
                                        ),
                                        dbc.CardBody(
                                            [
                                                # Seletor de Período
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    "Data Inicial:",
                                                                    className="fw-bold mb-2",
                                                                ),
                                                                dcc.DatePickerSingle(
                                                                    id="start-date-picker",
                                                                    min_date_allowed=datetime(
                                                                        1940, 1, 1
                                                                    ),
                                                                    max_date_allowed=datetime.now(),
                                                                    initial_visible_month=datetime.now(),
                                                                    date=datetime.now()
                                                                    - timedelta(days=7),
                                                                    display_format="DD/MM/YYYY",
                                                                    className="mb-3",
                                                                ),
                                                            ],
                                                            md=6,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    "Data Final:",
                                                                    className="fw-bold mb-2",
                                                                ),
                                                                dcc.DatePickerSingle(
                                                                    id="end-date-picker",
                                                                    min_date_allowed=datetime(
                                                                        1940, 1, 1
                                                                    ),
                                                                    max_date_allowed=datetime.now(),
                                                                    initial_visible_month=datetime.now(),
                                                                    date=datetime.now(),
                                                                    display_format="DD/MM/YYYY",
                                                                    className="mb-3",
                                                                ),
                                                            ],
                                                            md=6,
                                                        ),
                                                    ]
                                                ),
                                                # Validação do período
                                                html.Div(id="period-validation", className="mb-3"),
                                                # Fonte de Dados
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    "Fonte de Dados Climáticos:",
                                                                    className="fw-bold mb-2",
                                                                ),
                                                                dbc.Select(
                                                                    id="data-source-select",
                                                                    options=[
                                                                        {
                                                                            "label": (
                                                                                "📡 Open-Meteo "
                                                                                "(Recomendado)"
                                                                            ),
                                                                            "value": "openmeteo",
                                                                        },
                                                                        {
                                                                            "label": "🌤️ NASA POWER",
                                                                            "value": "nasa",
                                                                        },
                                                                        {
                                                                            "label": "🔍 Dados Locais",
                                                                            "value": "local",
                                                                        },
                                                                    ],
                                                                    value="openmeteo",
                                                                    className="mb-3",
                                                                ),
                                                            ],
                                                            width=12,
                                                        )
                                                    ]
                                                ),
                                                # Badge de fonte de dados selecionada
                                                html.Div(id="data-source-badge", className="mt-2"),
                                                # Botão de cálculo
                                                dbc.Button(
                                                    "🚀 Calcular ETo",
                                                    id="calculate-eto-btn",
                                                    color="primary",
                                                    size="lg",
                                                    className="w-100",
                                                    n_clicks=0,
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="mb-4 shadow-sm",
                                ),
                                # Card: Resultados do Cálculo
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [html.H5("📈 Resultados do Cálculo", className="mb-0")]
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.Alert(
                                                    [
                                                        html.I(className="bi bi-info-circle me-2"),
                                                        "Os resultados aparecerão aqui após o cálculo."
                                                        "Certifique-se de que selecionou uma "
                                                        "localização no mapa.",
                                                    ],
                                                    color="info",
                                                    id="results-placeholder",
                                                    className="mb-0",
                                                ),
                                                html.Div(id="eto-results-container"),
                                            ]
                                        ),
                                    ],
                                    className="mb-4 shadow-sm",
                                ),
                                # Card: Informações Técnicas
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [html.H5("🔬 Informações Técnicas", className="mb-0")]
                                        ),
                                        dbc.CardBody(
                                            [
                                                html.P(
                                                    [
                                                        html.Strong("Método utilizado: "),
                                                        "Penman-Monteith (FAO-56)",
                                                    ],
                                                    className="mb-2",
                                                ),
                                                html.P(
                                                    [
                                                        html.Strong("Parâmetros calculados: "),
                                                        "ETo diária, temperatura, umidade, radiação solar,"
                                                        "velocidade do vento",
                                                    ],
                                                    className="mb-2",
                                                ),
                                                html.P(
                                                    [
                                                        html.Strong("Precisão: "),
                                                        "Baseada nos dados da fonte selecionada e "
                                                        "calibração local",
                                                    ],
                                                    className="mb-0",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="shadow-sm",
                                ),
                            ],
                            lg=8,
                            className="mx-auto",
                        )
                    ]
                ),
                # Stores específicos da página ETo
                dcc.Store(id="eto-calculation-data"),
                dcc.Store(id="eto-results-store"),
            ],
            fluid=True,
        )
    ]
)


# Funções auxiliares para a página ETo
def create_period_validation_alert(is_valid, message):
    """
    Cria alerta de validação do período selecionado.
    Args:
        is_valid (bool): Se o período é válido
        message (str): Mensagem de validação
    Returns:
        dbc.Alert: Alerta de validação
    """
    color = "success" if is_valid else "danger"
    icon = "bi bi-check-circle" if is_valid else "bi bi-exclamation-triangle"
    return dbc.Alert(
        [
            html.I(className=f"{icon} me-2"),
            html.Strong("Período " + ("válido" if is_valid else "inválido") + ": "),
            message,
        ],
        color=color,
        className="py-2",
    )


def create_eto_results_card(results_data):
    """
    Cria card com os resultados do cálculo ETo.
    Args:
        results_data (dict): Dados dos resultados
    Returns:
        dbc.Card: Card com resultados
    """
    if not results_data:
        return dbc.Alert(
            "Nenhum resultado disponível. Execute o cálculo primeiro.", color="warning"
        )
    return dbc.Card(
        [
            dbc.CardHeader([html.H6("📊 Resultados do Cálculo ETo", className="mb-0")]),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P(
                                        [
                                            html.Strong("ETo Média: "),
                                            html.Span(
                                                f"{results_data.get('eto_mean', 0):.2f} mm/dia",
                                                className="text-success fw-bold",
                                            ),
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("ETo Máxima: "),
                                            f"{results_data.get('eto_max', 0):.2f} mm/dia",
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("ETo Mínima: "),
                                            f"{results_data.get('eto_min', 0):.2f} mm/dia",
                                        ]
                                    ),
                                ],
                                md=6,
                            ),
                            dbc.Col(
                                [
                                    html.P(
                                        [
                                            html.Strong("Período: "),
                                            f"{results_data.get('start_date', 'N/A')} a "
                                            f"{results_data.get('end_date', 'N/A')}",
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Dias calculados: "),
                                            str(results_data.get("days_count", 0)),
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Fonte: "),
                                            results_data.get("data_source", "N/A"),
                                        ]
                                    ),
                                ],
                                md=6,
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.P(
                        [
                            html.Small(
                                "Estes valores representam a evapotranspiração de "
                                "referência (ETo) calculada usando o método "
                                "Penman-Monteith padrão FAO-56.",
                                className="text-muted",
                            )
                        ]
                    ),
                ]
            ),
        ]
    )


def create_calculation_error_alert(error_message):
    """
    Cria alerta de erro no cálculo.
    Args:
        error_message (str): Mensagem de erro
    Returns:
        dbc.Alert: Alerta de erro
    """
    return dbc.Alert(
        [
            html.I(className="bi bi-exclamation-triangle me-2"),
            html.Strong("Erro no cálculo: "),
            error_message,
            html.Br(),
            html.Small(
                "Verifique a localização selecionada e tente novamente.", className="text-muted"
            ),
        ],
        color="danger",
        className="my-3",
    )


logger.info("✅ Página ETo carregada com sucesso")
