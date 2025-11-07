"""
Gerenciador de fontes de dados climáticos.

Detecta quais fontes estão disponíveis para uma determinada localização
e gerencia a fusão de dados de múltiplas fontes.
"""

from datetime import datetime
from typing import Any

from loguru import logger


class ClimateSourceManager:
    """Gerencia disponibilidade e seleção de fontes climáticas.

    Estratégia de Resolução Temporal:
    ------------------------------------
    Todas as fontes: DIÁRIA
        * Uso para mapa mundial dash (qualquer ponto)
        * Dados diários para período de 7-30 dias
        * Sob demanda (clique do usuário)
        * Fusão de múltiplas fontes disponível

    Fontes Configuradas (6 fontes):
    -------------------------------
    Global:
    - Open-Meteo Archive: Histórico (1940 → Today-2d), CC-BY-4.0
    - Open-Meteo Forecast: Previsão (Today-30d → Today+5d), CC-BY-4.0
    - NASA POWER: Histórico (1981 → Today-2-7d), Public Domain
    - Met Norway LocationForecast: Previsão global (Today → Today+5d), CC-BY-4.0

    🇺🇸 USA Continental:
    - NWS Forecast: Previsão (Today → Today+5d), Public Domain
    - NWS Stations: Observações (Today-1d → Now), Public Domain
    """

    # Configuração de fontes de dados disponíveis
    SOURCES_CONFIG: dict[str, dict[str, Any]] = {
        "openmeteo_archive": {
            "id": "openmeteo_archive",
            "name": "Open-Meteo Archive",
            "coverage": "global",
            "temporal": "daily",
            "bbox": None,
            "license": "CC-BY-4.0",
            "realtime": False,
            "priority": 1,
            "url": "https://archive-api.open-meteo.com/v1/archive",
            "variables": [
                "temperature_2m_max",
                "temperature_2m_mean",
                "temperature_2m_min",
                "relative_humidity_2m_max",
                "relative_humidity_2m_mean",
                "relative_humidity_2m_min",
                "wind_speed_10m_mean",
                "shortwave_radiation_sum",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
            ],
            "delay_hours": 48,
            "update_frequency": "daily",
            "historical_start": "1940-01-01",
            # Weather data by Open-Meteo.com
            "restrictions": {"attribution_required": True},
            "use_case": "Global historical ETo validation",
        },
        "openmeteo_forecast": {
            "id": "openmeteo_forecast",
            "name": "Open-Meteo Forecast",
            "coverage": "global",
            "temporal": "daily",
            "bbox": None,  # Global coverage
            "license": "CC-BY-4.0",  # Creative Commons Attribution 4.0
            "realtime": True,
            "priority": 1,
            "url": "https://api.open-meteo.com/v1/forecast",
            "variables": [
                "temperature_2m_max",
                "temperature_2m_mean",
                "temperature_2m_min",
                "relative_humidity_2m_max",
                "relative_humidity_2m_mean",
                "relative_humidity_2m_min",
                "wind_speed_10m_mean",
                "shortwave_radiation_sum",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
            ],
            "delay_hours": 1,
            "update_frequency": "daily",
            "historical_start": None,  # Only forecasts
            "forecast_horizon_days": 5,  # Padronizado para 5 dias
            "restrictions": {
                "attribution_required": True
            },  # Weather data by Open-Meteo.com
            "use_case": "Global forecast ETo calculations",
        },
        "nasa_power": {
            "id": "nasa_power",
            "name": "NASA POWER",
            "coverage": "global",
            "temporal": "daily",
            "bbox": None,  # Global coverage
            "license": "public_domain",  # Domínio Público
            "realtime": False,  # Atraso 2-3 dias (T, RH, precip, vento)
            # Atraso 5-7 dias (radiação solar)
            "priority": 2,
            "url": "https://power.larc.nasa.gov/api/temporal/daily/point",
            "variables": [
                "T2M_MAX",
                "T2M_MIN",
                "T2M",
                "RH2M",
                "WS2M",
                "ALLSKY_SFC_SW_DWN",
                "PRECTOTCORR",
            ],
            "delay_hours": 72,  # 2-3 dias de atraso
            "update_frequency": "daily",
            "historical_start": "1981-01-01",
            "restrictions": {"limit_requests": 1000},  # 1000 req/dia
            "use_case": "Global daily ETo, data fusion",
        },
        "nws_forecast": {
            "id": "nws_forecast",
            "name": "NWS Forecast",
            "coverage": "usa",
            "temporal": "hourly",
            "bbox": (-125.0, 24.0, -66.0, 49.0),  # (W,S,E,N) USA Continental
            "license": "public_domain",  # Domínio Público (US Government)
            "realtime": True,
            "priority": 3,
            "url": "https://api.weather.gov/",
            "variables": [
                "temperature",
                "relativeHumidity",
                "windSpeed",
                "windDirection",
                "skyCover",
                "quantitativePrecipitation",
            ],
            "delay_hours": 1,
            "update_frequency": "hourly",
            "forecast_horizon_days": 5,  # Padronizado para 5 dias (forecast)
            "restrictions": {
                "attribution_required": True,  # Citar NOAA
                "user_agent_required": True,  # User-Agent obrigatório
            },
            "use_case": "USA hourly ETo forecasts",
        },
        "nws_stations": {
            "id": "nws_stations",
            "name": "NWS Stations",
            "coverage": "usa",
            "temporal": "hourly",
            "bbox": (-125.0, 24.0, -66.0, 49.0),  # (W,S,E,N) USA Continental
            "license": "public_domain",  # Domínio Público (US Government)
            "realtime": True,
            "priority": 3,
            "url": "https://api.weather.gov/",
            "variables": [
                "temperature",
                "relativeHumidity",
                "windSpeed",
                "windDirection",
                "skyCover",
                "quantitativePrecipitation",
            ],
            "delay_hours": 1,
            "update_frequency": "hourly",
            "historical_start": None,  # Recent observations only
            "restrictions": {
                "attribution_required": True,  # Citar NOAA
                "user_agent_required": True,  # User-Agent obrigatório
                "data_window_days": 30,  # Últimos 30 dias
            },
            "use_case": "USA station observations",
        },
        "met_norway": {
            "id": "met_norway",
            "name": "MET Norway Locationforecast",
            "coverage": "global",
            "temporal": "daily",
            "bbox": None,  # Global coverage via Locationforecast 2.0
            "license": "NLOD-2.0+CC-BY-4.0",  # Norwegian + Creative Commons
            "realtime": True,
            "priority": 4,
            "url": (
                "https://api.met.no/weatherapi/locationforecast/2.0/compact"
            ),
            "variables": [
                # Variáveis disponíveis variam por região:
                # Nordic (4°E-31°E, 54°N-71.5°N): Todas as 5 variáveis abaixo
                #   - 1km MET Nordic, radar + Netatmo crowdsourced
                # Global: Apenas temperatura e umidade (4 variáveis)
                #   - 9km ECMWF, precipitação de menor qualidade
                #     (usar Open-Meteo)
                # Nota: Nomes refletem schema de saída padronizado,
                #       mas vêm de variáveis da API MET Norway:
                #       air_temperature_max/min, air_temperature,
                #       relative_humidity, precipitation_amount
                "air_temperature_max",
                "air_temperature_min",
                "air_temperature_mean",
                "relative_humidity_mean",
                "precipitation_sum",  # Apenas Nordic region
            ],
            "delay_hours": 1,
            "update_frequency": "daily",
            "forecast_horizon_days": 5,  # Padronizado para 5 dias (forecast)
            "restrictions": {
                "attribution_required": True,  # "Weather data from MET Norway"
                "user_agent_required": True,  # User-Agent obrigatório
                "limit_requests": "20 req/s",  # Rate limit
            },
            "use_case": (
                "Regional quality strategy: Nordic (NO/SE/FI/DK) = "
                "high-quality precipitation (1km + radar). "
                "Global = temperature/humidity only (skip precipitation, use Open-Meteo)"
            ),
            "regional_strategy": {
                "nordic": {
                    "bbox": (4.0, 54.0, 31.0, 71.5),  # (W, S, E, N)
                    "resolution": "1km (MET Nordic)",
                    "model": "MEPS 2.5km + downscaling",
                    "updates": "Hourly",
                    "post_processing": "Radar + Netatmo crowdsourced bias correction",
                    "variables": [
                        "air_temperature_max",
                        "air_temperature_min",
                        "air_temperature_mean",
                        "relative_humidity_mean",
                        "precipitation_sum",
                    ],
                    "precipitation_quality": "✅ HIGH (use MET Norway)",
                },
                "global": {
                    "resolution": "9km (ECMWF IFS)",
                    "model": "ECMWF IFS HRES",
                    "updates": "4x daily (00/06/12/18 UTC)",
                    "post_processing": "Minimal",
                    "variables": [
                        "air_temperature_max",
                        "air_temperature_min",
                        "air_temperature_mean",
                        "relative_humidity_mean",
                    ],
                    "precipitation_quality": "⚠️ LOW (use Open-Meteo multi-model instead)",
                },
            },
        },
    }

    # Validação de datasets (offline, apenas documentação)
    VALIDATION_DATASETS = {
        "xavier_brazil": {
            "name": "Xavier et al. Daily Weather Gridded Data",
            "period": "1961-01-01 to 2024-03-20",
            "resolution": "0.25° x 0.25°",
            "coverage": "brazil",
            "cities": [
                # Cidades de validação (Brasil)
                {
                    "name": "Balsas",
                    "uf": "MA",
                    "lat": -7.5312,
                    "long": -46.0390,
                },
                {
                    "name": "Imperatriz",
                    "uf": "MA",
                    "lat": -5.5265,
                    "long": -47.4798,
                },
                {
                    "name": "Barra do Corda",
                    "uf": "MA",
                    "lat": -5.5083,
                    "long": -45.2390,
                },
                {
                    "name": "Carolina",
                    "uf": "MA",
                    "lat": -7.3308,
                    "long": -47.4701,
                },
                {
                    "name": "Bom Jesus",
                    "uf": "PI",
                    "lat": -9.0709,
                    "long": -44.3605,
                },
                {
                    "name": "Corrente",
                    "uf": "PI",
                    "lat": -10.4409,
                    "long": -45.1633,
                },
                {
                    "name": "Gilbués",
                    "uf": "PI",
                    "lat": -9.8346,
                    "long": -45.3469,
                },
                {
                    "name": "Uruçuí",
                    "uf": "PI",
                    "lat": -7.2435,
                    "long": -44.5435,
                },
                {
                    "name": "Barreiras",
                    "uf": "BA",
                    "lat": -12.1449,
                    "long": -45.0042,
                },
                {
                    "name": "Luís Eduardo Magalhães",
                    "uf": "BA",
                    "lat": -12.0784,
                    "long": -45.8005,
                },
                {
                    "name": "Formosa do Rio Preto",
                    "uf": "BA",
                    "lat": -11.0470,
                    "long": -45.1910,
                },
                {
                    "name": "Correntina",
                    "uf": "BA",
                    "lat": -13.3418,
                    "long": -44.6411,
                },
                {
                    "name": "Araguaína",
                    "uf": "TO",
                    "lat": -7.1913,
                    "long": -48.2087,
                },
                {
                    "name": "Gurupi",
                    "uf": "TO",
                    "lat": -11.7298,
                    "long": -49.0715,
                },
                {
                    "name": "Palmas",
                    "uf": "TO",
                    "lat": -10.1840,
                    "long": -48.3336,
                },
                {
                    "name": "Porto Nacional",
                    "uf": "TO",
                    "lat": -10.7084,
                    "long": -48.4176,
                },
                # Piracicaba, SP (controle)
                {
                    "name": "Piracicaba",
                    "uf": "SP",
                    "lat": -22.7249,
                    "long": -47.6486,
                },
            ],
            "reference": "https://doi.org/10.1002/joc.5325",
            "validation_metric": "ETo_FAO56",
        },
        "openmeteo_global": {
            "name": "Open-Meteo ETo (FAO-56 Penman-Monteith)",
            "period": "1940-01-01 to present (forecast)",
            "resolution": "Variable (depends on model)",
            "coverage": "global",
            "license": "CC-BY-4.0",  # Creative Commons Attribution 4.0
            "delay": "~1-2 days (forecast), ~2 days (archive)",
            "use_case": "Global ETo validation and comparison",
            "reference": "https://open-meteo.com/en/docs",
            "validation_metric": "et0_fao_evapotranspiration",
            "note": (
                "Open-Meteo provides pre-calculated ETo using FAO-56 "
                "Penman-Monteith method. Perfect for validating our "
                "application's ETo calculations against a reliable "
                "reference. Available through both Archive API "
                "(historical) and Forecast API (recent/current)."
            ),
            "api_endpoints": {
                "archive": "https://archive-api.open-meteo.com/v1/archive",
                "forecast": "https://api.open-meteo.com/v1/forecast",
            },
            "variable": "et0_fao_evapotranspiration",
        },
    }

    def __init__(self) -> None:
        """Inicializa o gerenciador de fontes."""
        self.enabled_sources: dict[str, dict[str, Any]] = dict(
            self.SOURCES_CONFIG.items()
        )
        logger.info(
            "ClimateSourceManager initialized with %d sources",
            len(self.enabled_sources),
        )

    def get_available_sources(self, lat: float, long: float) -> list[dict]:
        """
        Retorna fontes disponíveis para uma coordenada específica.

        Args:
            lat: Latitude (-90 a 90)
            long: Longitude (-180 a 180)

        Returns:
            List[Dict]: Lista de fontes disponíveis com metadados
        """
        available = []

        for source_id, metadata in self.enabled_sources.items():
            if self._is_point_covered(lat, long, metadata):
                available.append(
                    {
                        "id": source_id,
                        "name": metadata["name"],
                        "coverage": metadata["coverage"],
                        "temporal": metadata["temporal"],
                        "realtime": metadata["realtime"],
                        "priority": metadata["priority"],
                        "delay_hours": metadata.get("delay_hours", 0),
                        "variables": metadata.get("variables", []),
                    }
                )

        # Ordena por prioridade
        available.sort(key=lambda x: x["priority"])

        logger.info(
            "Found %d sources for lat=%s, long=%s: %s",
            len(available),
            lat,
            long,
            [s["id"] for s in available],
        )

        return available

    def get_available_sources_for_location(
        self, lat: float, lon: float, exclude_non_commercial: bool = True
    ) -> dict[str, dict]:
        """
        Retorna fontes disponíveis para uma localização específica.

        Este método é otimizado para uso no mapa mundial, excluindo
        automaticamente fontes com restrições de licença não-comercial
        quando solicitado (parâmetro exclude_non_commercial).
        """
        result = {}

        for source_id, metadata in self.enabled_sources.items():
            # Filtrar fontes não-comerciais se solicitado
            license_type = metadata.get("license", "")
            is_non_commercial = license_type == "non_commercial"

            if exclude_non_commercial and is_non_commercial:
                logger.debug(
                    "Excluding %s (non-commercial license) from world map",
                    source_id,
                )
                continue

            # Verificar cobertura geográfica
            bbox = metadata.get("bbox")
            is_covered = self._is_point_covered(lat, lon, metadata)

            # Verificar restrições de fusão e download
            restrictions = metadata.get("restrictions", {})
            can_fuse = not restrictions.get("no_data_fusion", False)
            can_download = not restrictions.get("no_download", False)

            result[source_id] = {
                "available": is_covered,
                "name": metadata["name"],
                "coverage": metadata["coverage"],
                "bbox": bbox,
                "bbox_str": self._format_bbox(bbox),
                "license": license_type,
                "priority": metadata["priority"],
                "can_fuse": can_fuse,
                "can_download": can_download,
                "realtime": metadata.get("realtime", False),
                "temporal": metadata.get("temporal", "daily"),
                "variables": metadata.get("variables", []),
                "attribution_required": restrictions.get(
                    "attribution_required", False
                ),
            }

        # Log das fontes disponíveis
        available_ids = [
            sid for sid, meta in result.items() if meta["available"]
        ]
        logger.info(
            "Sources for lat=%.4f, lon=%.4f: %d available (%s)",
            lat,
            lon,
            len(available_ids),
            ", ".join(available_ids) if available_ids else "none",
        )

        return result

    def _format_bbox(self, bbox: tuple | None) -> str:
        """
        Formata bbox para exibição legível.

        Args:
            bbox: Tupla (west, south, east, north) ou None

        Returns:
            str: Bbox formatado (ex: "Europe: 35°N-72°N, 25°W-45°E")
        """
        if bbox is None:
            return "Global coverage"

        west, south, east, north = bbox

        # Formatar coordenadas
        def format_coord(value: float, is_latitude: bool) -> str:
            """Formata coordenada com direção cardinal."""
            direction = ""
            if is_latitude:
                direction = "N" if value >= 0 else "S"
            else:
                direction = "E" if value >= 0 else "W"
            return f"{abs(value):.0f}°{direction}"

        lat_range = f"{format_coord(south, True)}-{format_coord(north, True)}"
        lon_range = f"{format_coord(west, False)}-{format_coord(east, False)}"

        return f"{lat_range}, {lon_range}"

    def _is_point_covered(
        self, lat: float, long: float, metadata: dict[str, Any]
    ) -> bool:
        """
        Verifica se um ponto está coberto pela fonte.

        Args:
            lat: Latitude
            long: Longitude
            metadata: Metadados da fonte

        Returns:
            bool: True se ponto está coberto
        """
        bbox = metadata.get("bbox")

        # Cobertura global
        if bbox is None:
            return True

        # Cobertura regional (bbox format: west, south, east, north)
        west: float
        south: float
        east: float
        north: float
        west, south, east, north = bbox
        return bool(west <= long <= east and south <= lat <= north)

    def validate_period(
        self, start_date: datetime, end_date: datetime
    ) -> tuple[bool, str | None]:
        """
        Valida período de datas conforme especificações.

        Regras:
        - Mínimo: 7 dias
        - Máximo: 30 dias
        - Não pode ser mais de 1 ano no passado
        - Não pode ser mais de 1 dia no futuro

        Args:
            start_date: Data inicial
            end_date: Data final

        Returns:
            Tuple[bool, Optional[str]]: (válido, mensagem_erro)
        """
        now = datetime.now()

        # Verifica ordem das datas
        if end_date <= start_date:
            return False, "Data final deve ser posterior à data inicial"

        # Calcula duração
        period_days = (end_date - start_date).days + 1

        # Valida duração
        if period_days < 7:
            return False, f"Período mínimo: 7 dias (atual: {period_days})"

        if period_days > 30:
            return False, f"Período máximo: 30 dias (atual: {period_days})"

        # Valida limite passado (1 ano)
        one_year_ago = now.replace(year=now.year - 1)
        if start_date < one_year_ago:
            return False, (
                f"Data inicial não pode ser anterior a "
                f"{one_year_ago.strftime('%d/%m/%Y')}"
            )

        # Valida limite futuro (amanhã)
        tomorrow = now.replace(hour=23, minute=59, second=59)
        if end_date > tomorrow:
            return False, (
                f"Data final não pode ser posterior a "
                f"{tomorrow.strftime('%d/%m/%Y')}"
            )

        return True, None

    def get_fusion_weights(
        self, sources: list[str], location: tuple[float, float]
    ) -> dict[str, float]:
        """
        Calcula pesos para fusão de dados baseado em prioridades.

        ⚠️ IMPORTANTE: Valida licenças antes de calcular pesos.
        Fontes com licença estritamente não-comercial não podem ser
        usadas em fusão. Fontes CC-BY-4.0 podem ser usadas desde que
        seja dada atribuição apropriada.

        Args:
            sources: Lista de IDs de fontes selecionadas
            location: Tupla (lat, long)

        Returns:
            Dict[str, float]: Pesos normalizados para cada fonte

        Raises:
            ValueError: Se fonte com licença não-comercial for incluída
        """
        # Validação de licenciamento
        non_commercial_sources = []
        for source_id in sources:
            if source_id in self.SOURCES_CONFIG:
                config = self.SOURCES_CONFIG[source_id]
                license_type = config.get("license", "")

                # Bloqueia fontes não-comerciais em fusão
                if license_type == "non_commercial":
                    non_commercial_sources.append(
                        {
                            "id": source_id,
                            "name": config["name"],
                            "license": license_type,
                            "use_case": config.get("use_case", ""),
                        }
                    )

        if non_commercial_sources:
            source_names = ", ".join(
                [s["name"] for s in non_commercial_sources]
            )
            error_msg = (
                f"License violation: {source_names} cannot be used in "
                f"data fusion due to non-commercial license restrictions. "
                f"These sources are restricted to: "
                f"{non_commercial_sources[0]['use_case']}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Cálculo de pesos (prioridade inversa)
        weights = {}
        total_priority = 0

        for source_id in sources:
            if source_id in self.SOURCES_CONFIG:
                # Peso inverso da prioridade (menor prioridade = maior peso)
                priority = self.SOURCES_CONFIG[source_id]["priority"]
                weight = 1.0 / priority
                weights[source_id] = weight
                total_priority += weight

        # Normaliza pesos (soma = 1.0)
        if total_priority > 0:
            weights = {k: v / total_priority for k, v in weights.items()}

        logger.debug("Fusion weights for %s: %s", sources, weights)
        return weights

    def get_validation_info(self) -> dict:
        """
        Retorna informações sobre datasets de validação.

        Returns:
            Dict: Informações dos datasets de validação
        """
        return self.VALIDATION_DATASETS
