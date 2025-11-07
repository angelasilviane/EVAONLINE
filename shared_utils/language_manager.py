from dash import Input, Output, State, no_update
from loguru import logger


def register_language_callbacks(app):
    """
    Registra os callbacks necessários para o gerenciamento de idioma.
    Esta função é chamada uma vez no app.py para configurar a lógica.

    Args:
        app (dash.Dash): A instância da aplicação Dash.
    """

    # Usa app.callback ao invés de @callback para registrar apenas quando explicitamente chamado
    @app.callback(
        Output("language-store", "data"),
        Input("language-dropdown", "value"),  # O Input é o valor do dropdown
        State("language-store", "data"),
        prevent_initial_call=True,
    )
    def update_language(selected_lang, current_lang):
        """
        Atualiza o idioma no dcc.Store quando uma nova opção é selecionada no dropdown.

        Args:
            selected_lang: Novo idioma selecionado no dropdown
            current_lang: Idioma atual armazenado no store

        Returns:
            Novo idioma se diferente do atual, caso contrário no_update
        """
        if selected_lang and selected_lang != current_lang:
            logger.info(f"🌐 Idioma alterado para: {selected_lang}")
            return selected_lang

        # Se nenhum novo idioma foi selecionado, não atualiza
        return no_update


# 4. REMOÇÃO: A função não precisa retornar nada.
#    Sua única função é registrar o callback na instância do app.
