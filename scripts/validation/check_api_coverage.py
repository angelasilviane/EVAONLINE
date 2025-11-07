#!/usr/bin/env python3
"""
Script para verificar se TODAS as variáveis retornadas por cada API específica
têm limites físicos definidos em data_preprocessing.py
"""

import re
from pathlib import Path

from loguru import logger


def check_api_specific_variables():
    logger.info("🔍 VERIFICAÇÃO POR API: TODAS AS VARIÁVEIS RETORNADAS")
    logger.info("=" * 80)

    # 1. NASA POWER - variáveis retornadas no data_download.py
    nasa_variables = [
        "T2M_MAX",
        "T2M_MIN",
        "T2M",
        "RH2M",
        "WS2M",
        "ALLSKY_SFC_SW_DWN",
        "PRECTOTCORR",
    ]
    logger.info(f"📊 NASA POWER: {len(nasa_variables)} variáveis retornadas")
    for var in nasa_variables:
        logger.info(f"  ✅ {var}")

    # 2. Open-Meteo Archive/Forecast - TODAS as variáveis
    # retornadas no data_download.py
    openmeteo_variables = [
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "relative_humidity_2m_max",
        "relative_humidity_2m_mean",
        "relative_humidity_2m_min",
        "wind_speed_10m_max",
        "wind_speed_10m_mean",
        "shortwave_radiation_sum",
        "daylight_duration",
        "sunshine_duration",
        "precipitation_sum",
        "et0_fao_evapotranspiration",
    ]
    logger.info(
        f"\n🌤️ Open-Meteo Archive/Forecast: " f"{len(openmeteo_variables)} variáveis retornadas"
    )
    for var in openmeteo_variables:
        logger.info(f"  ✅ {var}")

    # 3. MET Norway Locationforecast - variáveis retornadas
    met_locationforecast_variables = [
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "wind_speed_10m_max",
        "wind_speed_10m_mean",
        "shortwave_radiation_sum",
        "precipitation_sum",
        "pressure_mean_sea_level",
    ]
    logger.info(
        f"\n🇳🇴 MET Norway Locationforecast: "
        f"{len(met_locationforecast_variables)} variáveis retornadas"
    )
    for var in met_locationforecast_variables:
        logger.info(f"  ✅ {var}")

    # 4. MET Norway FROST - ainda não implementado
    frost_variables = []  # Ainda não implementado
    logger.info(f"\n🏔️ MET Norway FROST: {len(frost_variables)} variáveis " "(não implementado)")

    # 5. NWS Forecast - ainda não implementado
    nws_forecast_variables = []  # Ainda não implementado
    logger.info(f"\n🇺🇸 NWS Forecast: {len(nws_forecast_variables)} variáveis " "(não implementado)")

    # 6. NWS Stations - variáveis retornadas
    nws_stations_variables = [
        "temp_celsius",
        "humidity_percent",
        "wind_speed_ms",
        "precipitation_mm",
    ]
    logger.info(f"\n🇺🇸 NWS Stations: {len(nws_stations_variables)} variáveis " "retornadas")
    for var in nws_stations_variables:
        logger.info(f"  ✅ {var}")

    # Total retornado por todas as APIs implementadas
    all_returned = (
        nasa_variables
        + openmeteo_variables
        + met_locationforecast_variables
        + frost_variables
        + nws_forecast_variables
        + nws_stations_variables
    )
    logger.info("\n📈 TOTAL RETORNADO PELAS APIs: " f"{len(all_returned)} variáveis")

    # Verificar limites no data_preprocessing.py
    backend_path = (
        Path(__file__).parent.parent.parent
        / "backend"
        / "core"
        / "data_processing"
        / "data_preprocessing.py"
    )
    with open(backend_path, "r") as f:
        pp_content = f.read()

    limits_match = re.search(r"limits = \{(.*?)\}", pp_content, re.DOTALL)
    variables_with_limits = set()
    if limits_match:
        limits_content = limits_match.group(1)
        limit_matches = re.findall(r'"([^"]+)":', limits_content)
        variables_with_limits = set(limit_matches)

    logger.info("🛡️ VARIÁVEIS COM LIMITES DEFINIDOS: " f"{len(variables_with_limits)}")

    # Verificar cobertura por API
    apis = {
        "NASA POWER": nasa_variables,
        "Open-Meteo": openmeteo_variables,
        "MET Norway Locationforecast": met_locationforecast_variables,
        "MET Norway FROST": frost_variables,
        "NWS Forecast": nws_forecast_variables,
        "NWS Stations": nws_stations_variables,
    }

    total_missing = 0
    total_extra = 0

    for api_name, api_vars in apis.items():
        if not api_vars:  # Pular APIs não implementadas
            continue

        api_vars_set = set(api_vars)
        covered = api_vars_set.intersection(variables_with_limits)
        missing = api_vars_set - variables_with_limits

        logger.info(f"\n🔍 {api_name}:")
        logger.info(
            f"  📊 Retornadas: {len(api_vars)} | "
            f"Cobertas: {len(covered)} | Faltando: {len(missing)}"
        )

        if missing:
            logger.info("  ❌ FALTANDO LIMITES:")
            for var in sorted(missing):
                logger.info(f"    ❌ {var}")
            total_missing += len(missing)
        else:
            logger.info("  ✅ TODAS as variáveis têm limites!")

    # Verificar limites extras (não usados por nenhuma API)
    all_returned_set = set(all_returned)
    extra_limits = variables_with_limits - all_returned_set

    logger.info("\n⚠️ LIMITES PARA VARIÁVEIS NÃO RETORNADAS: " f"{len(extra_limits)}")
    if extra_limits:
        for var in sorted(extra_limits):
            logger.info(f"  ⚠️ {var}")
        total_extra = len(extra_limits)

    # Resumo final
    logger.info(f"\n{'='*80}")
    logger.info("📋 RESUMO FINAL:")
    logger.info(f"  ✅ Variáveis retornadas pelas APIs: {len(all_returned)}")
    logger.info(f"  🛡️ Variáveis com limites definidos: " f"{len(variables_with_limits)}")
    logger.info(f"  ❌ Variáveis faltando limites: {total_missing}")
    logger.info(f"  ⚠️ Limites para variáveis não retornadas: {total_extra}")

    if total_missing == 0:
        logger.info("\n🎉 SUCESSO: TODAS as variáveis retornadas pelas APIs " "têm limites!")
    else:
        logger.info(f"\n❌ FALHA: {total_missing} variáveis ainda precisam " "de limites!")


if __name__ == "__main__":
    check_api_specific_variables()
