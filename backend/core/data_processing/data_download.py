from datetime import datetime, timedelta
from typing import List, Tuple, Union

import numpy as np
import pandas as pd
from celery import shared_task
from loguru import logger

# Imports de módulos de validação canônicos
try:
    from backend.api.services.climate_validation import (
        ClimateValidationService,
    )
except ImportError:
    from ...api.services.climate_validation import (
        ClimateValidationService,
    )


def _classify_for_data_fusion(
    data_inicial: datetime, data_final: datetime
) -> str:
    """
    Classifica requisição para seleção de fontes no Data Fusion.

    ⚠️ USO INTERNO - Esta função é usada APENAS para selecionar quais APIs
    incluir no Data Fusion baseado no período temporal solicitado.

    NÃO confundir com os 3 modos de operação do sistema:
    - historical_email: Histórico por email (1-90d, end ≤ hoje-30d)
    - dashboard_current: Dashboard atual (7/14/21/30d, end=hoje)
    - dashboard_forecast: Dashboard previsão (6d fixo, hoje→hoje+5d)
    (validados em climate_validation.py::detect_mode_from_dates)

    Regras de classificação para Data Fusion:
    - Se data_final > hoje → "forecast" (usar APIs de previsão)
    - Se data_inicial <= hoje - 30 dias → "historical" (usar APIs históricas)
    - Senão → "current" (usar APIs de dados recentes)

    Args:
        data_inicial: Data inicial da requisição
        data_final: Data final da requisição

    Returns:
        "forecast" | "historical" | "current" (para seleção de fontes)
    """
    today = datetime.now().date()
    start_date = (
        data_inicial.date() if hasattr(data_inicial, "date") else data_inicial
    )
    end_date = data_final.date() if hasattr(data_final, "date") else data_final
    threshold = today - timedelta(days=30)

    if end_date > today:
        return "forecast"
    elif start_date <= threshold:
        return "historical"
    else:
        return "current"


