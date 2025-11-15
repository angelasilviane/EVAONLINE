"""
Factory para criar clientes climáticos com cache injetado (Redis).

Fornece método centralizado para instanciar clientes de APIs climáticas
com todas as dependências (cache Redis) corretamente injetadas.

Padrões de Uso:
- NASA POWER: Sempre usa cache injetado (dados históricos pesados)
- MET Norway: Sempre usa cache injetado (dados regionais complexos)
- Open-Meteo Archive/Forecast: Usa cache local em disco (arquivos grandes)
- NWS Forecast: Cache interno (dados oficiais governamentais)
- NWS Stations: Sempre usa cache injetado (observações tempo real)

Responsabilidades:
1. Gerenciar singleton do ClimateCacheService (Redis)
2. Injetar dependências automaticamente em clientes
3. Fornecer cleanup centralizado de conexões
4. Garantir consistência na criação de clientes
"""

from loguru import logger

from backend.infrastructure.cache.climate_cache import ClimateCacheService


class ClimateClientFactory:
    """
    Factory para criar clientes climáticos com dependências injetadas.

    Features:
    - Singleton do serviço de cache (reutiliza conexão Redis)
    - Injeção automática de cache em todos os clientes
    - Método centralizado de cleanup
    """

    _cache_service: ClimateCacheService | None = None

    @classmethod
    def get_cache_service(cls) -> ClimateCacheService:
        """
        Retorna instância singleton do serviço de cache.

        Garante que todos os clientes compartilhem a mesma
        conexão Redis, evitando overhead de múltiplas conexões.

        Returns:
            ClimateCacheService: Serviço de cache compartilhado
        """
        if cls._cache_service is None:
            cls._cache_service = ClimateCacheService(prefix="climate")
            logger.info("ClimateCacheService singleton criado")
        return cls._cache_service

    @classmethod
    def create_nasa_power(cls):
        """
        Cria cliente NASA POWER com cache injetado.

        Quando usar:
        - Dados históricos globais (1990-presente)
        - Períodos longos (> 30 dias)
        - Alta confiabilidade e cobertura global
        - Cache Redis recomendado devido ao volume de dados

        Returns:
            NASAPowerClient: Cliente configurado com cache Redis
        """
        from .nasa_power.nasa_power_client import NASAPowerClient

        cache = cls.get_cache_service()
        client = NASAPowerClient(cache=cache)
        logger.debug("NASAPowerClient criado com cache injetado")
        return client

    @classmethod
    def create_met_norway(cls):
        """
        Cria cliente MET Norway com cache injetado.

        Quando usar:
        - Região Nórdica: Resolução 1km, radar, precipitação alta qualidade
        - Global: Temperatura e umidade apenas (9km ECMWF)
        - Previsões até 5 dias
        - Cache Redis recomendado para dados regionais complexos

        Returns:
            METNorwayClient: Cliente configurado com cache Redis
        """
        from .met_norway.met_norway_client import METNorwayClient

        cache = cls.get_cache_service()
        client = METNorwayClient(cache=cache)
        logger.debug("🇳🇴 METNorwayClient criado com cache injetado")
        return client

    @classmethod
    def create_nws(cls):
        """
        Cria cliente NWS (National Weather Service).

        Quando usar:
        - Apenas coordenadas nos EUA Continental
        - Previsões oficiais NOAA até 5 dias
        - Observações tempo real de estações
        - Cache interno (não precisa Redis)

        Nota: NWS usa cache interno próprio, não precisa injeção.

        Returns:
            NWSForecastClient: Cliente com cache interno
        """
        from .nws_forecast.nws_forecast_client import NWSForecastClient

        client = NWSForecastClient()
        logger.debug("🇺🇸 NWSForecastClient criado")
        return client

    @classmethod
    def create_nws_stations(cls):
        """
        Cria cliente NWS Stations com cache injetado.

        Quando usar:
        - Observações tempo real de estações meteorológicas
        - Apenas coordenadas nos EUA Continental
        - Dados atuais (últimas 24h)
        - Cache Redis recomendado para dados tempo real

        Returns:
            NWSStationsClient: Cliente configurado com cache Redis
        """
        from .nws_stations.nws_stations_client import NWSStationsClient

        cache = cls.get_cache_service()
        client = NWSStationsClient(cache=cache)
        logger.debug("🇺🇸 NWSStationsClient criado com cache injetado")
        return client

    @classmethod
    def create_openmeteo(cls):
        """
        Cria cliente Open-Meteo Forecast (padrão para compatibilidade).

        Quando usar:
        - Dados globais recentes + previsão (hoje-30d até hoje+5d)
        - Boa qualidade geral, cobertura mundial
        - Cache local em disco recomendado

        Returns:
            OpenMeteoForecastClient: Cliente com cache local
        """
        return cls.create_openmeteo_forecast()

    @classmethod
    def create_openmeteo_archive(
        cls,
        cache_dir: str = ".cache",
    ):
        """
        Cria cliente Open-Meteo Archive.

        Quando usar:
        - Dados históricos globais (1990-presente)
        - Períodos específicos no passado
        - Cache local em disco recomendado para arquivos grandes

        Args:
            cache_dir: Diretório para cache local

        Returns:
            OpenMeteoArchiveClient: Cliente com cache local
        """
        from .openmeteo_archive.openmeteo_archive_client import (
            OpenMeteoArchiveClient,
        )

        client = OpenMeteoArchiveClient(cache_dir=cache_dir)
        logger.debug("OpenMeteoArchiveClient criado (1940-2025)")
        return client

    @classmethod
    def create_openmeteo_forecast(
        cls,
        cache_dir: str = ".cache",
    ):
        """
        Cria cliente Open-Meteo Forecast.

        Quando usar:
        - Dados recentes + previsão global (hoje-30d até hoje+5d)
        - Melhor opção para cobertura mundial
        - Cache local em disco recomendado

        Args:
            cache_dir: Diretório para cache local

        Returns:
            OpenMeteoForecastClient: Cliente com cache local
        """
        from .openmeteo_forecast.openmeteo_forecast_client import (
            OpenMeteoForecastClient,
        )

        client = OpenMeteoForecastClient(cache_dir=cache_dir)
        logger.debug("OpenMeteoForecastClient criado (-30d a +5d)")
        return client

    @classmethod
    async def close_all(cls):
        """
        Fecha todas as conexões abertas (Redis, HTTP clients).
        """
        # Fechar Redis
        if cls._cache_service and cls._cache_service.redis:
            await cls._cache_service.redis.close()
            logger.info("ClimateCacheService Redis connection closed")
            cls._cache_service = None

        # CORREÇÃO: Adicionar cleanup de HTTP clients
        # Nota: HTTP clients são criados por request, não mantidos globalmente
        # Se necessário, implementar cleanup específico nos clients individuais
        logger.info("ClimateClientFactory cleanup completed")

    @classmethod
    def close_all_sync(cls):
        """Versão síncrona para contexts não-async."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Já está rodando, criar task
                asyncio.create_task(cls.close_all())
            else:
                # Rodar diretamente
                loop.run_until_complete(cls.close_all())
        except RuntimeError:
            # Novo loop se necessário
            asyncio.run(cls.close_all())
