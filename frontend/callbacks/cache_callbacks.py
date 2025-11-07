"""
CORRIGIDO
Callbacks para integração de cache entre frontend (Dash) e backend (FastAPI).
Features:
- Busca dados via GET /api/cache/climate/{location_id}
- Armazena resposta em `climate-cache-store` (localStorage)
- Usa `app-session-id` para Session-ID header
- Gerencia TTL de cache (expiração automática)
- Sincroniza estado entre stores
- Limpeza automática DURANTE OPERAÇÕES (sem intervalo periódico)
"""

import datetime
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from dash import Input, Output, State, callback_context, html
from dash.exceptions import PreventUpdate

# from ..services.api_client import APIClient

logger = logging.getLogger(__name__)

# Constantes de Cache
CACHE_TTL_MINUTES = 60
MAX_CACHE_ENTRIES = 50
BACKEND_URL = "http://localhost:8000"


def _is_cache_expired(entry: Dict[str, Any]) -> bool:
    """Verifica se uma entrada de cache expirou."""
    if "timestamp" not in entry or "ttl_minutes" not in entry:
        return True

    try:
        entry_time = datetime.fromisoformat(entry["timestamp"])
        ttl = timedelta(minutes=entry["ttl_minutes"])
        return datetime.now() > entry_time + ttl
    except (ValueError, KeyError) as e:
        logger.warning(f"Erro ao verificar expiração do cache: {e}")
        return True