@shared_task
def download_weather_data(
    data_source: Union[str, list],
    data_inicial: str,
    data_final: str,
    longitude: float,
    latitude: float,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Baixa dados meteorológicos das fontes especificadas para as coordenadas
    e período.

    - Coordenadas: climate_validation.py::validate_coordinates()
    - Datas/Período: climate_validation.py::validate_request_mode()
    - Detecção de Modo: climate_validation.py::detect_mode_from_dates()
    - Limites de APIs: Cada cliente valida internamente

    Fontes suportadas:
    - "nasa_power": NASA POWER (global, 1981+, domínio público)
    - "openmeteo_archive": Open-Meteo Archive (global, 1940+, CC BY 4.0)
    - "openmeteo_forecast": Open-Meteo Forecast (global, 16d, CC BY 4.0)
    - "met_norway": MET Norway Locationforecast
      (global, real-time, CC BY 4.0)
    - "nws_forecast": NWS Forecast (USA, previsões, domínio público)
    - "nws_stations": NWS Stations (USA, estações, domínio público)
    - "data fusion": Fusiona múltiplas fontes disponíveis (Kalman Ensemble)

    A validação dinâmica verifica automaticamente quais fontes estão
    disponíveis para as coordenadas específicas, rejeitando fontes
    indisponíveis.

    Args:
        data_source: Fonte de dados (str ou list de fontes)
        data_inicial: Data inicial no formato YYYY-MM-DD
        data_final: Data final no formato YYYY-MM-DD
        longitude: Longitude (-180 a 180)
        latitude: Latitude (-90 a 90)
    """
    # Import moved here to avoid circular imports during module initialization
    from backend.api.services.climate_source_manager import (
        ClimateSourceManager,
    )

    logger.info(
        f"Iniciando download - Fonte: {data_source}, "
        f"Período: {data_inicial} a {data_final}, "
        f"Coord: ({latitude}, {longitude})"
    )
    warnings_list = []

    # ✅ Validação de coordenadas (usando módulo canônico)
    coord_valid, coord_details = ClimateValidationService.validate_coordinates(
        lat=latitude, lon=longitude, location_name="Download Request"
    )
    if not coord_valid:
        msg = f"Coordenadas inválidas: {coord_details.get('errors')}"
        logger.error(msg)
        raise ValueError(msg)

    # ✅ Validação de formato de datas (usando módulo canônico)
    date_valid, date_details = ClimateValidationService.validate_date_range(
        start_date=data_inicial,
        end_date=data_final,
        allow_future=True,  # Permite forecast
    )
    if not date_valid:
        msg = f"Datas inválidas: {date_details.get('errors')}"
        logger.error(msg)
        raise ValueError(msg)

    # Converter para pandas datetime para cálculos
    data_inicial_formatted = pd.to_datetime(data_inicial)
    data_final_formatted = pd.to_datetime(data_final)
    period_days = date_details["period_days"]

    # 🔄 Classificar para Data Fusion (função interna)
    # NOTA: Usa _classify_for_data_fusion() que retorna classificação simples
    # ("forecast", "historical", "current") APENAS para selecionar fontes
    # no Data Fusion.
    # VALIDAÇÃO DE MODO: Deve ser feita nas rotas FastAPI ANTES de chamar
    # esta tarefa Celery, usando:
    # ClimateValidationService.validate_request_mode()
    request_type = _classify_for_data_fusion(
        data_inicial_formatted, data_final_formatted
    )
    logger.info(f"Data Fusion classification: {request_type}")

    # Validação dinâmica de fontes disponíveis para a localização
    source_manager = ClimateSourceManager()
    available_sources = source_manager.get_available_sources_for_location(
        lat=latitude,
        lon=longitude,
    )

    # Filtrar apenas fontes disponíveis para esta localização
    available_source_ids = [
        source_id
        for source_id, meta in available_sources.items()
        if meta["available"]
    ]

    logger.info(
        "Fontes disponíveis para (%s, %s): %s",
        latitude,
        longitude,
        available_source_ids,
    )

    # Validação da fonte de dados (aceita str ou list, case-insensitive)
    valid_sources = [
        "openmeteo_archive",
        "openmeteo_forecast",
        "nasa_power",
        "nws_forecast",
        "nws_stations",
        "met_norway",
        "data fusion",
    ]

    # Normalize input to list of lower-case strings
    if isinstance(data_source, list):
        requested = [str(s).lower() for s in data_source]
    else:
        # Suportar string com múltiplas fontes separadas por vírgula
        data_source_str = str(data_source).lower()
        if "," in data_source_str:
            requested = [s.strip() for s in data_source_str.split(",")]
        else:
            requested = [data_source_str]

    # Validate requested sources
    for req in requested:
        if req not in valid_sources:
            msg = f"Fonte inválida: {req}. Use: " f"{', '.join(valid_sources)}"
            logger.error(msg)
            raise ValueError(msg)

        # Para fontes específicas, verificar se estão disponíveis
        # na localização
        if req != "data fusion" and req not in available_source_ids:
            available_list = (
                ", ".join(available_source_ids)
                if available_source_ids
                else "nenhuma"
            )
            msg = (
                f"Fonte '{req}' não disponível para as coordenadas "
                f"({latitude}, {longitude}). "
                f"Fontes disponíveis: {available_list}"
            )
            logger.error(msg)
            raise ValueError(msg)

    # Define sources to query based on request_type and availability
    # NOTA: request_type ("forecast", "historical", "current") é usado aqui
    # APENAS para seleção inteligente de fontes no Data Fusion
    if "data fusion" in requested:
        # Data Fusion combina múltiplas fontes com Kalman Ensemble
        # Selecionar fontes baseadas no tipo de requisição
        if request_type == "historical":
            # APIs com dados históricos (>30 dias atrás)
            possible_sources = ["nasa_power", "openmeteo_archive"]
        elif request_type == "current":
            # APIs com dados recentes/atuais (últimos 30 dias, end=hoje)
            possible_sources = [
                "openmeteo_archive",  # Histórico até hoje-2d
                "nasa_power",  # Histórico até hoje
                "nws_stations",  # Observações tempo real (dia atual)
                "openmeteo_forecast",
            ]
        elif request_type == "forecast":
            # APIs com previsões futuras (end > hoje)
            possible_sources = [
                "openmeteo_forecast",  # Forecast: hoje-30d → hoje+5d
                "met_norway",  # Forecast: hoje → hoje+5d
                "nws_forecast",  # Forecast: hoje → hoje+5d (USA)
            ]

        sources = [
            src for src in possible_sources if src in available_source_ids
        ]

        if not sources:
            msg = (
                f"Nenhuma fonte disponível para {request_type} nas "
                f"coordenadas ({latitude}, {longitude})."
            )
            logger.error(msg)
            raise ValueError(msg)

        logger.info(
            f"Data Fusion selecionada para {request_type}, coletando de "
            f"{len(sources)} fontes disponíveis: {sources}"
        )
    else:
        sources = [req for req in requested if req in available_source_ids]
        logger.info(f"Fonte(s) selecionada(s): {sources}")

    weather_data_sources: List[pd.DataFrame] = []
    for source in sources:
        logger.info(f"📥 Processando fonte: {source}")

        # ✅ Validações de limites temporais delegadas aos clientes
        # Cada cliente (adapter) valida seus próprios limites internamente
        # NÃO há necessidade de validar aqui (duplicação removida)
        # Limites canônicos em: climate_source_availability.py
        data_final_adjusted = data_final_formatted

        # 🔄 Download data
        # NOTA: Validações de limites temporais são feitas pelos
        # próprios clientes/adapters. Cada API conhece seus limites
        # e valida internamente.
        # Inicializa variáveis
        weather_df = None

        try:
            if source == "nasa_power":
                # Usa novo cliente assíncrono via adapter síncrono
                from backend.api.services import NASAPowerSyncAdapter

                adapter = NASAPowerSyncAdapter()

                # Baixa dados via novo cliente (aceita datetime)
                nasa_data = adapter.get_daily_data_sync(
                    lat=latitude,
                    lon=longitude,
                    start_date=data_inicial_formatted,
                    end_date=data_final_adjusted,
                )

                # Converte para DataFrame pandas - variáveis NASA POWER
                data_records = []
                for record in nasa_data:
                    data_records.append(
                        {
                            "date": record.date,
                            # Variáveis NASA POWER nativas
                            "T2M_MAX": record.temp_max,
                            "T2M_MIN": record.temp_min,
                            "T2M": record.temp_mean,
                            "RH2M": record.humidity,
                            "WS2M": record.wind_speed,
                            "ALLSKY_SFC_SW_DWN": record.solar_radiation,
                            "PRECTOTCORR": record.precipitation,
                        }
                    )

                weather_df = pd.DataFrame(data_records)
                weather_df["date"] = pd.to_datetime(weather_df["date"])
                weather_df.set_index("date", inplace=True)

                logger.info(
                    f"✅ NASA POWER: {len(nasa_data)} registros diários "
                    f"para ({latitude}, {longitude})"
                )

            elif source == "openmeteo_archive":
                # Open-Meteo Archive (histórico desde 1950)
                from backend.api.services import OpenMeteoArchiveSyncAdapter

                adapter = OpenMeteoArchiveSyncAdapter()

                # Busca dados via novo adapter síncrono
                openmeteo_data = adapter.get_data_sync(
                    lat=latitude,
                    lon=longitude,
                    start_date=data_inicial_formatted,
                    end_date=data_final_adjusted,
                )

                if not openmeteo_data:
                    msg = (
                        f"Open-Meteo Archive: Nenhum dado "
                        f"para ({latitude}, {longitude})"
                    )
                    logger.warning(msg)
                    warnings_list.append(msg)
                    continue

                # Converte para DataFrame - TODAS as variáveis Open-Meteo
                weather_df = pd.DataFrame(openmeteo_data)
                weather_df["date"] = pd.to_datetime(weather_df["date"])
                weather_df.set_index("date", inplace=True)

                # Harmonizar variáveis OpenMeteo → NASA format para ETo
                # ETo: T2M_MAX, T2M_MIN, T2M (mean), RH2M, WS2M,
                #      ALLSKY_SFC_SW_DWN, PRECTOTCORR
                harmonization = {
                    "temperature_2m_max": "T2M_MAX",
                    "temperature_2m_min": "T2M_MIN",
                    "temperature_2m_mean": "T2M",  # NASA usa T2M para média
                    "relative_humidity_2m_mean": "RH2M",
                    "wind_speed_2m_mean": "WS2M",
                    "shortwave_radiation_sum": "ALLSKY_SFC_SW_DWN",
                    "precipitation_sum": "PRECTOTCORR",
                }

                for openmeteo_var, nasa_var in harmonization.items():
                    if openmeteo_var in weather_df.columns:
                        weather_df[nasa_var] = weather_df[openmeteo_var]

                logger.info(
                    f"✅ Open-Meteo Archive: {len(openmeteo_data)} "
                    f"registros diários para ({latitude}, {longitude})"
                )

            elif source == "openmeteo_forecast":
                # Open-Meteo Forecast (previsão + recent: -30d a +5d)
                from backend.api.services import OpenMeteoForecastSyncAdapter

                adapter = OpenMeteoForecastSyncAdapter()

                # Busca dados via adapter síncrono (aceita start/end date)
                forecast_data = adapter.get_data_sync(
                    lat=latitude,
                    lon=longitude,
                    start_date=data_inicial_formatted,
                    end_date=data_final_formatted,
                )

                if not forecast_data:
                    msg = (
                        f"Open-Meteo Forecast: Nenhum dado "
                        f"para ({latitude}, {longitude})"
                    )
                    logger.warning(msg)
                    warnings_list.append(msg)
                    continue

                # Converte para DataFrame - TODAS as variáveis Open-Meteo
                weather_df = pd.DataFrame(forecast_data)
                weather_df["date"] = pd.to_datetime(weather_df["date"])
                weather_df.set_index("date", inplace=True)

                # Harmonizar variáveis OpenMeteo → NASA format para ETo
                # ETo: T2M_MAX, T2M_MIN, T2M (mean), RH2M, WS2M,
                # ALLSKY_SFC_SW_DWN, PRECTOTCORR
                harmonization = {
                    "temperature_2m_max": "T2M_MAX",
                    "temperature_2m_min": "T2M_MIN",
                    "temperature_2m_mean": "T2M",  # NASA usa T2M para média
                    "relative_humidity_2m_mean": "RH2M",
                    "wind_speed_2m_mean": "WS2M",
                    "shortwave_radiation_sum": "ALLSKY_SFC_SW_DWN",
                    "precipitation_sum": "PRECTOTCORR",
                }

                # Renomear colunas existentes
                for openmeteo_var, nasa_var in harmonization.items():
                    if openmeteo_var in weather_df.columns:
                        weather_df[nasa_var] = weather_df[openmeteo_var]
                        logger.debug(
                            f"Harmonized: {openmeteo_var} → {nasa_var}"
                        )

                logger.info(
                    f"✅ Open-Meteo Forecast: {len(forecast_data)} "
                    f"registros diários para ({latitude}, {longitude})"
                )

            elif source == "met_norway":
                # MET Norway Locationforecast (Europa/Global, real-time,
                # horários convertidos em diários)
                from backend.api.services import (
                    METNorwayLocationForecastSyncAdapter as Adapter,
                )

                adapter = Adapter()

                # Verificar se está na cobertura (Europa/Global)
                if not adapter.health_check_sync():
                    msg = "MET Norway Locationforecast: Verificação falhou"
                    logger.warning(msg)
                    warnings_list.append(msg)
                    continue

                try:
                    # Busca dados via novo adapter síncrono
                    met_data = adapter.get_daily_data_sync(
                        lat=latitude,
                        lon=longitude,
                        start_date=data_inicial_formatted,
                        end_date=data_final_adjusted,
                    )

                    if not met_data:
                        msg = (
                            f"MET Norway Locationforecast: Nenhum dado "
                            f"para ({latitude}, {longitude})"
                        )
                        logger.warning(msg)
                        warnings_list.append(msg)
                        continue

                    # Obter variáveis recomendadas para a região
                    from backend.api.services import (
                        METNorwayClient,
                    )

                    recommended_vars = (
                        METNorwayClient.get_recommended_variables(
                            latitude, longitude
                        )
                    )

                    # Verificar se precipitação deve ser incluída
                    include_precipitation = (
                        "precipitation_sum" in recommended_vars
                    )

                    # Log da estratégia regional
                    if include_precipitation:
                        region_info = (
                            "NORDIC (1km + radar): "
                            "Incluindo precipitação (alta qualidade)"
                        )
                    else:
                        region_info = (
                            "GLOBAL (9km ECMWF): "
                            "Excluindo precipitação (usar Open-Meteo)"
                        )

                    logger.info(f"MET Norway Locationforecast - {region_info}")

                    # Converte para DataFrame - FILTRA variáveis por região
                    data_records = []
                    for record in met_data:
                        record_dict = {
                            "date": record.date,
                            # Temperaturas (sempre incluídas)
                            "temperature_2m_max": record.temp_max,
                            "temperature_2m_min": record.temp_min,
                            "temperature_2m_mean": record.temp_mean,
                            # Umidade (sempre incluída)
                            "relative_humidity_2m_mean": (
                                record.humidity_mean
                            ),
                        }

                        # Precipitação: apenas para região Nordic
                        if include_precipitation:
                            record_dict["precipitation_sum"] = (
                                record.precipitation_sum
                            )
                        # Else: omitir precipitação (será None ou ignorada)

                        data_records.append(record_dict)

                    weather_df = pd.DataFrame(data_records)
                    weather_df["date"] = pd.to_datetime(weather_df["date"])
                    weather_df.set_index("date", inplace=True)

                    # Adicionar atribuição CC-BY 4.0 aos warnings
                    warnings_list.append(
                        "📌 Dados MET Norway: CC-BY 4.0 - Atribuição requerida"  # noqa: E501
                    )

                    # Log de variáveis incluídas
                    logger.info(
                        "MET Norway Locationforecast: %d registros (%s, %s), "
                        "variáveis: %s",
                        len(met_data),
                        latitude,
                        longitude,
                        list(weather_df.columns),
                    )

                except ValueError as e:
                    msg = (
                        f"MET Norway Locationforecast: fora da cobertura - "
                        f"{str(e)}"
                    )
                    logger.warning(msg)
                    warnings_list.append(msg)
                    continue

            elif source == "nws_forecast":
                # NWS Forecast (USA, previsões)
                from backend.api.services import NWSDailyForecastSyncAdapter

                adapter = NWSDailyForecastSyncAdapter()

                # Verificar se está na cobertura (USA Continental)
                if not adapter.health_check_sync():
                    msg = "NWS Forecast: Verificação falhou"
                    logger.warning(msg)
                    warnings_list.append(msg)
                    continue

                try:
                    # Busca dados via adapter síncrono
                    nws_forecast_data = adapter.get_daily_data_sync(
                        lat=latitude,
                        lon=longitude,
                        start_date=data_inicial_formatted,
                        end_date=data_final_adjusted,
                    )

                    if not nws_forecast_data:
                        msg = (
                            f"NWS Forecast: Nenhum dado para "
                            f"({latitude}, {longitude})"
                        )
                        logger.warning(msg)
                        warnings_list.append(msg)
                        continue

                    # Converte para DataFrame - variáveis NWS Forecast
                    data_records = []
                    for record in nws_forecast_data:
                        data_records.append(
                            {
                                "date": record.date,
                                # Temperaturas
                                "temperature_2m_max": record.temp_max,
                                "temperature_2m_min": record.temp_min,
                                "temperature_2m_mean": record.temp_mean,
                                # Umidade
                                "relative_humidity_2m_mean": (
                                    record.humidity_mean
                                ),
                                # Vento
                                "wind_speed_10m_max": record.wind_speed_max,
                                "wind_speed_10m_mean": record.wind_speed_mean,
                                # Precipitação
                                "precipitation_sum": record.precipitation_sum,
                            }
                        )

                    weather_df = pd.DataFrame(data_records)
                    weather_df["date"] = pd.to_datetime(weather_df["date"])
                    weather_df.set_index("date", inplace=True)

                    logger.info(
                        "NWS Forecast: %d registros (%s, %s)",
                        len(nws_forecast_data),
                        latitude,
                        longitude,
                    )

                except ValueError as e:
                    msg = f"NWS Forecast: fora da cobertura USA - {str(e)}"
                    logger.warning(msg)
                    warnings_list.append(msg)
                    continue

            elif source == "nws_stations":
                # NWS Stations (USA, estações)
                from backend.api.services import NWSStationsSyncAdapter

                adapter = NWSStationsSyncAdapter()

                # Verificar se está na cobertura (USA Continental)
                if not adapter.health_check_sync():
                    msg = "NWS Stations: Verificação falhou"
                    logger.warning(msg)
                    warnings_list.append(msg)
                    continue

                try:
                    # Busca dados via novo adapter síncrono
                    nws_data = adapter.get_daily_data_sync(
                        lat=latitude,
                        lon=longitude,
                        start_date=data_inicial_formatted,
                        end_date=data_final_adjusted,
                    )

                    if not nws_data:
                        msg = (
                            f"NWS Stations: Nenhum dado para "
                            f"({latitude}, {longitude})"
                        )
                        logger.warning(msg)
                        warnings_list.append(msg)
                        continue

                    # Converte para DataFrame - variáveis disponíveis do NWS
                    data_records = []
                    for record in nws_data:
                        data_records.append(
                            {
                                "date": record.date,
                                # Temperaturas
                                "temp_celsius": record.temp_mean,
                                # Umidade
                                "humidity_percent": record.humidity,
                                # Vento
                                "wind_speed_ms": record.wind_speed,
                                # Precipitação
                                "precipitation_mm": record.precipitation,
                            }
                        )

                    weather_df = pd.DataFrame(data_records)
                    weather_df["date"] = pd.to_datetime(weather_df["date"])
                    weather_df.set_index("date", inplace=True)

                    logger.info(
                        "NWS Stations: %d registros (%s, %s)",
                        len(nws_data),
                        latitude,
                        longitude,
                    )

                except ValueError as e:
                    msg = f"NWS Stations: fora da cobertura USA - {str(e)}"
                    logger.warning(msg)
                    warnings_list.append(msg)
                    continue

        except Exception as e:
            logger.error(
                f"{source}: erro ao baixar dados: {str(e)}",
                exc_info=True,  # Mostra traceback completo
            )
            warnings_list.append(f"{source}: erro ao baixar dados: {str(e)}")
            continue

        # Valida DataFrame
        if weather_df is None or weather_df.empty:
            msg = (
                f"Nenhum dado obtido de {source} para "
                f"({latitude}, {longitude}) "
                f"entre {data_inicial} e {data_final}"
            )
            logger.warning(msg)
            warnings_list.append(msg)
            continue

        # Não padronizar colunas - preservar nomes nativos das APIs
        # Cada API retorna suas próprias variáveis específicas
        # Validação será feita em data_preprocessing.py com limits apropriados
        weather_df = weather_df.replace(-999.00, np.nan)
        weather_df = weather_df.dropna(how="all", subset=weather_df.columns)

        # Verifica quantidade de dados
        dias_retornados = (
            weather_df.index.max() - weather_df.index.min()
        ).days + 1
        if dias_retornados < period_days:
            msg = (
                f"{source}: obtidos {dias_retornados} dias "
                f"(solicitados: {period_days})"
            )
            warnings_list.append(msg)

        # Verifica dados faltantes
        perc_faltantes = weather_df.isna().mean() * 100
        nomes_variaveis = {
            # NASA POWER
            "ALLSKY_SFC_SW_DWN": "Radiação Solar (MJ/m²/dia)",
            "PRECTOTCORR": "Precipitação Total (mm)",
            "T2M_MAX": "Temperatura Máxima (°C)",
            "T2M_MIN": "Temperatura Mínima (°C)",
            "T2M": "Temperatura Média (°C)",
            "RH2M": "Umidade Relativa (%)",
            "WS2M": "Velocidade do Vento (m/s)",
            # Open-Meteo (Archive & Forecast)
            "temperature_2m_max": "Temperatura Máxima (°C)",
            "temperature_2m_min": "Temperatura Mínima (°C)",
            "temperature_2m_mean": "Temperatura Média (°C)",
            "relative_humidity_2m_max": "Umidade Relativa Máxima (%)",
            "relative_humidity_2m_min": "Umidade Relativa Mínima (%)",
            "relative_humidity_2m_mean": "Umidade Relativa Média (%)",
            "wind_speed_10m_mean": "Velocidade Média do Vento (m/s)",
            "wind_speed_10m_max": "Velocidade Máxima do Vento (m/s)",
            "shortwave_radiation_sum": "Radiação Solar (MJ/m²/dia)",
            "precipitation_sum": "Precipitação Total (mm)",
            "et0_fao_evapotranspiration": "ETo FAO-56 (mm/dia)",
            # NWS Stations
            "temp_celsius": "Temperatura (°C)",
            "humidity_percent": "Umidade Relativa (%)",
            "wind_speed_ms": "Velocidade do Vento (m/s)",
            "precipitation_mm": "Precipitação (mm)",
        }

        for nome_var, porcentagem in perc_faltantes.items():
            if porcentagem > 25:
                var_portugues = nomes_variaveis.get(
                    str(nome_var), str(nome_var)
                )
                msg = (
                    f"{source}: {porcentagem:.1f}% faltantes em "
                    f"{var_portugues}. Será feita imputação."
                )
                warnings_list.append(msg)

        weather_data_sources.append(weather_df)
        logger.debug("%s: DataFrame obtido\n%s", source, weather_df)

    # Consolidar dados (fusão Kalman será feita em eto_services.py)
    if not weather_data_sources:
        msg = "Nenhuma fonte forneceu dados válidos"
        logger.error(msg)
        raise ValueError(msg)

    # Se múltiplas fontes, concatenar TODAS as medições
    # A fusão Kalman em eto_services.py aplicará pesos inteligentes
    if len(weather_data_sources) > 1:
        logger.info(
            f"Concatenando {len(weather_data_sources)} fontes "
            f"(fusão Kalman será aplicada em eto_services.py)"
        )
        weather_data = pd.concat(weather_data_sources, axis=0)
        # MANTER duplicatas de datas - cada linha representa 1 fonte
        # Fusão Kalman processará todas as medições
        logger.info(
            f"Total de {len(weather_data)} medições de "
            f"{len(weather_data_sources)} fontes para fusão"
        )
    else:
        weather_data = weather_data_sources[0]

    # Validação final - aceitar todas as variáveis das APIs
    # Não mais restringir apenas às variáveis NASA POWER
    # Validação física será feita em data_preprocessing.py

    logger.info("Dados finais obtidos com sucesso")
    logger.debug("DataFrame final:\n%s", weather_data)
    return weather_data, warnings_list
