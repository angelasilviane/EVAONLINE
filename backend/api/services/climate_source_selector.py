"""
Intelligent climate source selector based on geographic coordinates.

Uses bounding boxes to automatically decide the best climate API
for each location, prioritizing high-quality regional sources.

Available APIs:
    - NWS (Regional - USA only):
        Forecast + Stations real-time

    - Open-Meteo Forecast (Global - Worldwide):
        Global standard, real-time (-30d to +5d)

    - Open-Meteo Archive (Global - Worldwide):
        Historical data (1940-present)

    - MET Norway (Global* - Worldwide):
        Global coverage, optimized for Europe

    - NASA POWER (Global - Worldwide):
        Universal fallback (2-7 day delay)
"""

from typing import Literal

from loguru import logger

from backend.api.services.climate_factory import ClimateClientFactory
from backend.api.services.geographic_utils import GeographicUtils

# Type hints for climate sources
ClimateSource = Literal[
    "nasa_power",
    "met_norway",
    "nws_forecast",
    "nws_stations",
    "openmeteo_archive",
    "openmeteo_forecast",
]


class ClimateSourceSelector:
    """
    Seletor inteligente de fonte climática.

    Determina automaticamente a melhor API para buscar dados climáticos
    baseado nas coordenadas geográficas fornecidas.

    IMPORTANTE: Utiliza GeographicUtils para detecção de região
    (SINGLE SOURCE OF TRUTH para bbox USA, Nordic, etc)

    Estratégia MET Norway:
        - Região Nórdica: Temperatura, Umidade, Precipitação
          (1km, radar + crowdsourced, atualizações horárias)
        - Resto do Mundo: Apenas Temperatura e Umidade
          (9km ECMWF, precipitação de menor qualidade - usar Open-Meteo)

    Prioridades:
        1. NWS (USA): Tempo real, alta qualidade regional
        2. MET Norway (Nordic): Melhor precipitação do mundo
        3. Open-Meteo Forecast: Tempo real, alta qualidade global
        4. NASA POWER: Fallback com delay 2-7 dias
    """

    @classmethod
    def select_source(cls, lat: float, lon: float) -> ClimateSource:
        """
        Seleciona melhor fonte climática para coordenadas.

        Algoritmo de seleção:
        1. Verifica se está no USA → NWS
        2. Verifica se está na região Nórdica → MET Norway (alta qualidade)
        3. Fallback → Open-Meteo Forecast (cobertura global, tempo real)

        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)

        Returns:
            Nome da fonte recomendada

        Exemplo:
            # Nova York, USA
            source = ClimateSourceSelector.select_source(40.7128, -74.0060)
            # → "nws_forecast"

            # Oslo, Noruega (região nórdica)
            source = ClimateSourceSelector.select_source(59.9139, 10.7522)
            # → "met_norway"

            # Paris, França
            source = ClimateSourceSelector.select_source(48.8566, 2.3522)
            # → "openmeteo_forecast"

            # Brasília, Brasil
            source = ClimateSourceSelector.select_source(-15.7939, -47.8828)
            # → "openmeteo_forecast"
        """
        # Prioridade 1: USA (NWS Forecast)
        if GeographicUtils.is_in_usa(lat, lon):
            logger.debug(
                f"📍 Coordenadas ({lat}, {lon}) no USA → NWS Forecast"
            )
            return "nws_forecast"

        # Prioridade 2: Região Nórdica (MET Norway alta qualidade)
        if GeographicUtils.is_in_nordic(lat, lon):
            logger.debug(
                f"📍 Coordenadas ({lat}, {lon}) na região NÓRDICA → "
                f"MET Norway (1km, radar, precipitação alta qualidade)"
            )
            return "met_norway"

        # Fallback: Global (Open-Meteo Forecast - tempo real, alta qualidade)
        logger.debug(f"📍 Coordenadas ({lat}, {lon}) → Open-Meteo Forecast")
        return "openmeteo_forecast"

    @classmethod
    def get_client(cls, lat: float, lon: float):
        """
        Retorna cliente apropriado para coordenadas.

        Combina select_source() com ClimateClientFactory para
        retornar cliente já configurado e pronto para uso.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Cliente climático configurado

        Exemplo:
            # Obter cliente automático para Paris
            client = ClimateSourceSelector.get_client(
                lat=48.8566, lon=2.3522
            )
            # → METNorwayClient com cache injetado

            data = await client.get_forecast_data(...)
            await client.close()
        """
        source = cls.select_source(lat, lon)

        if source == "met_norway":
            return ClimateClientFactory.create_met_norway()
        elif source == "nws_forecast" or source == "nws_stations":
            return ClimateClientFactory.create_nws()
        elif source == "openmeteo_archive":
            return ClimateClientFactory.create_openmeteo_archive()
        elif source == "openmeteo_forecast":
            return ClimateClientFactory.create_openmeteo_forecast()
        else:  # nasa_power
            return ClimateClientFactory.create_nasa_power()

    @classmethod
    def get_all_sources(cls, lat: float, lon: float) -> list[ClimateSource]:
        """
        Retorna TODAS as fontes disponíveis para coordenadas.

        Útil para fusão multi-fonte ou validação cruzada.

        Lógica:
        - NASA POWER sempre disponível (cobertura global)
        - MET Norway Locationforecast se na região nórdica (prioridade)
          ou global (temperatura/umidade apenas)
        - NWS Forecast/Stations se no USA
        - Open-Meteo Archive/Forecast sempre disponível

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Lista de fontes aplicáveis, ordenadas por prioridade

        Exemplo:
            # Oslo (Região Nórdica)
            sources = ClimateSourceSelector.get_all_sources(59.9139, 10.7522)
            # → ["met_norway", "openmeteo_forecast",
            #    "nasa_power", ...]

            # Brasília (apenas global)
            sources = ClimateSourceSelector.get_all_sources(-15.7939, -47.8828)
            # → ["openmeteo_forecast", "met_norway",
            #    "nasa_power", "openmeteo_archive"]
        """
        sources = []

        # Fontes regionais (alta prioridade)
        if GeographicUtils.is_in_usa(lat, lon):
            sources.append("nws_forecast")
            sources.append("nws_stations")

        # MET Norway tem prioridade na região nórdica
        if GeographicUtils.is_in_nordic(lat, lon):
            sources.append("met_norway")
            sources.append("openmeteo_forecast")
        else:
            # Fora da região nórdica: Open-Meteo tem prioridade
            sources.append("openmeteo_forecast")
            sources.append("met_norway")

        # Fontes globais adicionais
        sources.extend(["openmeteo_archive", "nasa_power"])

        logger.debug(f"📍 Fontes disponíveis para ({lat}, {lon}): {sources}")

        return sources

    @classmethod
    def get_data_availability_summary(cls) -> dict[str, dict]:
        """
        Retorna resumo da disponibilidade de dados de todas as fontes (6 APIs).

        Returns:
            dict: Informações de disponibilidade por fonte
        """
        # Implementação estática sem imports circulares
        summary = {
            "openmeteo_archive": {
                "coverage": "global",
                "period": "1940-01-01 to today-2d",
                "license": "CC-BY-4.0",
                "description": "Historical weather data (1940-present)",
            },
            "openmeteo_forecast": {
                "coverage": "global",
                "period": "today-30d to today+5d",
                "license": "CC-BY-4.0",
                "description": "Forecast weather data (up to 16 days)",
            },
            "nasa_power": {
                "coverage": "global",
                "period": "1981-01-01 to today-2-7d",
                "license": "Public Domain",
                "description": "NASA POWER meteorological data",
            },
            "nws_forecast": {
                "coverage": "usa",
                "period": "today to today+5d",
                "license": "Public Domain",
                "description": "NOAA NWS forecast data (USA only)",
            },
            "nws_stations": {
                "coverage": "usa",
                "period": "today-1d to now",
                "license": "Public Domain",
                "description": "NOAA NWS station observations (USA only)",
            },
            "met_norway": {
                "coverage": "global",
                "period": "today to today+5d",
                "license": "CC-BY-4.0",
                "description": "MET Norway Locationforecast (global coverage)",
            },
        }

        return summary

    @classmethod
    def get_coverage_info(cls, lat: float, lon: float) -> dict:
        """
        Retorna informações detalhadas sobre cobertura para coordenadas.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict com informações de cobertura

        Exemplo:
            info = ClimateSourceSelector.get_coverage_info(48.8566, 2.3522)
            # {
            #     'location': {'lat': 48.8566, 'lon': 2.3522},
            #     'recommended_source': 'met_norway',
            #     'all_sources': ['met_norway', 'nasa_power'],
            #     'regional_coverage': {
            #         'europe': True,
            #         'usa': False
            #     },
            #     'source_details': {...}
            # }
        """
        recommended = cls.select_source(lat, lon)
        all_sources = cls.get_all_sources(lat, lon)

        return {
            "location": {"lat": lat, "lon": lon},
            "recommended_source": recommended,
            "all_sources": all_sources,
            "regional_coverage": {
                "usa": GeographicUtils.is_in_usa(lat, lon),
                "nordic": GeographicUtils.is_in_nordic(lat, lon),
            },
            "source_details": {
                "nws_forecast": {
                    "bbox": GeographicUtils.USA_BBOX,
                    "description": "USA: -125°W a -66°W, 24°N a 49°N",
                    "quality": "high",
                    "realtime": True,
                },
                "nws_stations": {
                    "bbox": GeographicUtils.USA_BBOX,
                    "description": "USA stations: -125°W a -66°W, 24°N a 49°N",
                    "quality": "high",
                    "realtime": True,
                },
                "met_norway": {
                    "bbox": None,
                    "nordic_bbox": GeographicUtils.NORDIC_BBOX,
                    "description": (
                        "Global coverage. Nordic region "
                        "(NO/SE/FI/DK/Baltics): "
                        "1km resolution, hourly updates, radar-corrected "
                        "precipitation. Rest of world: 9km ECMWF, "
                        "temperature/humidity only"
                    ),
                    "quality": {
                        "nordic": ("very high (1km + radar + crowdsourced)"),
                        "global": ("medium (9km ECMWF, skip precipitation)"),
                    },
                    "realtime": True,
                },
                "openmeteo_archive": {
                    "bbox": None,
                    "description": "Global historical data",
                    "quality": "high",
                    "realtime": False,
                },
                "openmeteo_forecast": {
                    "bbox": None,
                    "description": "Global forecast data",
                    "quality": "high",
                    "realtime": True,
                },
                "nasa_power": {
                    "bbox": None,
                    "description": "Global coverage",
                    "quality": "medium",
                    "realtime": False,
                    "delay_days": "2-7",
                },
            },
        }


