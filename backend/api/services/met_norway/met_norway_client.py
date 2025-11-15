"""
MET Norway Locationforecast 2.0 Client with hourly-to-daily aggregation.
Usar somente "MET Norway" para MET Norway LocationForecast 2.0.

Documentation:
- https://api.met.no/weatherapi/locationforecast/2.0/documentation
- https://docs.api.met.no/doc/locationforecast/datamodel.html
- https://api.met.no/doc/locationforecast/datamodel

IMPORTANT:
- Locationforecast is GLOBAL (works anywhere)
- Returns HOURLY data that must be aggregated to daily
- No separate daily endpoint - aggregation done in backend
- 5-day forecast limit (standardized)

License: CC-BY 4.0 - Attribution required in all visualizations

Variable (from MET Norway JSON):
Instant values (hourly snapshots):
- air_temperature: Air temperature (°C)
- relative_humidity: Relative humidity (%)
- wind_speed: Wind speed at 10m (m/s)

Next 1 hour:
- precipitation_amount: Hourly precipitation (mm)

Next 6 hours:
- air_temperature_max: Maximum temperature (°C)
- air_temperature_min: Minimum temperature (°C)
- precipitation_amount: 6-hour precipitation (mm)

"""

import os
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
import numpy as np
from loguru import logger

# Import para detecção regional (fonte única)
from backend.api.services.geographic_utils import (
    GeographicUtils,
    TimezoneUtils,
    validate_coordinates,
)
from backend.api.services.weather_utils import WeatherConversionUtils
from pydantic import BaseModel, Field


class METNorwayConfig(BaseModel):
    """MET Norway API configuration."""

    # Base URL (GLOBAL, not just Europe)
    base_url: str = os.getenv(
        "MET_NORWAY_URL",
        "https://api.met.no/weatherapi/locationforecast/2.0/compact",
    )

    # Request timeout
    timeout: int = 30

    # Retry configuration
    retry_attempts: int = 3
    retry_delay: float = 1.0

    # User-Agent required (MET Norway requires identification)
    user_agent: str = os.getenv(
        "MET_NORWAY_USER_AGENT",
        "EVAonline/1.0 (https://github.com/angelassilviane/EVAONLINE)",
    )


class METNorwayDailyData(BaseModel):
    """Daily aggregated data from MET Norway API.

    Field names match our standardized output schema, but are calculated
    from MET Norway's API variable names:
    - temp_max/min: from air_temperature_max/min (next_6_hours)
    - temp_mean: calculated from hourly air_temperature (instant)
    - humidity_mean: calculated from hourly relative_humidity (instant)
    - precipitation_sum: calculated from precipitation_amount (next_1_hours)
    - wind_speed_2m_mean: converted from wind_speed (10m) using FAO-56 formula
    """

    date: datetime = Field(..., description="Date of record")
    temp_max: float | None = Field(
        None, description="Maximum temperature (°C) - from air_temperature_max"
    )
    temp_min: float | None = Field(
        None, description="Minimum temperature (°C) - from air_temperature_min"
    )
    temp_mean: float | None = Field(
        None, description="Mean temperature (°C) - from hourly air_temperature"
    )
    humidity_mean: float | None = Field(
        None,
        description=(
            "Mean relative humidity (%) - from hourly relative_humidity"
        ),
    )
    precipitation_sum: float | None = Field(
        None,
        description="Total precipitation (mm/day) - from precipitation_amount",
    )
    wind_speed_2m_mean: float | None = Field(
        None,
        description=(
            "Mean wind speed at 2m (m/s) - converted from 10m using FAO-56"
        ),
    )
    source: str = Field(default="met_norway", description="Data source")


class METNorwayCacheMetadata(BaseModel):
    """Metadata for cached MET Norway responses."""

    last_modified: str | None = Field(
        None, description="Last-Modified header from API (RFC 1123 format)"
    )
    expires: datetime | None = Field(
        None, description="Expiration timestamp (parsed from Expires header)"
    )
    data: list[METNorwayDailyData] = Field(
        ..., description="Cached forecast data"
    )


