import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, callback, dcc, html


def create_admin_page():
    """
    Página de administração com acesso a dashboards.

    Features:
    - Login via API
    - Acesso Grafana (embed)
    - Acesso Prometheus (embed)
    - Gerenciamento de usuários
    - Logs de aplicação
    """

    return dbc.Container(
        [
            dbc.Row([dbc.Col([html.H2("🔐 Administração EVAonline", className="mt-4 mb-4")])]),
            # Tabs para diferentes seções
            dcc.Tabs(
                id="admin-tabs",
                value="dashboards",
                children=[
                    # Tab 1: Dashboards
                    dcc.Tab(
                        label="📊 Dashboards",
                        value="dashboards",
                        children=[
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Iframe(
                                                src="http://localhost:3000/d/evaonline-main",
                                                style={
                                                    "width": "100%",
                                                    "height": "800px",
                                                    "border": "none",
                                                },
                                            )
                                        ],
                                        width=12,
                                    )
                                ],
                                className="mt-3",
                            )
                        ],
                    ),
                    # Tab 2: Logs
                    dcc.Tab(
                        label="📝 Logs",
                        value="logs",
                        children=[
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [html.Div(id="logs-container", style={"fontSize": "12px"})],
                                        width=12,
                                    )
                                ],
                                className="mt-3",
                            )
                        ],
                    ),
                    # Tab 3: Users
                    dcc.Tab(
                        label="👥 Usuários",
                        value="users",
                        children=[
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [dbc.Table(id="users-table", striped=True, hover=True)],
                                        width=12,
                                    )
                                ],
                                className="mt-3",
                            )
                        ],
                    ),
                ],
                className="mt-4",
            ),
        ],
        fluid=True,
    )


@callback(Output("logs-container", "children"), Input("admin-tabs", "value"))
def load_logs(tab_value):
    if tab_value != "logs":
        return ""

    try:
        response = requests.get("http://localhost:8000/api/v1/logs?limit=100")
        logs = response.json()

        return html.Pre(
            "\n".join([f"[{log['timestamp']}] {log['level']}: {log['message']}" for log in logs])
        )
    except Exception:
        return "Erro carregando logs"
