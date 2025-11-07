"""
CORRIGIDO
Callbacks para gerenciamento da lista de favoritos no frontend.

Features:
- Adicionar favoritos a partir da localização atual
- Excluir favoritos individuais
- Limpar lista completa
- Atualizar visualização da lista
- Validações e limites (máx. 10 favoritos)
"""

import logging
import uuid

import dash_bootstrap_components as dbc
from dash import callback_context, html
from dash.dependencies import ALL, Input, Output, State

logger = logging.getLogger(__name__)


def register_favorites_callbacks(app):
    """
    Registra todos os callbacks relacionados à lista de favoritos
    """

    # 1. ADICIONAR favorito à lista
    @app.callback(
        Output("favorites-store", "data", allow_duplicate=True),
        [Input("favorite-button", "n_clicks")],
        [State("current-location", "data"), State("favorites-store", "data")],
        prevent_initial_call=True,
    )
    def add_favorite(n_clicks, current_location, favorites):
        """Adiciona a localização atual à lista de favoritos"""
        if (
            n_clicks == 0
            or not current_location
            or not current_location.get("lat")
        ):
            return favorites

        # Garantir que favorites é uma lista
        if favorites is None:
            favorites = []

        # Verificar se já está nos favoritos
        for fav in favorites:
            if (
                abs(fav.get("lat", 0) - current_location.get("lat", 0)) < 0.001
                and abs(fav.get("lon", 0) - current_location.get("lon", 0))
                < 0.001
            ):
                logger.info("📍 Localização já está nos favoritos")
                return favorites

        # Limite de 10 favoritos
        if len(favorites) >= 10:
            logger.warning("❌ Limite de 10 favoritos atingido")
            return favorites

        # Adicionar novo favorito com ID único
        new_favorite = current_location.copy()
        new_favorite["id"] = f"fav_{len(favorites)}_{uuid.uuid4().hex[:8]}"

        # Garantir que temos todos os campos necessários
        if "lat_dms" not in new_favorite:
            from ..utils.timezone_utils import format_coordinates

            lat_dms, lon_dms = format_coordinates(
                new_favorite["lat"], new_favorite["lon"]
            )
            new_favorite["lat_dms"] = lat_dms
            new_favorite["lon_dms"] = lon_dms

        updated_favorites = favorites + [new_favorite]
        logger.info(
            f"⭐ Favorito adicionado: {new_favorite.get('location_info', 'Unknown')}"
        )

        return updated_favorites

    # 2. EXCLUIR favorito individual
    @app.callback(
        Output("favorites-store", "data", allow_duplicate=True),
        [Input({"type": "delete-favorite", "index": ALL}, "n_clicks")],
        [State("favorites-store", "data")],
        prevent_initial_call=True,
    )
    def delete_favorite(n_clicks_list, favorites):
        """Remove um favorito individual da lista"""
        ctx = callback_context
        if not ctx.triggered or not favorites:
            return favorites

        # Encontra qual botão de exclusão foi clicado
        triggered_id = ctx.triggered[0]["prop_id"]
        if "delete-favorite" in triggered_id:
            try:
                # Extrai o ID do favorito do componente que foi clicado
                fav_id = eval(triggered_id.split(".")[0])["index"]

                # Remove o favorito da lista
                updated_favorites = [
                    fav for fav in favorites if fav["id"] != fav_id
                ]
                logger.info(f"🗑️ Favorito removido: {fav_id}")
                return updated_favorites
            except Exception as e:
                logger.error(f"Erro ao excluir favorito: {e}")
                return favorites

        return favorites

    # 3. LIMPAR TODOS os favoritos
    @app.callback(
        Output("favorites-store", "data", allow_duplicate=True),
        [Input("clear-favorites-button", "n_clicks")],
        [State("favorites-store", "data")],
        prevent_initial_call=True,
    )
    def clear_all_favorites(n_clicks, favorites):
        """Limpa toda a lista de favoritos"""
        if n_clicks and n_clicks > 0:
            logger.info("🧹 Todos os favoritos foram removidos")
            return []
        return favorites

    # 4. ATUALIZAR VISUALIZAÇÃO da lista de favoritos
    @app.callback(
        [
            Output("favorites-list-container", "children"),
            Output("favorites-count-badge", "children"),
            Output("empty-favorites-alert", "style"),
        ],
        [Input("favorites-store", "data")],
    )
    def update_favorites_list(favorites):
        """Atualiza a exibição da lista de favoritos na interface"""
        if not favorites:
            return (
                html.Div(),
                "0/10",
                {"display": "block"},
            )  # Mostra alerta de lista vazia

        # Esconde alerta de lista vazia
        alert_style = {"display": "none"}

        # Cria tabela de favoritos
        table_header = [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Ponto", style={"width": "40%"}),
                        html.Th("Fuso Horário", style={"width": "30%"}),
                        html.Th("Ações Rápidas", style={"width": "30%"}),
                    ]
                )
            )
        ]

        table_rows = []
        for fav in favorites:
            row = html.Tr(
                [
                    html.Td(
                        [
                            html.Div(
                                fav.get("lat_dms", "N/A"), className="fw-bold"
                            ),
                            html.Div(
                                fav.get("lon_dms", "N/A"),
                                className="text-muted small",
                            ),
                            html.Div(
                                f"({fav.get('lat', 0):.4f}, {fav.get('lon', 0):.4f})",
                                className="text-muted small",
                            ),
                        ]
                    ),
                    html.Td(
                        [
                            html.Div(
                                fav.get("timezone", "N/A"), className="fw-bold"
                            ),
                            html.Div(
                                fav.get(
                                    "location_info", "Local não identificado"
                                ),
                                className="text-muted small mt-1",
                            ),
                        ]
                    ),
                    html.Td(
                        [
                            dbc.Button(
                                "📊 Calcular ETo",
                                color="success",
                                size="sm",
                                className="me-1 mb-1",
                                id={
                                    "type": "calc-fav-eto",
                                    "index": fav["id"],
                                },
                            ),
                            dbc.Button(
                                "❌ Excluir",
                                color="danger",
                                size="sm",
                                className="mb-1",
                                id={
                                    "type": "delete-favorite",
                                    "index": fav["id"],
                                },
                            ),
                        ],
                        style={"minWidth": "150px"},
                    ),
                ]
            )
            table_rows.append(row)

        table_body = [html.Tbody(table_rows)]

        table = dbc.Table(
            table_header + table_body,
            bordered=True,
            striped=True,
            hover=True,
            responsive=True,
            className="mt-3",
        )

        return table, f"{len(favorites)}/10", alert_style

    # 5. Callback para feedback visual do botão Salvar Favorito
    @app.callback(
        Output("favorite-button", "children", allow_duplicate=True),
        [Input("favorite-button", "n_clicks")],
        [State("favorites-store", "data"), State("current-location", "data")],
        prevent_initial_call=True,
    )
    def update_favorite_button_feedback(n_clicks, favorites, current_location):
        """
        Feedback visual temporário ao salvar favorito.
        """
        if n_clicks == 0:
            return [html.I(className="bi bi-star me-2"), "⭐ Salvar Favorito"]
        if not current_location or not current_location.get("lat"):
            return [html.I(className="bi bi-star me-2"), "⭐ Salvar Favorito"]
        # Feedback visual temporário
        return [html.I(className="bi bi-check-circle me-2"), "✅ Salvo!"]

    # 6. VALIDAÇÃO do botão Salvar Favorito
    @app.callback(
        Output("favorite-button", "children"),
        [Input("current-location", "data"), Input("favorites-store", "data")],
    )
    def update_favorite_button_content(current_location, favorites):
        """Atualiza o conteúdo do botão baseado no estado atual"""
        if not current_location or not current_location.get("lat"):
            return "⭐ Salvar Favorito"

        # Verifica se já está nos favoritos
        if favorites:
            for fav in favorites:
                if (
                    abs(fav.get("lat", 0) - current_location.get("lat", 0))
                    < 0.001
                    and abs(fav.get("lon", 0) - current_location.get("lon", 0))
                    < 0.001
                ):
                    return "✅ Já Salvo"

        # Verifica limite de favoritos
        if favorites and len(favorites) >= 10:
            return "📋 Limite Atingido"

        return "⭐ Salvar Favorito"

    # 7. FEEDBACK VISUAL do botão Salvar Favorito
    @app.callback(
        Output("favorite-button", "color"), [Input("favorites-store", "data")]
    )
    def update_favorite_button_color(favorites):
        """Muda a cor do botão quando atinge o limite de favoritos"""
        if favorites and len(favorites) >= 10:
            return "secondary"  # Cinza quando atingir limite
        return "primary"  # Azul normal
