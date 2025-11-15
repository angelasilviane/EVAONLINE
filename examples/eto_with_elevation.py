"""
Example: Complete ETo Calculation with OpenTopoData Integration.

Demonstra como usar elevação precisa do OpenTopoData
para cálculo de ETo FAO-56 mais preciso.
"""

import asyncio
from datetime import datetime, timedelta

from loguru import logger

from backend.api.services import (
    ElevationUtils,
    OpenMeteoForecastClient,
    OpenTopoClient,
)


async def calculate_eto_with_elevation(
    lat: float,
    lon: float,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """
    Calcula ETo considerando elevação precisa do OpenTopoData.

    Args:
        lat: Latitude
        lon: Longitude
        start_date: Data inicial
        end_date: Data final

    Returns:
        Dicionário com dados climáticos + fatores de elevação
    """
    # Inicializar clientes
    meteo_client = OpenMeteoForecastClient()
    topo_client = OpenTopoClient()

    try:
        # 1. Obter dados climáticos do Open-Meteo
        logger.info(f"Obtendo dados climáticos para ({lat}, {lon})...")
        climate_data = await meteo_client.get_daily_forecast(
            lat, lon, start_date, end_date
        )

        meteo_elevation = climate_data["location"]["elevation"]
        logger.info(f"Elevação Open-Meteo: {meteo_elevation}m")

        # 2. Obter elevação precisa do OpenTopoData
        logger.info("Obtendo elevação precisa do OpenTopoData...")
        topo_location = await topo_client.get_elevation(lat, lon)

        if topo_location:
            elevation = topo_location.elevation
            logger.info(
                f"Elevação OpenTopoData: {elevation}m "
                f"(dataset: {topo_location.dataset})"
            )

            diff = abs(elevation - meteo_elevation)
            logger.info(f"Diferença entre fontes: {diff:.1f}m")

        else:
            # Fallback para Open-Meteo
            elevation = meteo_elevation
            logger.warning("OpenTopoData indisponível, usando Open-Meteo")

        # 3. Calcular fatores de correção por elevação
        logger.info("Calculando fatores de correção FAO-56...")
        factors = ElevationUtils.get_elevation_correction_factor(elevation)

        logger.info(f"Pressão atmosférica: {factors['pressure']:.2f} kPa")
        logger.info(f"Constante psicrométrica: {factors['gamma']:.5f} kPa/°C")
        logger.info(f"Fator solar: {factors['solar_factor']:.4f}")

        # 4. Processar dados diários
        daily_results = []

        for day_data in climate_data["daily"]:
            # Ajustar radiação solar para elevação
            radiation_original = day_data.solar_radiation
            radiation_adjusted = (
                ElevationUtils.adjust_solar_radiation_for_elevation(
                    radiation_original,
                    elevation,
                )
            )

            # Compilar resultado do dia
            daily_results.append(
                {
                    "date": day_data.date,
                    "temp_max": day_data.temp_max,
                    "temp_min": day_data.temp_min,
                    "temp_mean": day_data.temp_mean,
                    "humidity_mean": day_data.humidity_mean,
                    "wind_speed_2m_mean": day_data.wind_speed_2m_mean,
                    "precipitation_sum": day_data.precipitation_sum,
                    "solar_radiation_original": radiation_original,
                    "solar_radiation_adjusted": radiation_adjusted,
                    "eto_fao": day_data.eto_fao,  # ETo do Open-Meteo
                    # TODO: Recalcular ETo com gamma e pressure ajustados
                }
            )

        return {
            "location": {
                "lat": lat,
                "lon": lon,
                "elevation": elevation,
                "elevation_source": (
                    "opentopo" if topo_location else "openmeteo"
                ),
                "elevation_openmeteo": meteo_elevation,
                "elevation_opentopo": elevation if topo_location else None,
                "elevation_difference": diff if topo_location else 0,
            },
            "elevation_factors": factors,
            "daily": daily_results,
            "summary": {
                "total_days": len(daily_results),
                "avg_temp_mean": sum(d["temp_mean"] for d in daily_results)
                / len(daily_results),
                "total_precipitation": sum(
                    d["precipitation_sum"] for d in daily_results
                ),
                "avg_eto": sum(d["eto_fao"] for d in daily_results)
                / len(daily_results),
                "solar_adjustment_percent": (factors["solar_factor"] - 1)
                * 100,
            },
        }

    finally:
        await meteo_client.close()
        await topo_client.close()


async def compare_elevations_multiple_locations():
    """
    Compara elevações de Open-Meteo vs OpenTopoData
    para múltiplas localizações.
    """
    locations = [
        {"name": "Brasília", "lat": -15.7801, "lon": -47.9292},
        {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333},
        {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729},
        {"name": "Belo Horizonte", "lat": -19.9167, "lon": -43.9345},
        {"name": "Curitiba", "lat": -25.4284, "lon": -49.2733},
    ]

    meteo_client = OpenMeteoForecastClient()
    topo_client = OpenTopoClient()

    try:
        logger.info("\n" + "=" * 60)
        logger.info("COMPARAÇÃO DE ELEVAÇÕES: Open-Meteo vs OpenTopoData")
        logger.info("=" * 60 + "\n")

        # Batch OpenTopoData (mais eficiente)
        coords = [(loc["lat"], loc["lon"]) for loc in locations]
        topo_results = await topo_client.get_elevations_batch(coords)

        results = []

        for i, location in enumerate(locations):
            # Open-Meteo (precisa fazer request individual)
            today = datetime.now()
            meteo_data = await meteo_client.get_daily_forecast(
                location["lat"],
                location["lon"],
                today,
                today,
            )

            meteo_elev = meteo_data["location"]["elevation"]
            topo_elev = topo_results[i].elevation
            diff = abs(meteo_elev - topo_elev)
            diff_percent = (diff / topo_elev) * 100

            # Calcular impacto no ETo
            factors_meteo = ElevationUtils.get_elevation_correction_factor(
                meteo_elev
            )
            factors_topo = ElevationUtils.get_elevation_correction_factor(
                topo_elev
            )

            gamma_diff = abs(factors_topo["gamma"] - factors_meteo["gamma"])
            gamma_diff_percent = (gamma_diff / factors_topo["gamma"]) * 100

            result = {
                "location": location["name"],
                "lat": location["lat"],
                "lon": location["lon"],
                "elevation_openmeteo": meteo_elev,
                "elevation_opentopo": topo_elev,
                "difference_m": diff,
                "difference_percent": diff_percent,
                "gamma_topo": factors_topo["gamma"],
                "gamma_meteo": factors_meteo["gamma"],
                "gamma_difference_percent": gamma_diff_percent,
            }

            results.append(result)

            # Log resultado
            logger.info(f"📍 {location['name']}")
            logger.info(f"   Open-Meteo: {meteo_elev:.1f}m")
            logger.info(f"   OpenTopo:   {topo_elev:.1f}m")
            logger.info(f"   Diferença:  {diff:.1f}m ({diff_percent:.1f}%)")
            logger.info(
                f"   Impacto γ:  {gamma_diff_percent:.2f}% "
                f"({factors_topo['gamma']:.5f} vs {factors_meteo['gamma']:.5f})"
            )
            logger.info("")

        return results

    finally:
        await meteo_client.close()
        await topo_client.close()


async def main():
    """Exemplo principal."""
    # Teste 1: Cálculo completo de ETo com elevação
    logger.info("\n" + "=" * 60)
    logger.info("TESTE 1: Cálculo de ETo com Elevação")
    logger.info("=" * 60 + "\n")

    brasilia_lat, brasilia_lon = -15.7801, -47.9292
    start = datetime.now()
    end = start + timedelta(days=5)

    result = await calculate_eto_with_elevation(
        brasilia_lat,
        brasilia_lon,
        start,
        end,
    )

    logger.info("\n📊 RESUMO:")
    logger.info(
        f"Local: ({result['location']['lat']}, {result['location']['lon']})"
    )
    logger.info(f"Elevação: {result['location']['elevation']:.1f}m")
    logger.info(f"Fonte elevação: {result['location']['elevation_source']}")
    logger.info(f"Pressão: {result['elevation_factors']['pressure']:.2f} kPa")
    logger.info(f"Gamma: {result['elevation_factors']['gamma']:.5f} kPa/°C")
    logger.info(
        f"Ajuste solar: +{result['summary']['solar_adjustment_percent']:.1f}%"
    )
    logger.info(f"ETo médio: {result['summary']['avg_eto']:.2f} mm/dia")
    logger.info(f"Temp média: {result['summary']['avg_temp_mean']:.1f}°C")
    logger.info(
        f"Precipitação total: {result['summary']['total_precipitation']:.1f} mm"
    )

    # Teste 2: Comparar elevações
    logger.info("\n")
    await compare_elevations_multiple_locations()


if __name__ == "__main__":
    asyncio.run(main())
