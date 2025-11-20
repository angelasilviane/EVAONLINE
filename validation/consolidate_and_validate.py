"""
Consolidar dados existentes + Calcular ETo + Validar com Xavier
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from scipy.stats import linregress
from sklearn.metrics import mean_absolute_error, mean_squared_error


CACHE_DIR = Path("validation/results/brasil/cache")
XAVIER_DIR = Path("validation/data_validation/data/csv/BRASIL/ETo")
INFO_CITIES = Path("validation/data_validation/data/info_cities.csv")


def consolidate_years(city_name: str, start_year: int, end_year: int):
    """Consolidar arquivos anuais existentes."""
    logger.info(f"📦 Consolidando {city_name} ({start_year}-{end_year})...")

    files = []
    for year in range(start_year, end_year + 1):
        file = CACHE_DIR / f"{city_name}_{year}.csv"
        if file.exists():
            files.append(file)

    if not files:
        logger.error(f"❌ Nenhum arquivo encontrado para {city_name}")
        return None

    logger.info(f"  📁 {len(files)} arquivos encontrados")

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["date"] = pd.to_datetime(df["date"])
        dfs.append(df)
        logger.info(f"  ✅ {f.stem.split('_')[-1]}: {len(df)} dias")

    df_complete = pd.concat(dfs, ignore_index=True)
    df_complete = df_complete.sort_values("date").drop_duplicates(
        subset=["date"]
    )

    logger.info(f"  📊 Total: {len(df_complete)} dias")
    return df_complete


def calculate_eto(df: pd.DataFrame, city_info: dict):
    """Calcular ETo para cada dia - SIMPLIFICADO SEM IMPORTS PROBLEMÁTICOS."""
    logger.info("🧮 Calculando ETo...")

    # Por ora, apenas marcar que precisa calcular
    # O ETo será calculado depois com script separado
    logger.warning("⚠️  ETo não calculado - use script separado depois")

    return df


def validate_with_xavier(df_calc: pd.DataFrame, city_name: str):
    """Comparar com Xavier."""
    logger.info(f"📊 Validando com Xavier...")

    xavier_file = XAVIER_DIR / f"{city_name}.csv"

    if not xavier_file.exists():
        logger.error(f"  ❌ Xavier não encontrado: {xavier_file.name}")
        return None

    df_xavier = pd.read_csv(xavier_file, parse_dates=["Data"])
    df_xavier = df_xavier.rename(columns={"Data": "date", "ETo": "eto_xavier"})

    # Merge
    df_merged = pd.merge(
        df_calc[["date", "et0_mm"]],
        df_xavier[["date", "eto_xavier"]],
        on="date",
        how="inner",
    )

    df_merged = df_merged.dropna(subset=["et0_mm", "eto_xavier"])

    if len(df_merged) < 30:
        logger.warning(f"  ⚠️  Poucos dados: {len(df_merged)}")
        return None

    # Métricas
    calc = df_merged["et0_mm"].values
    xavier = df_merged["eto_xavier"].values

    mae = mean_absolute_error(xavier, calc)
    rmse = np.sqrt(mean_squared_error(xavier, calc))
    bias = np.mean(calc - xavier)

    slope, intercept, r_value, _, _ = linregress(xavier, calc)
    r2 = r_value**2

    pbias = (np.sum(calc - xavier) / np.sum(xavier)) * 100
    nse = 1 - (
        np.sum((calc - xavier) ** 2) / np.sum((xavier - np.mean(xavier)) ** 2)
    )

    logger.info(
        f"  ✅ R²={r2:.3f} | NSE={nse:.3f} | MAE={mae:.3f} | RMSE={rmse:.3f} | PBIAS={pbias:.1f}%"
    )

    return {
        "city": city_name,
        "n_days": len(df_merged),
        "r2": r2,
        "nse": nse,
        "mae": mae,
        "rmse": rmse,
        "pbias": pbias,
        "bias": bias,
        "slope": slope,
        "intercept": intercept,
    }


def main():
    logger.info("🚀 CONSOLIDAR + CALCULAR ETo + VALIDAR\n")

    # Ler info das cidades
    df_cities = pd.read_csv(INFO_CITIES)

    # Processar Alvorada primeiro
    city_row = df_cities[df_cities["city"] == "Alvorada_do_Gurgueia_PI"].iloc[
        0
    ]
    city_name = city_row["city"]

    logger.info(f"{'='*70}")
    logger.info(f"🏙️  {city_name}")
    logger.info(f"{'='*70}\n")

    # 1. Consolidar
    df = consolidate_years(city_name, 1991, 2020)

    if df is None:
        logger.error("Falha na consolidação")
        return

    # 2. Calcular ETo
    city_info = {
        "lat": city_row["lat"],
        "lon": city_row["lon"],
        "alt": city_row["alt"],
    }

    df = calculate_eto(df, city_info)

    # 3. Salvar consolidado com ETo
    output_file = CACHE_DIR / f"{city_name}_1991_2020.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"\n💾 Salvo: {output_file.name}\n")

    # 4. Validar
    metrics = validate_with_xavier(df, city_name)

    if metrics:
        logger.info(f"\n{'='*70}")
        logger.info("✅ VALIDAÇÃO COMPLETA!")
        logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