def get_available_sources_for_frontend(lat: float, lon: float) -> dict:
    """
    Retorna fontes disponíveis formatadas para o frontend.

    Usado pela interface dash_eto.py para popular dropdown de fontes.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Dict com informações formatadas:
        {
            "recommended": "openmeteo_forecast",
            "sources": [
                {
                    "value": "fusion",
                    "label": "🔀 Fusão Inteligente (Recomendado)",
                    "description": "Combina múltiplas fontes para melhor qualidade" # noqa: E501
                },
                {
                    "value": "openmeteo_forecast",
                    "label": "Open-Meteo Forecast",
                    "description": "Dados globais em tempo real",
                    "icon": "🌍"
                },
                ...
            ],
            "location_info": {
                "in_usa": False,
                "in_nordic": False,
                "region": "Global"
            }
        }
    """
    # Detecta região
    in_usa = GeographicUtils.is_in_usa(lat, lon)
    in_nordic = GeographicUtils.is_in_nordic(lat, lon)

    region = (
        "USA Continental"
        if in_usa
        else ("Região Nórdica" if in_nordic else "Global")
    )

    # Obtém fonte recomendada e todas disponíveis
    recommended = ClimateSourceSelector.select_source(lat, lon)
    all_sources = ClimateSourceSelector.get_all_sources(lat, lon)

    # Mapeamento de ícones e descrições
    source_metadata = {
        "openmeteo_archive": {
            "icon": "📚",
            "label": "Open-Meteo Archive",
            "description": "Dados históricos globais (1990-hoje)",
        },
        "openmeteo_forecast": {
            "icon": "🌍",
            "label": "Open-Meteo Forecast",
            "description": "Dados recentes + previsão global",
        },
        "nasa_power": {
            "icon": "🛰️",
            "label": "NASA POWER",
            "description": "Dados históricos globais (1990-hoje)",
        },
        "met_norway": {
            "icon": "🇳🇴" if in_nordic else "🌐",
            "label": "MET Norway" + (" (Alta Qualidade)" if in_nordic else ""),
            "description": "Previsão meteorológica"
            + (" - Resolução 1km" if in_nordic else " - Global"),
        },
        "nws_forecast": {
            "icon": "🇺🇸",
            "label": "NWS Forecast",
            "description": "Previsão oficial NOAA (USA)",
        },
        "nws_stations": {
            "icon": "📡",
            "label": "NWS Stations",
            "description": "Observações em tempo real (USA)",
        },
    }

    # Monta lista de fontes formatadas
    sources_list = [
        {
            "value": "fusion",
            "label": "🔀 Fusão Inteligente (Recomendado)",
            "description": f"Combina {len(all_sources)} fontes para melhor qualidade e cobertura",  # noqa: E501
            "is_default": True,
        }
    ]

    # Adiciona fontes individuais
    for source in all_sources:
        if source in source_metadata:
            meta = source_metadata[source]
            sources_list.append(
                {
                    "value": source,
                    "label": f"{meta['icon']} {meta['label']}",
                    "description": meta["description"],
                    "is_recommended": source == recommended,
                }
            )

    return {
        "recommended": recommended,
        "sources": sources_list,
        "location_info": {
            "in_usa": in_usa,
            "in_nordic": in_nordic,
            "region": region,
        },
        "total_sources": len(all_sources),
    }
