"""
NWS Forecast Daily Sync Adapter

Adapter sincrono para nws_forecast_client.py (cliente assincrono).
Converte dados horarios do NWS Forecast em dados diarios agregados.

Este adapter:
- Wraps o NWSForecastClient assincrono em interface sincrona
- Gerencia event loop automaticamente
- Converte dados horarios em agregacoes diarias usando pandas
- Mantém compatibilidade com codigo sincrono existente

Coverage: USA Continental (-125°W to -66°W, 24°N to 49°N)
Extended: Alaska/Hawaii (18°N to 71°N)

License: US Government Public Domain
API Documentation: https://www.weather.gov/documentation/services-web-api

Related Files:
- nws_forecast_client.py: Cliente assincrono (base)
- nws_stations_sync_adapter.py: Adapter para estacoes/observacoes
"""

import asyncio
from datetime import datetime
from typing import List, Optional

import pandas as pd
from loguru import logger
from pydantic import BaseModel

from .nws_forecast_client import (
    create_nws_forecast_client,
)


class NWSDailyForecastRecord(BaseModel):
    """
    Registro diário de dados NWS Forecast.

    Formato de saida do adapter para compatibilidade com
    sistemas existentes que esperam dados diarios.

    Attributes:
        date: Data no formato YYYY-MM-DD (string)
        temp_max: Temperatura maxima (°C)
        temp_min: Temperatura minima (°C)
        temp_mean: Temperatura media (°C)
        humidity_mean: Umidade relativa media (%)
        wind_speed_max: Velocidade maxima do vento (m/s)
        wind_speed_mean: Velocidade media do vento (m/s)
        precipitation_sum: Precipitacao total (mm)
    """

    date: str
    temp_max: Optional[float] = None
    temp_min: Optional[float] = None
    temp_mean: Optional[float] = None
    humidity_mean: Optional[float] = None
    wind_speed_max: Optional[float] = None
    wind_speed_mean: Optional[float] = None
    precipitation_sum: Optional[float] = None


