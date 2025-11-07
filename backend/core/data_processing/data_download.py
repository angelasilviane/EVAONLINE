from datetime import datetime, timedelta
from typing import List, Tuple, Union

import numpy as np
import pandas as pd
from celery import shared_task
from loguru import logger


def classify_request_type(data_inicial: datetime, data_final: datetime) -> str:
    """
    Classifica requisição: histórico ou atual/forecast.

    Regra: Se data_inicial <= hoje - 30 dias → HISTÓRICO
           Senão → ATUAL/FORECAST

    Args:
        data_inicial: Data inicial da requisição
        data_final: Data final da requisição

    Returns:
        "historical" ou "current"
    """
    threshold = datetime.now() - timedelta(days=30)

    # Comparar apenas as datas (sem horários)
    data_inicial_date = (
        data_inicial.date() if hasattr(data_inicial, "date") else data_inicial
    )
    threshold_date = (
        threshold.date() if hasattr(threshold, "date") else threshold
    )

    return "historical" if data_inicial_date <= threshold_date else "current"


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

    Fontes suportadas:
    - "nasa_power": NASA POWER (global, 1981+, domínio público)
    - "openmeteo_archive": Open-Meteo Archive (global, 1950+, CC BY 4.0)
    - "openmeteo_forecast": Open-Meteo Forecast (global, 16d, CC BY 4.0)
    - "met_norway": MET Norway Locationforecast
      (global, real-time, CC BY 4.0)
    - "nws_forecast": NWS Forecast (USA, previsões, domínio público)
    - "nws_stations": NWS Stations (USA, estações, domínio público)
    - "data fusion": Fusiona múltiplas fontes disponíveis (Kalman Ensemble)

    A validação dinâmica verifica automaticamente quais fontes estão disponíveis
    para as coordenadas específicas, rejeitando fontes indisponíveis.

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

    # Validação das coordenadas
    if not (-90 <= latitude <= 90):
        msg = "Latitude deve estar entre -90 e 90 graus"
        logger.error(msg)
        raise ValueError(msg)
    if not (-180 <= longitude <= 180):
        msg = "Longitude deve estar entre -180 e 180 graus"
        logger.error(msg)
        raise ValueError(msg)

    # Validação das datas
    try:
        data_inicial_formatted = pd.to_datetime(data_inicial)
        data_final_formatted = pd.to_datetime(data_final)
    except ValueError:
        msg = "As datas devem estar no formato 'AAAA-MM-DD'"
        logger.error(msg)
        raise ValueError(msg)

    # Verifica se é uma data válida (não futura para dados históricos)
    data_atual = pd.to_datetime(datetime.now().date())
    if data_inicial_formatted > data_atual:
        msg = (
            "A data inicial não pode ser futura para dados históricos. "
            f"Data atual: {data_atual.strftime('%Y-%m-%d')}"
        )
        logger.error(msg)
        raise ValueError(msg)

    # Verifica ordem das datas
    if data_final_formatted < data_inicial_formatted:
        msg = "A data final deve ser posterior à data inicial"
        logger.error(msg)
        raise ValueError(msg)

    # Verifica período mínimo (validações específicas por fonte depois)
    period_days = (data_final_formatted - data_inicial_formatted).days + 1
    if period_days < 1:
        msg = "O período deve ter pelo menos 1 dia"
        logger.error(msg)
        raise ValueError(msg)

    # Classificar tipo de requisição (histórico vs atual/forecast)
    request_type = classify_request_type(
        data_inicial_formatted, data_final_formatted
    )
    logger.info(f"Tipo de requisição: {request_type}")

    # Validações de período por tipo de requisição
    if request_type == "current" and not (7 <= period_days <= 30):
        msg = "Dados atuais: período entre 7 e 30 dias"
        logger.error(msg)
        raise ValueError(msg)

    if request_type == "historical" and period_days > 90:
        msg = "Dados históricos: período máximo de 90 dias"
        logger.error(msg)
        raise ValueError(msg)

    # Validação dinâmica de fontes disponíveis para a localização
    source_manager = ClimateSourceManager()
    available_sources = source_manager.get_available_sources_for_location(
        lat=latitude,
        lon=longitude,
        exclude_non_commercial=True,  # Exclui fontes não-comerciais do mapa
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
        requested = [str(data_source).lower()]

    # Validate requested sources
    for req in requested:
        if req not in valid_sources:
            msg = (
                f"Fonte inválida: {data_source}. Use: "
                f"{', '.join(valid_sources)}"
            )
            logger.error(msg)
            raise ValueError(msg)

        # Para fontes específicas, verificar se estão disponíveis na localização
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

    # Define sources to query
    if "data fusion" in requested:
        # Data Fusion combina múltiplas fontes com Kalman Ensemble
        # Usar apenas fontes disponíveis para esta localização
        sources = [
            src
            for src in [
                "openmeteo_archive",  # Prioridade 1: histórico (1940+)
                "nasa_power",  # Prioridade 2: confiável (1981+)
                "met_norway",  # Prioridade 3: Global, 5d
                "nws_forecast",  # Prioridade 4: USA, tempo real
                "openmeteo_forecast",  # Prioridade 5: Futuro, 5 dias
                "nws_stations",  # Prioridade 6: USA stations
            ]
            if src in available_source_ids
        ]

        if not sources:
            msg = (
                f"Nenhuma fonte disponível para as coordenadas "
                f"({latitude}, {longitude}). Fontes disponíveis globalmente: "
                f"{available_source_ids}"
            )
            logger.error(msg)
            raise ValueError(msg)

        logger.info(
            "Data Fusion selecionada, coletando de %d fontes disponíveis: %s",
            len(sources),
            sources,
        )
    else:
        sources = requested
        logger.info(f"Fonte(s) selecionada(s): {sources}")

    current_date = pd.to_datetime(datetime.now().date())
    weather_data_sources: List[pd.DataFrame] = []
    for source in sources:
        # Validações específicas por fonte de dados
        if source == "nasa_power":
            # NASA POWER: dados históricos desde 1981, sem dados futuros
            # Padrão EVAonline: >= 1990-01-01
            nasa_start_limit = pd.to_datetime("1990-01-01")
            if data_inicial_formatted < nasa_start_limit:
                msg = "NASA POWER: data inicial deve ser >= 1990-01-01"
                logger.error(msg)
                raise ValueError(msg)
            if data_final_formatted > current_date:
                warnings_list.append(
                    "NASA POWER: truncando para data atual (sem dados futuros)"
                )

        elif source == "openmeteo_archive":
            # Open-Meteo Archive: dados históricos desde 1950
            # Padrão EVAonline: >= 1990-01-01
            oma_start_limit = pd.to_datetime("1990-01-01")
            if data_inicial_formatted < oma_start_limit:
                msg = "Open-Meteo Archive: data inicial deve ser >= 1990-01-01"
                logger.error(msg)
                raise ValueError(msg)

        elif source == "openmeteo_forecast":
            # Open-Meteo Forecast: últimos 90 dias + próximos 16 dias
            # Padrão EVAonline: últimos 30 dias + próximos 5 dias
            min_date = current_date - pd.Timedelta(days=30)
            if data_inicial_formatted < min_date:
                msg = (
                    f"Open-Meteo Forecast: data inicial deve ser >= {min_date.strftime('%Y-%m-%d')} "
                    "(máximo 30 dias no passado)"
                )
                logger.error(msg)
                raise ValueError(msg)

            forecast_limit = current_date + pd.Timedelta(days=5)
            if data_final_formatted > forecast_limit:
                msg = (
                    "Open-Meteo Forecast: data final deve ser <= hoje + 5 dias"
                )
                logger.error(msg)
                raise ValueError(msg)

        elif source == "met_norway":
            # MET Norway: apenas forecast, hoje até hoje + 9 dias
            # Padrão EVAonline: data atual + 5 dias
            if data_inicial_formatted < current_date:
                msg = (
                    "MET Norway: data inicial deve ser >= hoje (sem histórico)"
                )
                logger.error(msg)
                raise ValueError(msg)

            forecast_limit = current_date + pd.Timedelta(days=5)
            if data_final_formatted > forecast_limit:
                msg = "MET Norway: data final deve ser <= hoje + 5 dias"
                logger.error(msg)
                raise ValueError(msg)

        elif source == "nws_forecast":
            # NWS Forecast: apenas forecast, hoje até hoje + 5
            # Padrão EVAonline: data atual + 5 dias
            if data_inicial_formatted < current_date:
                msg = "NWS Forecast: data inicial deve ser >= hoje (sem histórico)"
                logger.error(msg)
                raise ValueError(msg)

            forecast_limit = current_date + pd.Timedelta(days=5)
            if data_final_formatted > forecast_limit:
                msg = "NWS Forecast: data final deve ser <= hoje + 5 dias"
                logger.error(msg)
                raise ValueError(msg)

        elif source == "nws_stations":
            # NWS Stations: dados reais, apenas hoje-1 até hoje
            min_date = current_date - pd.Timedelta(days=1)
            if data_inicial_formatted < min_date:
                msg = (
                    f"NWS Stations: data inicial deve ser >= {min_date.strftime('%Y-%m-%d')} "
                    "(dados reais das estações, máximo 1 dia)"
                )
                logger.error(msg)
                raise ValueError(msg)

            if data_final_formatted > current_date:
                msg = (
                    "NWS Stations: data final deve ser <= hoje (sem forecast)"
                )
                logger.error(msg)
                raise ValueError(msg)

                # Limite máximo: 1 dia
            if period_days > 1:
                msg = "NWS Stations: período máximo de 1 dia (dados reais)"
                logger.error(msg)
                raise ValueError(msg)

        # Adjust end date for NASA POWER (no future data)
        data_final_adjusted = (
            min(data_final_formatted, current_date)
            if source == "nasa_power"
            else data_final_formatted
        )
        if (
            data_final_adjusted < data_final_formatted
            and source == "nasa_power"
        ):
            warnings_list.append(
                f"NASA POWER data truncated to "
                f"{data_final_adjusted.strftime('%Y-%m-%d')} "
                "as it does not provide future data."
            )

        # Download data
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
                    "NASA POWER: obtidos %d registros para (%s, %s)",
                    len(nasa_data),
                    latitude,
                    longitude,
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

                logger.info(
                    "Open-Meteo Archive: obtidos %d registros para (%s, %s)",
                    len(openmeteo_data),
                    latitude,
                    longitude,
                )

            elif source == "openmeteo_forecast":
                # Open-Meteo Forecast (previsão até 16 dias)
                from backend.api.services import OpenMeteoForecastSyncAdapter

                adapter = OpenMeteoForecastSyncAdapter()

                # Calcular dias até data final
                days_to_forecast = (
                    data_final_adjusted - pd.Timestamp.now()
                ).days + 1
                # 1-16 dias
                days_to_forecast = max(1, min(days_to_forecast, 16))

                # Busca dados via novo adapter síncrono
                forecast_data = adapter.get_forecast_sync(
                    lat=latitude,
                    lon=longitude,
                    days=days_to_forecast,
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

                logger.info(
                    "Open-Meteo Forecast: obtidos %d registros para (%s, %s)",
                    len(forecast_data),
                    latitude,
                    longitude,
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
                        METNorwayLocationForecastClient,
                    )

                    recommended_vars = METNorwayLocationForecastClient.get_recommended_variables(  # noqa: E501
                        latitude, longitude
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
            logger.error("%s: erro ao baixar dados: %s", source, str(e))
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

    # Realiza fusão se necessário
    weather_data = None  # ✅ Inicializar antes do uso

    if "data fusion" in requested:
        if len(weather_data_sources) < 2:
            msg = "São necessárias pelo menos duas fontes válidas para fusão"
            logger.error(msg)
            raise ValueError(msg)

        try:
            # Usar KalmanEnsembleStrategy para fusão
            # (novo, com histórico PostgreSQL)
            from backend.core.data_processing.kalman_ensemble import (
                KalmanEnsembleStrategy,
            )

            # Preparar medições atuais consolidadas de todas as fontes
            current_measurements = {}

            # Consolidar dados de todas as fontes
            # (tomar médias onde disponível)
            for source_df in weather_data_sources:
                for col in source_df.columns:
                    if col not in current_measurements:
                        current_measurements[col] = []
                    # Pegar primeira data válida de cada coluna
                    valid_values = source_df[col].dropna()
                    if len(valid_values) > 0:
                        current_measurements[col].append(valid_values.iloc[0])

            # Calcular médias das medições consolidadas
            for key in current_measurements:
                if current_measurements[key]:
                    current_measurements[key] = np.mean(
                        current_measurements[key]
                    )
                else:
                    current_measurements[key] = np.nan

            # Adicionar metadados necessários para Kalman
            if (
                len(weather_data_sources) > 0
                and not weather_data_sources[0].empty
                and len(weather_data_sources[0].index) > 0
            ):
                first_date = weather_data_sources[0].index[0]
                current_measurements["date"] = first_date.strftime("%Y-%m-%d")
                current_measurements["latitude"] = latitude
                current_measurements["longitude"] = longitude
            else:
                # Fallback se não conseguir obter data
                current_date = pd.Timestamp.now().strftime("%Y-%m-%d")
                current_measurements["date"] = current_date
                current_measurements["latitude"] = latitude
                current_measurements["longitude"] = longitude

            # Executar fusão com KalmanEnsembleStrategy (sync wrapper)
            kalman_strategy = KalmanEnsembleStrategy(
                db_session=None, redis_client=None
            )
            fused_measurements = kalman_strategy.auto_fuse_sync(
                latitude=latitude,
                longitude=longitude,
                current_measurements=current_measurements,
            )

            # Converter resultado para DataFrame
            if fused_measurements:
                weather_data = pd.DataFrame([fused_measurements])
                weather_data.index = pd.to_datetime(
                    [current_measurements["date"]]
                )
                logger.info("Fusão Kalman Ensemble concluída com sucesso")
            else:
                # Fallback para primeira fonte se Kalman falhar
                weather_data = weather_data_sources[0]
                logger.warning("Kalman falhou, usando fonte original")

        except Exception as e:
            msg = f"Erro na fusão de dados: {str(e)}"
            logger.error(msg)
            # Fallback para primeira fonte
            weather_data = weather_data_sources[0]
            warnings_list.append(
                f"Fusão Kalman falhou, usando fonte original: {str(e)}"
            )
    else:
        if not weather_data_sources:
            msg = "Nenhuma fonte forneceu dados válidos"
            logger.error(msg)
            raise ValueError(msg)
        weather_data = weather_data_sources[0]

    # Validação final - aceitar todas as variáveis das APIs
    # Não mais restringir apenas às variáveis NASA POWER
    # Validação física será feita em data_preprocessing.py

    logger.info("Dados finais obtidos com sucesso")
    logger.debug("DataFrame final:\n%s", weather_data)
    return weather_data, warnings_list
