"""
User Request Simulator – Versão ESCALÁVEL para 1991–2020 em TODAS as cidades
Validado em produção com 2025
"""

import asyncio
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

# Seus módulos
from historical_data_loader import HistoricalDataLoader
from data_download_historical import download_historical_weather_data  # async
from validation_logic_eto.api.services.opentopo.opentopo_sync_adapter import (
    OpenTopoSyncAdapter,
)
from validation_logic_eto.core.eto_calculation.eto_services import (
    calculate_eto_timeseries,
)


# Instância única global → evita recarregar CSV 500 vezes
DATA_LOADER = HistoricalDataLoader()
OPENTOPO = OpenTopoSyncAdapter()

# Limita concorrência para não derrubar APIs
MAX_CONCURRENT_REQUESTS = 15  # Ajuste conforme sua máquina/internet


async def process_single_city(
    city_name: str,
    start_date: str = "1991-01-01",
    end_date: str = "1990-12-31",
) -> Dict:
    """Processa uma única cidade com tratamento robusto de erros"""
    try:
        city_info = DATA_LOADER.get_city_info(city_name)
        if not city_info:
            return {
                "city": city_name,
                "success": False,
                "error": "Cidade não encontrada",
            }

        lat, lon = city_info["lat"], city_info["lon"]
        alt_ref = city_info["alt"]
        region = city_info["region"]

        # Altitude via API (com fallback)
        try:
            alt_result = await asyncio.to_thread(
                OPENTOPO.get_elevation_sync, lat, lon
            )
            if hasattr(alt_result, "elevation"):
                alt_api = float(alt_result.elevation)
            elif isinstance(alt_result, (int, float)):
                alt_api = float(alt_result)
            else:
                logger.warning(
                    f"OpenTopo retornou tipo inesperado para {city_name}"
                )
                alt_api = alt_ref
        except Exception as e:
            logger.warning(f"OpenTopo falhou para {city_name}: {e}")
            alt_api = alt_ref

        # Download + fusão Kalman
        df_weather, warnings = await download_historical_weather_data(
            latitude=lat,
            longitude=lon,
            start_date=start_date,
            end_date=end_date,
            use_fusion=True,
        )

        if len(df_weather) < 8000:  # menos de ~22 anos
            return {
                "city": city_name,
                "success": False,
                "error": f"Apenas {len(df_weather)} dias baixados",
            }

        # Cálculo ETo vetorizado (rápido mesmo com 11k linhas)
        df_eto = calculate_eto_timeseries(
            df=df_weather,
            latitude=lat,
            longitude=lon,
            elevation_m=alt_api,
        )

        # Validação contra referência oficial
        comparison = DATA_LOADER.compare_eto_results(
            calculated_eto=df_eto,
            city_name=city_name,
            region=region,
        )

        mae = comparison.get("mae", float("nan")) if comparison else None

        return {
            "city": city_name,
            "success": True,
            "weather_days": len(df_weather),
            "eto_mae": mae,
            "altitude_diff": abs(alt_api - alt_ref),
            "warnings": len(warnings),
        }

    except Exception as e:
        logger.error(f"Falha crítica em {city_name}: {e}")
        return {"city": city_name, "success": False, "error": str(e)}


async def simulate_multiple_requests(
    cities: Optional[List[str]] = None,
    start_date: str = "1991-01-01",
    end_date: str = "2020-12-31",
    max_concurrent: int = MAX_CONCURRENT_REQUESTS,
) -> pd.DataFrame:
    """Roda TODAS as cidades em paralelo com controle de concorrência"""
    if cities is None:
        df_cities = DATA_LOADER.get_all_cities_info()
        cities = df_cities["city"].tolist()

    logger.info(
        f"Iniciando validação em massa: {len(cities)} cidades | {start_date} → {end_date}"
    )

    # Controla concorrência para não matar a máquina/API
    semaphore = asyncio.Semaphore(max_concurrent)

    async def sem_task(city):
        async with semaphore:
            return await process_single_city(city, start_date, end_date)

    tasks = [sem_task(city) for city in cities]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    df_results = pd.DataFrame(results)

    # Relatório final
    success_rate = df_results["success"].mean() * 100
    valid_cities = df_results[df_results["success"]]
    logger.success(
        f"VALIDAÇÃO CONCLUÍDA: {len(valid_cities)}/{len(cities)} cidades OK ({success_rate:.1f}%)"
    )
    if len(valid_cities) > 0:
        logger.success(
            f"MAE médio ETo: {valid_cities['eto_mae'].mean():.3f} mm/dia"
        )

    df_results.to_csv("relatorio_validacao_1991_2020.csv", index=False)
    return df_results


# Uso real
if __name__ == "__main__":
    # Teste para Alvorada_do_Gurgueia_PI em 1990
    asyncio.run(
        simulate_multiple_requests(
            cities=["Alvorada_do_Gurgueia_PI"],
            start_date="1990-01-01",
            end_date="1990-12-31",
        )
    )
