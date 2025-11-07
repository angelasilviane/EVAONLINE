"""
Callbacks para a página inicial - busca dados da API
"""

import logging
import requests
from dash import Input, Output, html
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def register_home_callbacks(app):
    """Registra callbacks da página inicial."""

    @app.callback(
        Output("api-status-display", "children"),
        Input("interval-component", "n_intervals"),
    )
    def update_api_status(n_intervals):
        """Atualiza o status da API."""
        try:
            # Fazer chamada para a API de health
            response = requests.get(
                "http://localhost:8000/api/v1/health", timeout=5
            )
            data = response.json()

            # Criar cards com informações
            cards = [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H5(
                                    "Status da API", className="card-title"
                                ),
                                html.P(
                                    f"Serviço: {data.get('service', 'N/A')}",
                                    className="card-text",
                                ),
                                html.P(
                                    f"Versão: {data.get('version', 'N/A')}",
                                    className="card-text",
                                ),
                                html.P(
                                    f"Status: {data.get('status', 'N/A')}",
                                    className="card-text",
                                ),
                                dbc.Badge(
                                    (
                                        "Online"
                                        if data.get("status") == "ok"
                                        else "Offline"
                                    ),
                                    color=(
                                        "success"
                                        if data.get("status") == "ok"
                                        else "danger"
                                    ),
                                    className="mt-2",
                                ),
                            ]
                        )
                    ],
                    className="mb-3",
                )
            ]

            return cards

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao conectar com API: {e}")
            return dbc.Alert(
                f"Erro ao conectar com a API: {str(e)}",
                color="danger",
                className="mt-3",
            )
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return dbc.Alert(
                f"Erro inesperado: {str(e)}", color="warning", className="mt-3"
            )

    @app.callback(
        Output("services-status-display", "children"),
        Input("interval-component", "n_intervals"),
    )
    def update_services_status(n_intervals):
        """Atualiza o status dos serviços."""
        try:
            # Fazer chamada para a API de status dos serviços
            response = requests.get(
                "http://localhost:8000/api/v1/api/internal/" "services/status",
                timeout=10,
            )
            data = response.json()

            # Criar cards para cada serviço
            service_cards = []

            for service_id, service_info in data.get("services", {}).items():
                status_color = (
                    "success"
                    if service_info.get("status") == "healthy"
                    else "danger"
                )

                card = dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H6(
                                    service_info.get("name", service_id),
                                    className="card-title",
                                ),
                                html.P(
                                    f"Status: {service_info.get('status', 'unknown')}",
                                    className="card-text",
                                ),
                                dbc.Badge(
                                    (
                                        "Disponível"
                                        if service_info.get("available", False)
                                        else "Indisponível"
                                    ),
                                    color=status_color,
                                    className="mt-2",
                                ),
                            ]
                        )
                    ],
                    className="mb-2",
                )
                service_cards.append(card)

            # Card de resumo
            summary_card = dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(
                                "Resumo dos Serviços", className="card-title"
                            ),
                            html.P(
                                f"Total: {data.get('total_services', 0)}",
                                className="card-text",
                            ),
                            html.P(
                                f"Saúde: {data.get('healthy_count', 0)}",
                                className="card-text",
                            ),
                        ]
                    )
                ],
                className="mb-3",
            )

            return [summary_card] + service_cards

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao conectar com API de serviços: {e}")
            return dbc.Alert(
                f"Erro ao conectar com a API de serviços: {str(e)}",
                color="danger",
                className="mt-3",
            )
        except Exception as e:
            logger.error(f"Erro inesperado nos serviços: {e}")
            return dbc.Alert(
                f"Erro inesperado: {str(e)}", color="warning", className="mt-3"
            )