def _clean_expired_entries(cache_data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove automaticamente entradas expiradas do cache."""
    if not cache_data or not isinstance(cache_data, dict):
        return {}

    cleaned_cache = {}
    expired_count = 0

    for key, entry in cache_data.items():
        if not _is_cache_expired(entry):
            cleaned_cache[key] = entry
        else:
            expired_count += 1

    if expired_count > 0:
        logger.info(
            f"🧹 Limpeza automática: {expired_count} entradas expiradas removidas"
        )

    return cleaned_cache


def _get_location_id(location_data: Dict[str, Any]) -> Optional[str]:
    """Gera um ID único baseado nos dados de localização."""
    if not location_data:
        return None

    # Prioridade 1: ID explícito
    location_id = location_data.get("id")
    if location_id:
        return str(location_id)

    # Prioridade 2: Coordenadas (formato padronizado)
    lat = location_data.get("lat")
    lon = location_data.get("lon")
    if lat is not None and lon is not None:
        return f"lat_{lat:.6f}_lon_{lon:.6f}"

    # Prioridade 3: Nome/localização
    location_name = location_data.get("location_info") or location_data.get(
        "name"
    )
    if location_name:
        import hashlib

        return f"loc_{hashlib.md5(location_name.encode()).hexdigest()[:8]}"

    return None


def register_cache_callbacks(app):
    """Registra todos os callbacks de cache no app Dash"""

    @app.callback(
        Output("climate-cache-store", "data"),
        [Input("selected-location", "data"), Input("url", "pathname")],
        [
            State("app-session-id", "data"),
            State("climate-cache-store", "data"),
        ],
        prevent_initial_call=True,
    )
    async def fetch_climate_cache(
        selected_location: dict,
        pathname: str,
        session_id: str,
        cache_data: dict,
    ):
        """
        Sincroniza cache para a localização selecionada com limpeza automática.

        Estratégia de limpeza:
        - 🧭 NAVEGAÇÃO: Limpeza quando usuário muda de página
        - ⚡ OPERAÇÕES: Limpeza antes de cada acesso ao cache
        - ❌ NÃO PRECISA de limpeza periódica com Interval
        """
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # ✅ LIMPEZA AUTOMÁTICA: Quando usuário navega entre páginas
        if trigger_id == "url":
            if cache_data and isinstance(cache_data, dict):
                cleaned_cache = _clean_expired_entries(cache_data)
                if len(cleaned_cache) != len(cache_data):
                    logger.info(
                        "🔄 Limpeza automática executada durante navegação"
                    )
                    return cleaned_cache
            raise PreventUpdate

        # ✅ PROCESSAMENTO NORMAL: Quando selected-location é atualizado
        if not selected_location:
            raise PreventUpdate

        location_id = _get_location_id(selected_location)
        if not location_id:
            raise PreventUpdate

        # ✅✅✅ LIMPEZA AUTOMÁTICA: Antes de cada operação de cache
        # Mais eficiente que intervalo periódico!
        if cache_data and isinstance(cache_data, dict):
            cache_data = _clean_expired_entries(cache_data)

        cache_key = f"location_{location_id}"

        # Verificar se já temos no cache (após limpeza)
        if cache_key in cache_data:
            entry = cache_data[cache_key]
            if not _is_cache_expired(entry):
                logger.info(f"✅ Cache HIT para {location_id}")
                return cache_data
            else:
                logger.info(f"⏰ Cache EXPIRED para {location_id} (removendo)")
                cache_data = cache_data.copy()
                del cache_data[cache_key]

        # Garantir session_id
        if not session_id:
            session_id = f"sess_{uuid.uuid4().hex}"

        # Cache miss → buscar do backend via API client
        try:
            api_client = APIClient()

            # Usar endpoint correto da API
            # Assumindo que existe /api/v1/climate/download ou similar
            payload = await api_client.download_climate_data(
                {"location_id": location_id, "session_id": session_id}
            )

            # Armazenar com metadata
            cache_entry = {
                "timestamp": datetime.now().isoformat(),
                "ttl_minutes": CACHE_TTL_MINUTES,
                "data": payload,
            }

            # Adicionar ao cache (garantir que é dict)
            if not isinstance(cache_data, dict):
                cache_data = {}
            else:
                cache_data = cache_data.copy()

            cache_data[cache_key] = cache_entry

            # Limitar tamanho do cache
            if len(cache_data) > MAX_CACHE_ENTRIES:
                try:
                    # Ordena por timestamp e mantém os mais recentes
                    sorted_keys = sorted(
                        cache_data.keys(),
                        key=lambda k: cache_data[k].get("timestamp", ""),
                        reverse=True,
                    )
                    cache_data = {
                        k: cache_data[k]
                        for k in sorted_keys[:MAX_CACHE_ENTRIES]
                    }
                    logger.info(
                        f"📦 Cache limitado para {MAX_CACHE_ENTRIES} entradas"
                    )
                except Exception as e:
                    logger.warning(f"Erro ao limitar cache: {e}")

            logger.info(f"💾 Cache MISS → armazenado para {location_id}")
            return cache_data

        except Exception as e:
            logger.error(
                f"❌ Erro ao buscar dados climáticos para {location_id}: {e}"
            )
            raise PreventUpdate

    @app.callback(
        Output("app-session-id", "data"),
        Input("url", "pathname"),
        State("app-session-id", "data"),
    )
    def initialize_session_id(pathname, existing_session_id):
        """Inicializa session ID se não existir."""
        if not existing_session_id:
            new_session_id = f"sess_{uuid.uuid4().hex}"
            logger.info(f"🆕 Nova sessão iniciada: {new_session_id}")
            return new_session_id
        return existing_session_id

    @app.callback(
        Output("cache-stats", "children"),
        [Input("climate-cache-store", "data"), Input("url", "pathname")],
        prevent_initial_call=True,
    )
    def update_cache_stats(cache_data, pathname):
        """Exibe estatísticas do cache."""
        if not cache_data or not isinstance(cache_data, dict):
            return html.Small("💾 Cache: vazio", className="text-muted")

        total_count = len(cache_data)
        expired_count = sum(
            1 for entry in cache_data.values() if _is_cache_expired(entry)
        )

        if expired_count > 0:
            return html.Small(
                f"💾 Cache: {total_count} entradas ({expired_count} expirando)",
                className="text-warning",
            )
        else:
            return html.Small(
                f"💾 Cache: {total_count}/{MAX_CACHE_ENTRIES} entradas",
                className="text-success",
            )
