"""
Batch Download por Ano - Para evitar timeouts
Processa uma cidade por vez, um ano por vez
"""

import argparse
import asyncio
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger

from data_download_historical import download_historical_weather_data
from validation_logic_eto.core.eto_calculation.eto_calculation import (
    calculate_et0_pm_asce_hourly,
    calculate_et0_hargreaves,
)


# ==================== CONFIGURAÇÃO ====================
BASE_DIR = Path(__file__).parent
INFO_CITIES = BASE_DIR / "data_validation/data/info_cities.csv"
CACHE_DIR = BASE_DIR / "results/brasil/cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def calculate_eto_for_dataframe(
    df: pd.DataFrame, latitude: float, altitude: float
) -> pd.DataFrame:
    """
    Calcula ETo para cada linha do DataFrame.
    """
    eto_list = []

    for _, row in df.iterrows():
        try:
            # Penman-Monteith ASCE (preferred)
            eto = calculate_et0_pm_asce_hourly(
                tmax_c=row.get("T2M_MAX"),
                tmin_c=row.get("T2M_MIN"),
                rhmax=None,
                rhmin=None,
                rhmean=row.get("RH2M"),
                u2_ms=row.get("WS2M"),
                rs_mj=row.get("ALLSKY_SFC_SW_DWN"),
                latitude_deg=latitude,
                elevation_m=altitude,
                doy=pd.to_datetime(row["date"]).dayofyear,
            )

            # Fallback: Hargreaves
            if eto is None or pd.isna(eto):
                eto = calculate_et0_hargreaves(
                    tmax_c=row.get("T2M_MAX"),
                    tmin_c=row.get("T2M_MIN"),
                    tavg_c=row.get("T2M"),
                    latitude_deg=latitude,
                    doy=pd.to_datetime(row["date"]).dayofyear,
                )

            eto_list.append(eto)

        except Exception as e:
            logger.debug(f"Erro cálculo ETo {row['date']}: {e}")
            eto_list.append(np.nan)

    df["et0_mm"] = eto_list
    return df


async def download_city_yearly(
    city_name: str,
    latitude: float,
    longitude: float,
    altitude: float,
    start_year: int,
    end_year: int,
):
    """
    Baixa dados de uma cidade ano por ano para evitar timeouts.
    Calcula ETo para cada ano.
    """
    all_data = []

    for year in range(start_year, end_year + 1):
        cache_file = CACHE_DIR / f"{city_name}_{year}.csv"

        if cache_file.exists():
            logger.info(f"📦 Cache: {year}")
            try:
                df_year = pd.read_csv(cache_file)
                # Garantir que date é datetime
                if "date" in df_year.columns:
                    df_year["date"] = pd.to_datetime(df_year["date"])
                all_data.append(df_year)
                continue
            except Exception as e:
                logger.warning(f"⚠️  Erro lendo cache {year}: {e}")
                # Se falhar, re-baixar

        try:
            logger.info(f"📥 Baixando {year}...")
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            df_year, warnings = await download_historical_weather_data(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                use_fusion=True,
            )

            if df_year is not None and not df_year.empty:
                # Garantir que date é datetime
                if "date" in df_year.columns:
                    df_year["date"] = pd.to_datetime(df_year["date"])

                # Calcular ETo
                logger.info(f"  🧮 Calculando ETo {year}...")
                df_year = calculate_eto_for_dataframe(
                    df_year, latitude, altitude
                )

                df_year.to_csv(cache_file, index=False)
                logger.info(f"✅ {year}: {len(df_year)} dias")
                all_data.append(df_year)
            else:
                logger.warning(f"⚠️  {year}: Sem dados")

        except Exception as e:
            logger.error(f"❌ Erro {year}: {e}")
            continue

    if not all_data:
        return None

    # Concatenar todos os anos
    df_complete = pd.concat(all_data, ignore_index=True)

    # Ordenar e remover duplicatas se a coluna date existir
    if "date" in df_complete.columns:
        df_complete = df_complete.sort_values("date").drop_duplicates(
            subset=["date"]
        )
    else:
        logger.warning(f"⚠️  Coluna 'date' não encontrada no DataFrame")
        logger.info(f"   Colunas disponíveis: {list(df_complete.columns)}")
        return None

    # Salvar completo
    output_file = CACHE_DIR / f"{city_name}_{start_year}_{end_year}.csv"
    df_complete.to_csv(output_file, index=False)
    logger.info(f"💾 Completo: {output_file.name} ({len(df_complete)} dias)")

    return df_complete


async def process_all_cities_yearly(
    start_year: int = 1991,
    end_year: int = 2020,
    cities_filter: list[str] | None = None,
):
    """
    Processa todas as cidades, ano por ano.
    """
    df_cities = pd.read_csv(INFO_CITIES)
    logger.info(f"📍 {len(df_cities)} cidades em info_cities.csv")

    if cities_filter:
        df_cities = df_cities[df_cities["city"].isin(cities_filter)]
        logger.info(f"🔍 Filtradas: {len(df_cities)} cidades")

    for idx, row in df_cities.iterrows():
        city = row["city"]
        lat = row["lat"]
        lon = row["lon"]
        alt = row["alt"]

        logger.info(f"\n{'='*70}")
        logger.info(f"🏙️  [{idx+1}/{len(df_cities)}] {city}")
        logger.info(f"{'='*70}")

        await download_city_yearly(
            city_name=city,
            latitude=lat,
            longitude=lon,
            altitude=alt,
            start_year=start_year,
            end_year=end_year,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Batch Download por Ano - Todas as Cidades"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=1991,
        help="Ano inicial",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2020,
        help="Ano final",
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        help="Cidades específicas (opcional)",
    )

    args = parser.parse_args()

    logger.info("🚀 INICIANDO BATCH DOWNLOAD POR ANO")
    logger.info(f"   Período: {args.start_year} → {args.end_year}")

    asyncio.run(
        process_all_cities_yearly(
            start_year=args.start_year,
            end_year=args.end_year,
            cities_filter=args.cities,
        )
    )


if __name__ == "__main__":
    main()
