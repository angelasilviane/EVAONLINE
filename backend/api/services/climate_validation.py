"""
Serviço de validação centralizado para dados climáticos.

Responsabilidades:
1. Valida coordenadas (-90 a 90, -180 a 180)
2. Valida formato de datas (YYYY-MM-DD)
3. Valida período (7, 14, 21 ou 30 dias) para dashboard online tempo real
4. Valida período (1-90 dias) para requisições históricas enviadas por email
5. Valida período fixo (6 dias: hoje→hoje+5d) para previsão dashboard
6. Valida variáveis climáticas
7. Valida nome de fonte (string)
"""

from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from .climate_source_availability import OperationMode


class ClimateValidationService:
    """Centraliza validações de coordenadas e datas climáticas."""

    # Constantes de validação
    LAT_MIN, LAT_MAX = -90.0, 90.0
    LON_MIN, LON_MAX = -180.0, 180.0

    # LIMITES DE PERÍODO POR MODO (conforme pseudocódigo):
    # 1. HISTORICAL_EMAIL: 1-90 dias, end ≤ hoje-30d (email, escolha livre)
    # 2. DASHBOARD_CURRENT: [7,14,21,30] dias, end=hoje (web, dropdown)
    # 3. DASHBOARD_FORECAST: 6 dias fixo (hoje→hoje+5d), previsões web
    #
    # Limites temporais de cada API em climate_source_availability.py:
    # - NASA POWER: 1990-01-01 → hoje
    # - Open-Meteo Archive: 1990-01-01 → hoje-2d
    # - Open-Meteo Forecast: hoje-30d → hoje+5d
    # - MET Norway: hoje → hoje+5d
    # - NWS Forecast: hoje → hoje+5d (USA)
    # - NWS Stations: tempo real apenas, dia atual (USA)

    # Variáveis válidas (padronizadas para todas as APIs)
    VALID_CLIMATE_VARIABLES = {
        # Temperatura
        "temperature_2m",
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        # Umidade
        "relative_humidity_2m",
        "relative_humidity_2m_max",
        "relative_humidity_2m_min",
        "relative_humidity_2m_mean",
        # Vento (IMPORTANTE: todas as APIs fornecem a 2m após conversão)
        "wind_speed_2m",
        "wind_speed_2m_mean",
        "wind_speed_2m_ms",
        # Precipitação
        "precipitation",
        "precipitation_sum",
        # Radiação solar
        "solar_radiation",
        "shortwave_radiation_sum",
        # Evapotranspiração
        "evapotranspiration",
        "et0_fao_evapotranspiration",
    }

    # Fontes válidas (todas as 6 APIs implementadas)
    VALID_SOURCES = {
        # Global - Dados Históricos
        "openmeteo_archive",  # Histórico (1990-01-01 → hoje-2d)
        "nasa_power",  # Histórico (1990-01-01 → hoje)
        # Global - Previsão/Recent
        "openmeteo_forecast",  # Recent+Forecast (hoje-30d → hoje+5d)
        "met_norway",  # Previsão (hoje → hoje+5d)
        # USA Continental - Previsão
        "nws_forecast",  # Previsão (hoje → hoje+5d)
        "nws_stations",  # Observações tempo real (apenas dia atual)
    }

    # NOTA: Limites temporais detalhados (start_date, end_date_offset)
    # estão em climate_source_availability.py (fonte única da verdade)
    # Este módulo apenas valida FORMATO e PERÍODO (7-30 dias)

    @staticmethod
    def validate_request_mode(
        mode: str,
        start_date: str,
        end_date: str,
        period_days: int | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Valida modo de operação e suas restrições específicas.

        Args:
            mode: Modo de operação:
                'historical_email', 'dashboard_current', 'dashboard_forecast'
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            period_days: Número de dias (opcional, será calculado se omitido)

        Returns:
            Tupla (válido, detalhes)
        """
        valid_modes = [
            OperationMode.HISTORICAL_EMAIL.value,
            OperationMode.DASHBOARD_CURRENT.value,
            OperationMode.DASHBOARD_FORECAST.value,
        ]
        if mode not in valid_modes:
            return False, {
                "error": f"Invalid mode '{mode}'. Valid: {valid_modes}"
            }

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            return False, {"error": f"Invalid date format: {e}"}

        if period_days is None:
            period_days = (end - start).days + 1

        today = datetime.now().date()
        errors = []

        # MODO 1: HISTORICAL_EMAIL (dados antigos, envio por email)
        if mode == OperationMode.HISTORICAL_EMAIL.value:
            # Período: 1-90 dias
            if not (1 <= period_days <= 90):
                errors.append(
                    f"Historical period must be 1-90 days, got {period_days}"
                )
            # Constraint: end_date ≤ hoje - 30 dias
            max_end = today - timedelta(days=30)
            if end > max_end:
                errors.append(
                    f"Historical end_date must be ≤ {max_end.isoformat()} "
                    f"(today - 30 days), got {end_date}"
                )

        # MODO 2: DASHBOARD_CURRENT (dados recentes, web tempo real)
        elif mode == OperationMode.DASHBOARD_CURRENT.value:
            # Período: exatamente 7, 14, 21 ou 30 dias (dropdown)
            if period_days not in [7, 14, 21, 30]:
                errors.append(
                    f"Dashboard period must be [7, 14, 21, 30] days, "
                    f"got {period_days}"
                )
            # Constraint: end_date = hoje (fixo)
            if end != today:
                errors.append(
                    f"Dashboard end_date must be today ({today.isoformat()}), "
                    f"got {end_date}"
                )

        # MODO 3: DASHBOARD_FORECAST (previsão 5 dias, web)
        elif mode == OperationMode.DASHBOARD_FORECAST.value:
            # Período: hoje → hoje+5d = 6 dias (14, 15, 16, 17, 18, 19)
            if period_days != 6:
                errors.append(
                    f"Forecast period must be exactly 6 days "
                    f"(today → today+5d), got {period_days}"
                )
            # Constraint: start_date = hoje
            if start != today:
                errors.append(
                    f"Forecast start_date must be today "
                    f"({today.isoformat()}), got {start_date}"
                )
            # Constraint: end_date = hoje + 5 dias
            expected_end = today + timedelta(days=5)
            if end != expected_end:
                errors.append(
                    f"Forecast end_date must be {expected_end.isoformat()} "
                    f"(today+5d), got {end_date}"
                )

        if errors:
            logger.warning(f"Mode validation failed for '{mode}': {errors}")
            return False, {"errors": errors, "mode": mode}

        logger.debug(
            f"Mode '{mode}' validated: {start_date} to {end_date} "
            f"({period_days} days)"
        )
        return True, {
            "mode": mode,
            "start": start,
            "end": end,
            "period_days": period_days,
            "valid": True,
        }

    @staticmethod
    def validate_coordinates(
        lat: float, lon: float, location_name: str = "Location"
    ) -> tuple[bool, dict[str, Any]]:
        """
        Valida coordenadas geográficas.

        Args:
            lat: Latitude
            lon: Longitude
            location_name: Nome do local (para mensagens de erro)

        Returns:
            Tupla (válido, detalhes)
        """
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            return False, {"error": "Invalid coordinates format"}

        errors = []

        lat_min = ClimateValidationService.LAT_MIN
        lat_max = ClimateValidationService.LAT_MAX
        lon_min = ClimateValidationService.LON_MIN
        lon_max = ClimateValidationService.LON_MAX

        if not lat_min <= lat <= lat_max:
            errors.append(f"Latitude {lat} out of range ({lat_min}~{lat_max})")

        if not lon_min <= lon <= lon_max:
            errors.append(
                f"Longitude {lon} out of range " f"({lon_min}~{lon_max})"
            )

        if errors:
            logger.warning(
                f"Coordinate validation failed "
                f"for {location_name}: {errors}"
            )
            return False, {"errors": errors}

        logger.debug(f"Coordinates validated: {location_name} ({lat}, {lon})")
        return True, {"lat": lat, "lon": lon, "valid": True}

    @staticmethod
    def validate_date_range(
        start_date: str,
        end_date: str,
        allow_future: bool = False,
        max_future_days: int = 0,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Valida FORMATO de datas e limites de futuro.

        NOTA: NÃO valida período em dias (min/max).
        Cada modo valida seu período específico em validate_request_mode().
        Cada API valida limites temporais próprios em
        climate_source_availability.py.

        Args:
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            allow_future: Se permite datas futuras
            max_future_days: Máximo de dias no futuro permitido
                (0 = até hoje, 5 = até hoje+5d para forecast)

        Returns:
            Tupla (válido, detalhes)
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            return False, {"error": f"Invalid date format: {e}"}

        errors = []
        today = datetime.now().date()
        max_allowed_date = today + timedelta(days=max_future_days)

        # Validações básicas
        if start > end:
            errors.append(f"Start date {start} > end date {end}")

        # Validação de futuro (com flexibilidade por modo)
        if not allow_future:
            if start > today:
                errors.append(f"Start date {start} is in the future")
            if end > today:
                errors.append(f"End date {end} is in the future")
        else:
            # Se permite futuro, verifica limite máximo
            if end > max_allowed_date:
                errors.append(
                    f"End date {end} exceeds maximum "
                    f"({max_allowed_date}, today+{max_future_days}d)"
                )

        if errors:
            logger.warning(f"Date range validation failed: {errors}")
            return False, {"errors": errors}

        period_days = (end - start).days + 1
        logger.debug(
            f"Date range validated: {start} to {end} ({period_days} days)"
        )
        return True, {
            "start": start,
            "end": end,
            "period_days": period_days,
            "valid": True,
        }

    @staticmethod
    def validate_variables(variables: list) -> tuple[bool, dict[str, Any]]:
        """
        Valida lista de variáveis climáticas.

        Args:
            variables: Lista de variáveis desejadas

        Returns:
            Tupla (válido, detalhes)
        """
        if not variables:
            return False, {"error": "At least one variable is required"}

        invalid_vars = (
            set(variables) - ClimateValidationService.VALID_CLIMATE_VARIABLES
        )

        if invalid_vars:
            logger.warning(f"Invalid climate variables: {invalid_vars}")
            return False, {
                "error": f"Invalid variables: {invalid_vars}",
                "valid_options": list(
                    ClimateValidationService.VALID_CLIMATE_VARIABLES
                ),
            }

        logger.debug(f"Variables validated: {variables}")
        return True, {"variables": variables, "valid": True}

    @staticmethod
    def validate_source(source: str) -> tuple[bool, dict[str, Any]]:
        """
        Valida fonte de dados.

        Args:
            source: Nome da fonte

        Returns:
            Tupla (válido, detalhes)
        """
        if source not in ClimateValidationService.VALID_SOURCES:
            logger.warning(f"Invalid source: {source}")
            return False, {
                "error": f"Invalid source: {source}",
                "valid_options": list(ClimateValidationService.VALID_SOURCES),
            }

        logger.debug(f"Source validated: {source}")
        return True, {"source": source, "valid": True}

    @staticmethod
    def detect_mode_from_dates(
        start_date: str, end_date: str
    ) -> tuple[str | None, str | None]:
        """
        Auto-detecta modo de operação baseado nas datas.
        NOTA: Interface tem botões, mas detector útil para validação.

        Lógica:
        1. Se start = hoje E end = hoje+5d → DASHBOARD_FORECAST
        2. Se end = hoje E period in [7,14,21,30] → DASHBOARD_CURRENT
        3. Se end ≤ hoje-30d E period ≤ 90 → HISTORICAL_EMAIL
        4. Caso contrário → None (modo não identificável)

        Args:
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)

        Returns:
            Tupla (modo detectado ou None, mensagem de erro)
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            return None, f"Invalid date format: {e}"

        today = datetime.now().date()
        period_days = (end - start).days + 1

        # Regra 1: DASHBOARD_FORECAST
        if start == today and end == today + timedelta(days=5):
            return "dashboard_forecast", None

        # Regra 2: DASHBOARD_CURRENT
        if end == today and period_days in [7, 14, 21, 30]:
            return "dashboard_current", None

        # Regra 3: HISTORICAL_EMAIL
        if end <= today - timedelta(days=30) and 1 <= period_days <= 90:
            return "historical_email", None

        # Caso contrário: ambíguo
        return None, (
            f"Cannot detect mode from dates {start_date} to {end_date}. "
            f"Period: {period_days} days. "
            f"Please specify mode explicitly."
        )

    @staticmethod
    def validate_all(
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        variables: list,
        source: str = "openmeteo_forecast",
        allow_future: bool = False,
        mode: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Valida todos os parâmetros de uma vez.

        Args:
            lat, lon: Coordenadas
            start_date, end_date: Intervalo de datas
            variables: Variáveis climáticas
            source: Fonte de dados
            allow_future: Permite datas futuras
            mode: Modo de operação (None = auto-detect)

        Returns:
            Tupla (válido, detalhes)
        """
        # Auto-detectar modo se não fornecido
        if mode is None:
            detected_mode, error = (
                ClimateValidationService.detect_mode_from_dates(
                    start_date, end_date
                )
            )
            if detected_mode:
                mode = detected_mode
                logger.info(f"Auto-detected mode: {mode}")
            else:
                logger.warning(f"Mode auto-detection failed: {error}")
                # Continua validação sem modo (para compatibilidade)

        validations = [
            (
                "coordinates",
                ClimateValidationService.validate_coordinates(lat, lon),
            ),
        ]

        # Determinar max_future_days baseado no modo
        max_future_days = 0  # Padrão: até hoje
        if mode == "dashboard_forecast":
            max_future_days = 5  # Até hoje+5d

        validations.append(
            (
                "date_range",
                ClimateValidationService.validate_date_range(
                    start_date,
                    end_date,
                    allow_future=allow_future,
                    max_future_days=max_future_days,
                ),
            )
        )

        validations.extend(
            [
                (
                    "variables",
                    ClimateValidationService.validate_variables(variables),
                ),
                ("source", ClimateValidationService.validate_source(source)),
            ]
        )

        # Adicionar validação de modo se detectado
        if mode:
            validations.append(
                (
                    "mode",
                    ClimateValidationService.validate_request_mode(
                        mode, start_date, end_date
                    ),
                )
            )

        errors = {}
        details = {}

        for name, (valid, detail) in validations:
            if not valid:
                errors[name] = detail
            else:
                details[name] = detail

        if errors:
            logger.warning(f"Validation errors: {errors}")
            return False, {"errors": errors, "details": details}

        logger.info(f"All validations passed for ({lat}, {lon})")
        return True, {"all_valid": True, "details": details}


# Instância singleton
climate_validation_service = ClimateValidationService()
