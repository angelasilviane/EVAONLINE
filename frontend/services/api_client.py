"""
Cliente HTTP para integração com API backend.

Fornece métodos para chamar endpoints da API FastAPI
de forma assíncrona nos callbacks do Dash.
"""

import logging
from typing import Any, Dict, Optional

import httpx
from config.settings.app_config import get_legacy_settings

logger = logging.getLogger(__name__)


class APIClient:
    """
    Cliente HTTP para comunicação com backend FastAPI.

    Usado nos callbacks do Dash para integrar com:
    - ETo calculations
    - Cache management
    - Climate data
    - Favorites
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Inicializa cliente API.

        Args:
            base_url: URL base da API (padrão: localhost:8000/api/v1)
        """
        settings = get_legacy_settings()
        port = getattr(settings, "api", {}).get("PORT", 8000)
        self.base_url = (
            base_url or f"http://localhost:{port}{settings.API_V1_PREFIX}"
        )
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.client.aclose()

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Faz requisição GET para API.

        Args:
            endpoint: Endpoint relativo (ex: "/health")
            params: Parâmetros de query

        Returns:
            Dados da resposta JSON
        """
        try:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"🔍 GET {url}")

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            logger.error(f"❌ Erro GET {endpoint}: {e}")
            raise

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Faz requisição POST para API.

        Args:
            endpoint: Endpoint relativo (ex: "/eto/calculate")
            data: Dados JSON para enviar

        Returns:
            Dados da resposta JSON
        """
        try:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"📤 POST {url}")

            response = await self.client.post(url, json=data or {})
            response.raise_for_status()

            return response.json()
        except Exception as e:
            logger.error(f"❌ Erro POST {endpoint}: {e}")
            raise

    async def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Faz requisição PUT para API.

        Args:
            endpoint: Endpoint relativo
            data: Dados JSON para enviar

        Returns:
            Dados da resposta JSON
        """
        try:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"📝 PUT {url}")

            response = await self.client.put(url, json=data or {})
            response.raise_for_status()

            return response.json()
        except Exception as e:
            logger.error(f"❌ Erro PUT {endpoint}: {e}")
            raise

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Faz requisição DELETE para API.

        Args:
            endpoint: Endpoint relativo

        Returns:
            Dados da resposta JSON
        """
        try:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"🗑️ DELETE {url}")

            response = await self.client.delete(url)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            logger.error(f"❌ Erro DELETE {endpoint}: {e}")
            raise

    # ===========================================
    # MÉTODOS ESPECÍFICOS PARA ETO CALCULATOR
    # ===========================================

    async def calculate_eto(
        self, location_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcula ETo para localização específica.

        Args:
            location_data: Dados da localização (lat, lon, timezone, etc.)

        Returns:
            Resultado do cálculo ETo
        """
        return await self.post("/internal/eto/calculate", location_data)

    # ⚠️ REMOVIDO: get_eto_history() - Este endpoint não existe no backend
    # Se precisar implementar histórico de cálculos, adicionar no backend primeiro

    # ===========================================
    # MÉTODOS PARA CACHE E FAVORITOS
    # ===========================================

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Busca estatísticas do cache.

        Returns:
            Estatísticas de cache
        """
        return await self.get("/internal/cache/stats")

    async def clear_cache(self) -> Dict[str, Any]:
        """
        Limpa cache do servidor.

        Returns:
            Status da operação
        """
        return await self.post("/internal/cache/clear")

    async def get_favorites(self) -> Dict[str, Any]:
        """
        Busca lista de favoritos do usuário.

        Returns:
            Lista de favoritos
        """
        return await self.get("/internal/eto/favorites/list")

    async def add_favorite(
        self, favorite_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adiciona novo favorito.

        Args:
            favorite_data: Dados do favorito

        Returns:
            Favorito criado
        """
        return await self.post("/internal/eto/favorites/add", favorite_data)

    # ⚠️ REMOVIDO: update_favorite() não existe no backend

    async def delete_favorite(self, favorite_id: str) -> Dict[str, Any]:
        """
        Remove favorito.

        Args:
            favorite_id: ID do favorito

        Returns:
            Status da operação
        """
        fav_path = f"/internal/eto/favorites/remove/{favorite_id}"
        return await self.delete(fav_path)

    # ===========================================
    # MÉTODOS PARA DADOS CLIMÁTICOS
    # ===========================================

    async def get_climate_sources(self) -> Dict[str, Any]:
        """
        Busca fontes de dados climáticos disponíveis.

        Returns:
            Lista de fontes climáticas
        """
        return await self.get("/climate/sources")

    async def download_climate_data(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Baixa dados climáticos para localização.

        Args:
            request_data: Parâmetros de download (lat, lon, dates, etc.)

        Returns:
            Dados climáticos
        """
        return await self.post("/climate/download", request_data)

    async def validate_climate_data(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valida dados climáticos.

        Args:
            data: Dados a validar

        Returns:
            Resultado da validação
        """
        return await self.post("/climate/validate", data)

    # ===========================================
    # MÉTODOS PARA MONITORAMENTO
    # ===========================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica saúde da aplicação.

        Returns:
            Status de saúde
        """
        return await self.get("/health")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Busca estatísticas da aplicação.

        Returns:
            Estatísticas gerais
        """
        return await self.get("/stats")


# ===========================================
# INSTÂNCIA GLOBAL PARA USO NOS CALLBACKS
# ===========================================

# Removido: api_client = APIClient() - Criar instâncias locais nos callbacks

# ===========================================
# FUNÇÕES UTILITÁRIAS PARA CALLBACKS
# ===========================================


async def fetch_eto_calculation(
    location_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Função utilitária para calcular ETo nos callbacks.

    Args:
        location_data: Dados da localização

    Returns:
        Resultado do cálculo
    """
    async with APIClient() as client:
        return await client.calculate_eto(location_data)


async def fetch_climate_data(location_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função utilitária para buscar dados climáticos nos callbacks.

    Args:
        location_data: Dados da localização

    Returns:
        Dados climáticos
    """
    async with APIClient() as client:
        return await client.download_climate_data(location_data)


async def fetch_favorites() -> Dict[str, Any]:
    """
    Função utilitária para buscar favoritos nos callbacks.

    Returns:
        Lista de favoritos
    """
    async with APIClient() as client:
        return await client.get_favorites()


# ===========================================
# EXEMPLO DE USO NOS CALLBACKS
# ===========================================

"""
EXEMPLO: Como usar nos callbacks do Dash

from frontend.services.api_client import APIClient, fetch_eto_calculation

# Callback assíncrono
@app.callback(
    Output("eto-result", "children"),
    Input("calculate-btn", "n_clicks"),
    State("current-location", "data"),
    prevent_initial_call=True,
)
async def calculate_eto_callback(n_clicks, location_data):
    if not n_clicks or not location_data:
        return "Dados insuficientes"

    try:
        # Criar instância local do cliente API
        api_client = APIClient()

        # Chama API backend
        result = await fetch_eto_calculation(location_data)

        # Processa resultado
        eto_value = result.get("eto", 0)
        return f"ETo calculado: {eto_value} mm/dia"

    except Exception as e:
        logger.error(f"Erro no cálculo ETo: {e}")
        return "Erro no cálculo"
"""