class METNorwayClient:
    """
    MET Norway client with
    GLOBAL coverage and DAILY data support.

    Regional Quality Strategy:
    - Nordic Region (NO, SE, FI, DK, Baltics): High-quality precipitation
      with radar + crowdsourced bias-correction (1km MET Nordic)
    - Rest of World: Temperature and humidity only (9km ECMWF base)
      Precipitation has lower quality without post-processing
    """

    # Daily variables available from MET Norway
    # Note: Solar radiation NOT available - use other APIs
    # API variable names (from MET Norway JSON):
    #   - air_temperature (instant, hourly)
    #   - air_temperature_max (next_6_hours)
    #   - air_temperature_min (next_6_hours)
    #   - relative_humidity (instant, hourly)
    #   - precipitation_amount (next_1_hours, next_6_hours)
    #   - wind_speed (instant, hourly)
    DAILY_VARIABLES_FOR_ETO = [
        "air_temperature_max",
        "air_temperature_min",
        "air_temperature_mean",  # Calculated from hourly air_temperature
        "precipitation_sum",  # Calculated from precipitation_amount
        "relative_humidity_mean",  # Calculated from hourly relative_humidity
    ]

    # Variables for Nordic region (high quality with bias correction)
    NORDIC_VARIABLES = [
        "air_temperature_max",
        "air_temperature_min",
        "air_temperature_mean",
        "precipitation_sum",  # High quality: radar + crowdsourced
        "relative_humidity_mean",
    ]

    # Variables for rest of world (basic ECMWF, skip precipitation)
    GLOBAL_VARIABLES = [
        "air_temperature_max",
        "air_temperature_min",
        "air_temperature_mean",
        "relative_humidity_mean",
        # precipitation_sum excluded: use Open-Meteo for better quality
    ]

    def __init__(
        self,
        config: METNorwayConfig | None = None,
        cache: Any | None = None,
    ):
        """
        Initialize MET Norway client (GLOBAL).

        Args:
            config: Custom configuration (optional)
            cache: ClimateCacheService (optional)
        """
        self.config = config or METNorwayConfig()

        # Required headers
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
        }

        self.client = httpx.AsyncClient(
            timeout=self.config.timeout, headers=headers
        )
        self.cache = cache

    async def close(self):
        """Close HTTP connection."""
        await self.client.aclose()

    @staticmethod
    def _round_coordinates(lat: float, lon: float) -> tuple[float, float]:
        """
        Round coordinates to 4 decimal places as required by MET Norway API.

        From API documentation:
        "Most forecast models are fairly coarse, e.g. using a 1km resolution
        grid. This means there is no need to send requests with any higher
        resolution coordinates. For this reason you should never use more
        than 4 decimals in lat/lon coordinates."

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Tuple of (rounded_lat, rounded_lon)
        """
        return round(lat, 4), round(lon, 4)

    @staticmethod
    def _parse_rfc1123_date(date_str: str | None) -> datetime | None:
        """
        Parse RFC 1123 date format from HTTP headers.

        Args:
            date_str: Date string in RFC 1123 format
                     (e.g., "Tue, 16 Jun 2020 12:13:49 GMT")

        Returns:
            Parsed datetime or None if parsing fails
        """
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None

    @classmethod
    def is_in_nordic_region(cls, lat: float, lon: float) -> bool:
        """
        Check if coordinates are in Nordic region (MET Nordic 1km dataset).

        The MET Nordic dataset provides high-quality weather data with:
        - 1km resolution (vs 9km global)
        - Hourly updates (vs 4x/day global)
        - Extensive post-processing with radar and crowdsourced data
        - Bias correction for precipitation using radar + Netatmo stations

        Coverage: Norway, Denmark, Sweden, Finland, Baltic countries

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            True if in Nordic region (high quality), False otherwise
        """
        return GeographicUtils.is_in_nordic(lat, lon)

    @classmethod
    def get_recommended_variables(cls, lat: float, lon: float) -> list[str]:
        """
        Get recommended variables based on location quality.

        Strategy:
        - Nordic region: Include precipitation (radar + bias-corrected)
        - Rest of world: Exclude precipitation (use Open-Meteo instead)

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            List of recommended variable names for the location
        """
        if cls.is_in_nordic_region(lat, lon):
            logger.debug(
                f"📍 Location ({lat}, {lon}) in NORDIC region: "
                f"Using high-quality precipitation (1km + radar)"
            )
            return cls.NORDIC_VARIABLES
        else:
            logger.debug(
                f"📍 Location ({lat}, {lon}) OUTSIDE Nordic region: "
                f"Skipping precipitation (use Open-Meteo)"
            )
            return cls.GLOBAL_VARIABLES

    @validate_coordinates
    async def get_daily_forecast(
        self,
        lat: float,
        lon: float,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        timezone: str | None = None,
        variables: list[str] | None = None,
    ) -> list[METNorwayDailyData]:
        """
        Fetch DAILY weather forecast with pre-calculated aggregations.

        Implements MET Norway API best practices:
        - Coordinates rounded to 4 decimals (cache efficiency)
        - If-Modified-Since headers (avoid unnecessary downloads)
        - Dynamic TTL based on Expires header
        - Status code 203/429 handling

        Performs hourly-to-daily aggregation of MET Norway data including:
        - Temperature extremes and means
        - Humidity
        - Precipitation sums

        Note: Solar radiation and wind speed are NOT provided.
        Use other APIs (Open-Meteo) for radiation and wind data.

        Args:
            lat: Latitude in decimal degrees (-90 to 90)
            lon: Longitude in decimal degrees (-180 to 180)
            start_date: Start date (default: today)
            end_date: End date (default: start + 5 days)
            timezone: Timezone name (e.g., 'America/Sao_Paulo')
            variables: List of variables to fetch (default: all for ETo)

        Returns:
            List of daily aggregated weather records

        Raises:
            ValueError: Invalid coordinates or date range exceeds 5-day limit
        """
        # NOTE: Coordinate and date validation should happen
        # in climate_validation.py + climate_source_availability.py
        # BEFORE calling this client. This method assumes pre-validated data.

        # Round coordinates to 4 decimals (API best practice)
        lat, lon = self._round_coordinates(lat, lon)

        # Default dates
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=5)

        if start_date > end_date:
            msg = "start_date must be <= end_date"
            raise ValueError(msg)

        # Default variables (optimized for location quality)
        if not variables:
            variables = self.get_recommended_variables(lat, lon)

        # Check if we're in Nordic region for logging
        in_nordic = self.is_in_nordic_region(lat, lon)
        region_label = "NORDIC (1km)" if in_nordic else "GLOBAL (9km)"

        logger.info(
            f"📍 MET Norway ({region_label}): "
            f"lat={lat}, lon={lon}, variables={len(variables)}"
        )

        # Build cache key
        vars_str = "_".join(sorted(variables)) if variables else "default"
        cache_key = (
            f"met_lf_{lat}_{lon}_{start_date.date()}_"
            f"{end_date.date()}_{vars_str}"
        )
        cache_metadata_key = f"{cache_key}_metadata"

        # 1. Check cache and expiration
        if self.cache:
            cached_metadata = await self.cache.get(cache_metadata_key)
            if cached_metadata:
                # Check if data has expired
                if (
                    cached_metadata.expires
                    and datetime.now() < cached_metadata.expires
                ):
                    logger.info("🎯 Cache HIT (not expired): " "MET Norway")
                    return cached_metadata.data

                # Data expired - try conditional request with If-Modified-Since
                logger.info(
                    "Cache expired, checking with If-Modified-Since..."
                )
                last_modified = cached_metadata.last_modified
            else:
                last_modified = None
        else:
            last_modified = None

        # 2. Fetch from API (with conditional request if possible)
        logger.info("Querying MET Norway API...")

        # Request parameters
        params: dict[str, float | str] = {
            "lat": lat,
            "lon": lon,
        }

        if timezone:
            params["timezone"] = timezone
            logger.warning(
                "Timezone parameter may affect date boundaries. "
                "Ensure proper handling in aggregation."
            )

        # Request with retry
        for attempt in range(self.config.retry_attempts):
            try:
                logger.debug(
                    f"MET Norway request "
                    f"(attempt {attempt + 1}/{self.config.retry_attempts}): "
                    f"lat={lat}, lon={lon}"
                )

                # Add If-Modified-Since header if we have cached data
                headers = {}
                if last_modified:
                    headers["If-Modified-Since"] = last_modified
                    logger.debug(f"Using If-Modified-Since: {last_modified}")

                response = await self.client.get(
                    self.config.base_url, params=params, headers=headers
                )

                # Handle 304 Not Modified
                if response.status_code == 304:
                    logger.info("✅ 304 Not Modified: Using cached data")
                    if self.cache:
                        cached_metadata = await self.cache.get(
                            cache_metadata_key
                        )
                        if cached_metadata:
                            # Update expiration time
                            expires_header = response.headers.get("Expires")
                            if expires_header:
                                new_expires = self._parse_rfc1123_date(
                                    expires_header
                                )
                                cached_metadata.expires = new_expires
                                # Re-cache with updated expiration
                                ttl = self._calculate_ttl(new_expires)
                                await self.cache.set(
                                    cache_metadata_key,
                                    cached_metadata,
                                    ttl=ttl,
                                )
                            return cached_metadata.data
                    # Fallback if cache unavailable
                    return []

                # Handle 203 Non-Authoritative (deprecated/beta)
                if response.status_code == 203:
                    logger.warning(
                        "⚠️ 203 Non-Authoritative Information: "
                        "This product version is deprecated or in beta. "
                        "Check documentation for updates."
                    )

                # Handle 429 Too Many Requests (rate limiting)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    logger.error(
                        f"❌ 429 Too Many Requests: Rate limit exceeded. "
                        f"Retry after {retry_after}s. "
                        f"Consider reducing request frequency."
                    )
                    raise httpx.HTTPStatusError(
                        f"Rate limited (429). Retry after {retry_after}s",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()

                # Extract headers
                last_modified_header = response.headers.get("Last-Modified")
                expires_header = response.headers.get("Expires")

                logger.debug(
                    f"Response headers - "
                    f"Last-Modified: {last_modified_header}, "
                    f"Expires: {expires_header}"
                )

                # Parse expires timestamp
                expires_dt = self._parse_rfc1123_date(expires_header)

                # Process response
                data = response.json()
                parsed_data = self._parse_daily_response(
                    data, variables, start_date, end_date
                )

                logger.info(
                    f"MET Norway: " f"{len(parsed_data)} days retrieved"
                )

                # 3. Save to cache with metadata
                if self.cache and parsed_data:
                    # Create metadata object
                    metadata = METNorwayCacheMetadata(
                        last_modified=last_modified_header,
                        expires=expires_dt,
                        data=parsed_data,
                    )

                    # Calculate TTL from Expires header (with fallback)
                    ttl = self._calculate_ttl(expires_dt)

                    # Save to cache
                    await self.cache.set(cache_metadata_key, metadata, ttl=ttl)
                    logger.debug(
                        f"Cache SAVE: MET Norway"
                        f"(TTL: {ttl}s, expires: {expires_dt})"
                    )

                return parsed_data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Don't retry on rate limiting
                    raise
                logger.warning(
                    f"MET Norway request failed "
                    f"(attempt {attempt + 1}): {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    raise
                await self._delay_retry()

            except httpx.HTTPError as e:
                logger.warning(
                    f"MET Norway request failed "
                    f"(attempt {attempt + 1}): {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    raise
                await self._delay_retry()

        return []

    @staticmethod
    def _calculate_ttl(expires: datetime | None) -> int:
        """
        Calculate cache TTL from Expires header.

        Args:
            expires: Expiration datetime from Expires header

        Returns:
            TTL in seconds (default: 3600 if no Expires header)
        """
        if not expires:
            # Default to 1 hour if no Expires header
            return 3600

        now = (
            datetime.now(expires.tzinfo) if expires.tzinfo else datetime.now()
        )
        ttl_seconds = int((expires - now).total_seconds())

        # Ensure TTL is positive and reasonable
        if ttl_seconds <= 0:
            return 60  # Minimum 1 minute
        if ttl_seconds > 86400:  # Max 24 hours
            return 86400

        return ttl_seconds

    def _parse_daily_response(
        self,
        data: dict,
        variables: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> list[METNorwayDailyData]:
        """
        Process MET Norway API response usando METNorwayAggregator.

        Args:
            data: API response JSON
            variables: Requested variable names (for validation)
            start_date: Start of period
            end_date: End of period

        Returns:
            List of daily aggregated records
        """
        try:
            # Extract geometry for calculations
            geometry = data.get("geometry", {})
            coordinates = geometry.get("coordinates", [])

            if len(coordinates) >= 2:
                api_lon, api_lat = coordinates[0], coordinates[1]
                api_elevation = (
                    coordinates[2] if len(coordinates) > 2 else None
                )
                logger.debug(
                    f"API geometry: lat={api_lat}, lon={api_lon}, "
                    f"elev={api_elevation}m"
                )
            else:
                api_lat, api_lon, api_elevation = None, None, None
                logger.warning("No geometry in API response")

            timeseries = data.get("properties", {}).get("timeseries", [])

            if not timeseries:
                logger.warning("MET Norway: no data")
                return []

            # Usar METNorwayAggregator para processamento
            aggregator = METNorwayAggregator()

            # 1. Agregar dados horários em diários
            daily_raw_data = aggregator.aggregate_hourly_to_daily(
                timeseries, start_date, end_date, TimezoneUtils
            )

            # 2. Calcular agregações finais
            daily_data = aggregator.calculate_daily_aggregations(
                daily_raw_data, WeatherConversionUtils()
            )

            # 3. Validar dados agregados
            if not aggregator.validate_daily_data(daily_data):
                logger.warning("Dados diários falharam na validação")

            logger.info(
                f"MET Norway parsed: {len(daily_data)} days "
                f"from {len(timeseries)} hourly entries"
            )
            return daily_data

        except Exception as e:
            logger.error(
                f"❌ Error processing MET Norway response: {e}",
                exc_info=True,
            )
            msg = f"Invalid MET Norway response: {e}"
            raise ValueError(msg) from e

    async def _delay_retry(self):
        """Wait before retry attempt."""
        import asyncio

        await asyncio.sleep(self.config.retry_delay)

    async def health_check(self) -> bool:
        """
        Check if MET Norway API is accessible.

        Returns:
            True if API responds successfully, False otherwise
        """
        try:
            # Brasília, Brazil (testing with GLOBAL coordinates)
            params: dict[str, float | str] = {
                "lat": -15.7939,
                "lon": -47.8828,
            }

            response = await self.client.get(
                self.config.base_url, params=params
            )
            response.raise_for_status()

            logger.info("MET Norway health check: OK")
            return True

        except Exception as e:
            logger.error(f"MET Norway health check failed: {e}")
            return False

    def get_attribution(self) -> str:
        """
        Return CC-BY 4.0 attribution text.

        Returns:
            Attribution text as required by license
        """
        return "Weather data from MET Norway (CC BY 4.0)"

    def get_coverage_info(self) -> dict[str, Any]:
        """
        Return geographic coverage information.

        Returns:
            dict: Coverage information with regional quality tiers
        """
        return {
            "region": "GLOBAL",
            "bbox": {
                "lon_min": -180,
                "lat_min": -90,
                "lon_max": 180,
                "lat_max": 90,
            },
            "description": (
                "Global coverage with regional quality optimization"
            ),
            "forecast_horizon": "5 days ahead (standardized)",
            "data_type": "Forecast (no historical data)",
            "update_frequency": "Updated every 6 hours",
            "quality_tiers": {
                "nordic": {
                    "region": "Norway, Denmark, Sweden, Finland, Baltics",
                    "bbox": GeographicUtils.NORDIC_BBOX,
                    "resolution": "1 km",
                    "model": "MEPS 2.5km + downscaling",
                    "updates": "Hourly",
                    "post_processing": "Extensive (radar + crowdsourced)",
                    "variables": (
                        "Temperature, Humidity, Precipitation (high quality)"
                    ),
                    "precipitation_quality": (
                        "High (radar + Netatmo bias correction)"
                    ),
                },
                "global": {
                    "region": "Rest of World",
                    "resolution": "9 km",
                    "model": "ECMWF",
                    "updates": "4x per day",
                    "post_processing": "Minimal",
                    "variables": "Temperature, Humidity only",
                    "precipitation_quality": "Lower (use Open-Meteo instead)",
                },
            },
        }

    @classmethod
    def get_data_availability_info(cls) -> dict[str, Any]:
        """
        Return data availability information.

        Returns:
            dict: Information about temporal coverage and limitations
        """
        return {
            "data_start_date": None,  # Forecast only
            "max_historical_years": 0,
            "forecast_horizon_days": 5,
            "description": "Forecast data only, global coverage",
            "coverage": "Global",
            "update_frequency": "Every 6 hours",
        }


# Factory function
def create_met_norway_client(
    cache: Any | None = None,
) -> METNorwayClient:
    """
    Factory function to create MET Norway client
    (GLOBAL coverage).

    Args:
        cache: Optional ClimateCacheService instance

    Returns:
        Configured METNorwayClient instance
    """
    return METNorwayClient(cache=cache)


class METNorwayAggregator:
    """
    Classe especializada para agregação de dados horários MET Norway para diários.

    Responsabilidades:
    - Agregar dados horários em diários com tratamento adequado de NaN
    - Calcular estatísticas derivadas (vento 10m→2m, precipitação)
    - Validar consistência dos dados agregados
    - Logging detalhado do processo de agregação
    """

    @staticmethod
    def aggregate_hourly_to_daily(
        timeseries: list[dict],
        start_date: datetime,
        end_date: datetime,
        timezone_utils: TimezoneUtils,
    ) -> dict:
        """
        Agrega dados horários em registros diários.

        Args:
            timeseries: Lista de entradas horárias da API
            start_date: Data inicial do período
            end_date: Data final do período
            timezone_utils: Utilitários de timezone para comparações seguras

        Returns:
            Lista de dicionários com dados diários agregados
        """
        from collections import defaultdict
        from typing import Dict, List, Any
        from datetime import date

        daily_data: Dict[date, Dict[str, Any]] = defaultdict(
            lambda: {
                "temp_values": [],
                "humidity_values": [],
                "wind_speed_values": [],
                "precipitation_1h": [],
                "precipitation_6h": [],
                "temp_max_6h": [],
                "temp_min_6h": [],
                "count": 0,
            }
        )

        # Processar cada entrada horária
        for entry in timeseries:
            try:
                time_str = entry.get("time")
                if not time_str:
                    continue

                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                date_key = dt.date()

                # Filtrar por período
                if timezone_utils.compare_dates_safe(dt, start_date, "lt"):
                    continue
                if timezone_utils.compare_dates_safe(dt, end_date, "gt"):
                    continue

                day_data = daily_data[date_key]

                # Extrair valores instantâneos
                instant = (
                    entry.get("data", {}).get("instant", {}).get("details", {})
                )

                # Temperatura
                temp = instant.get("air_temperature")
                if temp is not None:
                    day_data["temp_values"].append(temp)

                # Umidade
                humidity = instant.get("relative_humidity")
                if humidity is not None:
                    day_data["humidity_values"].append(humidity)

                # Velocidade do vento
                wind_speed = instant.get("wind_speed")
                if wind_speed is not None:
                    day_data["wind_speed_values"].append(wind_speed)

                # Precipitação 1h (prioridade)
                next_1h = (
                    entry.get("data", {})
                    .get("next_1_hours", {})
                    .get("details", {})
                )
                precip_1h = next_1h.get("precipitation_amount")
                if precip_1h is not None:
                    day_data["precipitation_1h"].append(precip_1h)

                # Precipitação 6h (fallback)
                next_6h = (
                    entry.get("data", {})
                    .get("next_6_hours", {})
                    .get("details", {})
                )
                precip_6h = next_6h.get("precipitation_amount")
                if precip_6h is not None:
                    day_data["precipitation_6h"].append(precip_6h)

                # Temperaturas extremas 6h
                temp_max_6h = next_6h.get("air_temperature_max")
                if temp_max_6h is not None:
                    day_data["temp_max_6h"].append(temp_max_6h)

                temp_min_6h = next_6h.get("air_temperature_min")
                if temp_min_6h is not None:
                    day_data["temp_min_6h"].append(temp_min_6h)

                day_data["count"] += 1

            except Exception as e:
                logger.warning(f"Erro processando entrada horária: {e}")
                continue

        return dict(daily_data)

    @staticmethod
    def calculate_daily_aggregations(
        daily_raw_data: dict,
        weather_utils: WeatherConversionUtils,
    ) -> list[METNorwayDailyData]:
        """
        Calcula agregações diárias finais a partir dos dados brutos.

        Args:
            daily_raw_data: Dados diários brutos agrupados por data
            weather_utils: Utilitários para conversões meteorológicas

        Returns:
            Lista de registros diários agregados
        """
        result = []

        for date_key, day_values in daily_raw_data.items():
            try:
                # Temperatura média
                temp_mean = (
                    float(np.nanmean(day_values["temp_values"]))
                    if day_values["temp_values"]
                    else None
                )

                # Temperaturas extremas: preferir 6h, fallback para instant
                temp_max = (
                    float(np.nanmax(day_values["temp_max_6h"]))
                    if day_values["temp_max_6h"]
                    else (
                        float(np.nanmax(day_values["temp_values"]))
                        if day_values["temp_values"]
                        else None
                    )
                )

                temp_min = (
                    float(np.nanmin(day_values["temp_min_6h"]))
                    if day_values["temp_min_6h"]
                    else (
                        float(np.nanmin(day_values["temp_values"]))
                        if day_values["temp_values"]
                        else None
                    )
                )

                # Umidade média
                humidity_mean = (
                    float(np.nanmean(day_values["humidity_values"]))
                    if day_values["humidity_values"]
                    else None
                )

                # Velocidade do vento: converter 10m → 2m
                wind_10m_mean = (
                    float(np.nanmean(day_values["wind_speed_values"]))
                    if day_values["wind_speed_values"]
                    else None
                )
                wind_2m_mean = weather_utils.convert_wind_10m_to_2m(
                    wind_10m_mean
                )

                if wind_2m_mean is not None:
                    logger.debug(
                        f"✅ Vento convertido 10m→2m para {date_key}: "
                        f"{wind_10m_mean:.2f} → {wind_2m_mean:.2f} m/s"
                    )

                # Precipitação: priorizar 1h, fallback para 6h
                if day_values["precipitation_1h"]:
                    precipitation_sum = float(
                        np.sum(day_values["precipitation_1h"])
                    )
                elif day_values["precipitation_6h"]:
                    precipitation_sum = float(
                        np.sum(day_values["precipitation_6h"])
                    )
                    logger.debug(
                        f"Usando precipitação 6h para {date_key}: "
                        f"{len(day_values['precipitation_6h'])} períodos"
                    )
                else:
                    precipitation_sum = 0.0

                # Criar registro diário
                daily_record = METNorwayDailyData(
                    date=date_key,
                    temp_max=temp_max,
                    temp_min=temp_min,
                    temp_mean=temp_mean,
                    humidity_mean=humidity_mean,
                    precipitation_sum=precipitation_sum,
                    wind_speed_2m_mean=wind_2m_mean,
                )

                result.append(daily_record)

            except Exception as e:
                logger.warning(f"Erro agregando dia {date_key}: {e}")
                continue

        # Ordenar por data
        result.sort(key=lambda x: x.date)
        return result

    @staticmethod
    def validate_daily_data(daily_data: list[METNorwayDailyData]) -> bool:
        """
        Valida consistência dos dados diários agregados.

        Args:
            daily_data: Lista de registros diários

        Returns:
            True se dados são consistentes, False caso contrário
        """
        if not daily_data:
            logger.warning("Dados diários vazios")
            return False

        issues = []

        for record in daily_data:
            # Verificar temperaturas
            if record.temp_max is not None and record.temp_min is not None:
                if record.temp_max < record.temp_min:
                    issues.append(
                        f"Temperatura inconsistente em {record.date}: "
                        f"max={record.temp_max} < min={record.temp_min}"
                    )

            # Verificar umidade
            if record.humidity_mean is not None:
                if not (0 <= record.humidity_mean <= 100):
                    issues.append(
                        f"Umidade fora do range em {record.date}: "
                        f"{record.humidity_mean}%"
                    )

            # Verificar precipitação
            if record.precipitation_sum is not None:
                if record.precipitation_sum < 0:
                    issues.append(
                        f"Precipitação negativa em {record.date}: "
                        f"{record.precipitation_sum}mm"
                    )

        if issues:
            for issue in issues:
                logger.warning(f"Problema de validação: {issue}")
            return False

        logger.debug(
            f"Dados diários validados: {len(daily_data)} registros OK"
        )
        return True