class NWSDailyForecastSyncAdapter:
    """
    Adapter síncrono para NWS Forecast com agregação diária.

    Converte previsões horárias em dados diários agregados de forma
    síncrona. Gerencia event loop automaticamente para
    compatibilidade com código síncrono.

    Este adapter:
        - Wraps NWSForecastClient (async) em interface síncrona
        - Cria/reusa event loop conforme necessário
        - Agrega dados horários em diários usando pandas
        - Remove timezone para compatibilidade com datas naive

    Métodos:
        - health_check_sync(): Verifica disponibilidade da API
        - get_daily_data_sync(): Obtém dados diários agregados
        - get_attribution(): Retorna informações de atribuição

    Exemplo:
        adapter = NWSDailyForecastSyncAdapter()
        if adapter.health_check_sync():
            data = adapter.get_daily_data_sync(
                39.7392, -104.9903,
                start_date, end_date
            )
    """

    def __init__(self):
        """Inicializar adapter com cliente NWS assincrono."""
        self.client = create_nws_forecast_client()

    def health_check_sync(self) -> bool:
        """
        Verificar se NWS API está acessível (sincrono).

        Cria event loop se necessário e executa health check
        do cliente assincrono de forma bloqueante.

        Returns:
            bool: True se API está funcionando, False caso contrário

        Exemplo:
            adapter = NWSDailyForecastSyncAdapter()
            if adapter.health_check_sync():
                print("NWS API disponível")
        """
        try:
            # Criar event loop se não existir
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Executar health check de forma síncrona
            result = loop.run_until_complete(self.client.health_check())
            return result.get("status") == "ok"
        except Exception as e:
            logger.error(f"NWS Forecast health check failed: {e}")
            return False

    def get_daily_data_sync(
        self, lat: float, lon: float, start_date: datetime, end_date: datetime
    ) -> List[NWSDailyForecastRecord]:
        """
        Obter dados diários agregados do NWS Forecast (sincrono).

        Obtém previsões horárias e agrega em dados diários usando pandas.
        Executa de forma síncrona criando/reusando event loop.

        Processo:
            1. Obter dados horários do cliente async
            2. Converter para DataFrame pandas
            3. Filtrar período solicitado (start_date a end_date)
            4. Agregar por dia usando resample('D')
            5. Calcular estatísticas (mean, max, min, sum)
            6. Retornar lista de NWSDailyForecastRecord

        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            start_date: Data inicial (datetime naive)
            end_date: Data final (datetime naive)

        Returns:
            List[NWSDailyForecastRecord]: Dados diários agregados
            Lista vazia se sem dados ou erro

        Raises:
            ValueError: Se coordenadas fora da cobertura USA

        Exemplo:
            adapter = NWSDailyForecastSyncAdapter()
            data = adapter.get_daily_data_sync(
                39.7392, -104.9903,
                datetime(2025, 11, 6),
                datetime(2025, 11, 10)
            )
            for record in data:
                print(f"{record.date}: {record.temp_max}°C")
        """
        try:
            # Criar event loop se não existir
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Executar de forma síncrona
            return loop.run_until_complete(
                self._get_daily_data_async(lat, lon, start_date, end_date)
            )
        except ValueError:
            # Re-raise validation errors (coverage, dates, etc)
            raise
        except Exception as e:
            logger.error(f"NWS Forecast data retrieval failed: {e}")
            return []

    async def _get_daily_data_async(
        self, lat: float, lon: float, start_date: datetime, end_date: datetime
    ) -> List[NWSDailyForecastRecord]:
        """
        Obter dados diários agregados de forma assíncrona.
        """
        try:
            # Obter dados horários do forecast
            forecast_data = await self.client.get_forecast_data(lat, lon)

            if not forecast_data:
                logger.warning(f"Nenhum dado de forecast para ({lat}, {lon})")
                return []

            # Converter para DataFrame para agregação
            records = []
            for item in forecast_data:
                records.append(
                    {
                        "timestamp": pd.to_datetime(item.timestamp),
                        "temp_celsius": item.temp_celsius,
                        "humidity_percent": item.humidity_percent,
                        "wind_speed_ms": item.wind_speed_ms,
                        "precipitation_mm": item.precip_mm,
                    }
                )

            if not records:
                return []

            df = pd.DataFrame(records)
            df.set_index("timestamp", inplace=True)

            # Remover timezone do index para comparação
            # (start_date e end_date são naive datetime)
            df.index = df.index.tz_localize(None)  # type: ignore

            # Filtrar período solicitado
            mask = (df.index >= start_date) & (df.index <= end_date)
            df_filtered = df[mask]

            if df_filtered.empty:
                logger.warning("Nenhum dado no período para NWS Forecast")
                return []

            # Agregar por dia
            daily_data = []

            # Agregar por dia usando resample
            daily_data = []

            # Resample para dados diários
            daily_grouped = df_filtered.resample("D")

            for date, group in daily_grouped:
                if len(group) > 0:  # Só processar se há dados
                    date_str = str(date)[:10]  # YYYY-MM-DD

                # Calcular agregados diários
                temp_col = group["temp_celsius"]
                humid_col = group["humidity_percent"]
                wind_col = group["wind_speed_ms"]
                precip_col = group["precipitation_mm"]

                record = NWSDailyForecastRecord(
                    date=date_str,
                    temp_max=(
                        temp_col.max() if temp_col.notna().any() else None
                    ),
                    temp_min=(
                        temp_col.min() if temp_col.notna().any() else None
                    ),
                    temp_mean=(
                        temp_col.mean() if temp_col.notna().any() else None
                    ),
                    humidity_mean=(
                        humid_col.mean() if humid_col.notna().any() else None
                    ),
                    wind_speed_max=(
                        wind_col.max() if wind_col.notna().any() else None
                    ),
                    wind_speed_mean=(
                        wind_col.mean() if wind_col.notna().any() else None
                    ),
                    precipitation_sum=(
                        precip_col.sum() if precip_col.notna().any() else None
                    ),
                )

                daily_data.append(record)

            logger.info(
                f"NWS Forecast: agregados {len(daily_data)} dias "
                f"de dados horários para ({lat}, {lon})"
            )

            return daily_data

        except ValueError:
            # Re-raise validation errors (coverage, dates, etc)
            raise
        except Exception as e:
            logger.error(f"Erro ao processar dados NWS Forecast: {e}")
            return []

    def get_attribution(self) -> str:
        """
        Retorna texto de atribuição dos dados NWS.

        Returns:
            str: Texto formatado com informações de atribuição
        """
        attr = self.client.get_attribution()
        return (
            f"{attr['source']} | "
            f"License: {attr['license']} | "
            f"API: {attr['api_docs']}"
        )
