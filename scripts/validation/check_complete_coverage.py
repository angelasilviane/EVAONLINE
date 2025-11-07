#!/usr/bin/env python3
"""
Script para verificar se TODAS as variáveis climáticas retornadas pelas APIs
têm limites físicos definidos em data_preprocessing.py
"""

import re
from pathlib import Path

from loguru import logger


def check_all_api_variables():
    logger.info("🔍 VERIFICAÇÃO COMPLETA: TODAS AS VARIÁVEIS DAS APIs")
    logger.info("=" * 80)

    # 1. NASA POWER - 7 variáveis
    nasa_variables = [
        "T2M_MAX",
        "T2M_MIN",
        "T2M",
        "RH2M",
        "WS2M",
        "ALLSKY_SFC_SW_DWN",
        "PRECTOTCORR",
    ]
    logger.info(f"📊 NASA POWER: {len(nasa_variables)} variáveis")
    for var in nasa_variables:
        logger.info(f"  ✅ {var}")

    # 2. Open-Meteo - TODAS as 13 variáveis possíveis
    openmeteo_variables = [
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_max",
        "wind_speed_10m_mean",
        "shortwave_radiation_sum",
        "relative_humidity_2m_max",
        "relative_humidity_2m_mean",
        "relative_humidity_2m_min",
        "daylight_duration",
        "sunshine_duration",
        "et0_fao_evapotranspiration",
    ]
    logger.info("\n🌤️ Open-Meteo Archive/Forecast: " f"{len(openmeteo_variables)} variáveis")
    for var in openmeteo_variables:
        logger.info(f"  ✅ {var}")

    # 3. MET Norway Locationforecast - variáveis possíveis
    met_norway_variables = [
        "temp_mean",
        "temp_min",
        "temp_max",
        "humidity_mean",
        "wind_speed_max",
        "wind_speed_mean",
        "solar_radiation_sum",
        "precipitation_sum",
        "pressure_mean_sea_level",
    ]
    logger.info("\n🇳🇴 MET Norway Locationforecast: " f"{len(met_norway_variables)} variáveis")
    for var in met_norway_variables:
        logger.info(f"  ✅ {var}")

    # 4. MET Norway FROST - variáveis possíveis (só na Noruega)
    frost_variables = ["temp_celsius", "humidity_percent"]
    logger.info(f"\n🏔️ MET Norway FROST: {len(frost_variables)} variáveis")
    for var in frost_variables:
        logger.info(f"  ✅ {var}")

    # 5. NWS - 4 variáveis
    nws_variables = ["temp_celsius", "humidity_percent", "wind_speed_ms", "precipitation_mm"]
    logger.info("\n🇺🇸 NWS Forecast/Stations: " f"{len(nws_variables)} variáveis")
    for var in nws_variables:
        logger.info(f"  ✅ {var}")

    # Total teórico
    all_possible = (
        nasa_variables
        + openmeteo_variables
        + met_norway_variables
        + frost_variables
        + nws_variables
    )
    logger.info("\n📈 TOTAL TEÓRICO: " f"{len(all_possible)} variáveis climáticas possíveis")

    # Verificar quais têm limites no data_preprocessing.py
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

    # Verificar cobertura
    covered = variables_with_limits.intersection(set(all_possible))
    missing = set(all_possible) - variables_with_limits

    logger.info(
        "✅ COBERTURA: "
        f"{len(covered)}/{len(all_possible)} variáveis "
        f"({len(covered)/len(all_possible)*100:.1f}%)"
    )

    if missing:
        logger.info(f"\n❌ VARIÁVEIS FALTANDO LIMITES ({len(missing)}):")
        for var in sorted(missing):
            logger.info(f"  ❌ {var}")
    else:
        logger.info("\n🎉 SUCESSO: TODAS as variáveis têm limites físicos!")

    # Verificar se há limites extras (não usados)
    extra_limits = variables_with_limits - set(all_possible)
    if extra_limits:
        logger.info("\n⚠️ LIMITES PARA VARIÁVEIS NÃO USADAS " f"({len(extra_limits)}):")
        for var in sorted(extra_limits):
            logger.info(f"  ⚠️ {var}")


if __name__ == "__main__":
    check_all_api_variables()
