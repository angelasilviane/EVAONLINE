"""
Batch Download e Validação - Todas as Cidades
Download de dados históricos (1991-2020) + Cálculo ETo + Comparação Xavier
"""

import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime
from scipy.stats import linregress
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Imports do pipeline
from validation_logic_eto.api.services.nasa_power.nasa_power_sync_adapter import (
    NASAPowerSyncAdapter,
)
from validation_logic_eto.api.services.openmeteo_archive.openmeteo_archive_sync_adapter import (
    OpenMeteoArchiveSyncAdapter,
)
from validation_logic_eto.core.data_processing.data_preprocessing import (
    preprocessing,
)
from validation_logic_eto.core.data_processing.kalman_ensemble import (
    ClimateKalmanEnsemble,
)
from validation_logic_eto.core.eto_calculation.eto_calculation import (
    calculate_et0_hargreaves,
    calculate_et0_pm_asce_hourly,
)


# ==================== CONFIGURAÇÃO ====================
BASE_DIR = Path(__file__).parent
INFO_CITIES = BASE_DIR / "data_validation/data/info_cities.csv"
XAVIER_DIR = BASE_DIR / "data_validation/data/csv/BRASIL/ETo"
OUTPUT_DIR = BASE_DIR / "results/brasil/batch_validation"
CACHE_DIR = BASE_DIR / "results/brasil/cache"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


async def download_city_data(
    city_name: str,
    latitude: float,
    longitude: float,
    altitude: float,
    start_date: str,
    end_date: str,
) -> pd.DataFrame | None:
    """
    Baixa dados de uma cidade com fusão Kalman.
    Retorna DataFrame com variáveis fusionadas.
    """
    try:
        logger.info(f"📥 Baixando {city_name}: {start_date} → {end_date}")

        # Criar adaptadores
        nasa = NASAPowerSyncAdapter()
        openmeteo = OpenMeteoArchiveSyncAdapter()

        # Download NASA POWER
        logger.info(f"  ├─ NASA POWER...")
        nasa_data = await asyncio.to_thread(
            nasa.get_historical_data,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        # Download OpenMeteo Archive
        logger.info(f"  ├─ OpenMeteo Archive...")
        openmeteo_data = await asyncio.to_thread(
            openmeteo.get_historical_data,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        # Preprocessing
        logger.info(f"  ├─ Preprocessing...")
        nasa_prep = preprocessing(nasa_data, source_name="nasa")
        openmeteo_prep = preprocessing(openmeteo_data, source_name="openmeteo")

        # Fusão Kalman
        logger.info(f"  ├─ Fusão Kalman...")
        kalman = ClimateKalmanEnsemble()

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        all_dates = pd.date_range(start_dt, end_dt, freq="D")

        fused_records = []

        for current_date in all_dates:
            date_str = current_date.strftime("%Y-%m-%d")

            # Coletar medidas das duas fontes
            measurements = {}
            for i, (source_df, prefix) in enumerate(
                [(nasa_prep, ""), (openmeteo_prep, "1")]
            ):
                row = source_df[source_df["date"] == date_str]
                if not row.empty:
                    for var in [
                        "T2M_MAX",
                        "T2M_MIN",
                        "T2M",
                        "RH2M",
                        "WS2M",
                        "ALLSKY_SFC_SW_DWN",
                        "PRECTOTCORR",
                    ]:
                        if var in row.columns:
                            key = f"{var}{prefix}"
                            measurements[key] = row[var].values[0]

            if not measurements:
                continue

            try:
                fused_day = kalman.auto_fuse_sync(
                    latitude=latitude,
                    longitude=longitude,
                    measurements=measurements,
                    date=current_date,
                )

                fused_record = {"date": date_str}
                fused_record.update(fused_day["fused"])
                fused_records.append(fused_record)

            except Exception as e:
                logger.warning(f"  │  Erro fusão {date_str}: {e}")
                continue

        if not fused_records:
            logger.error(f"  └─ ❌ Nenhum dado fusionado para {city_name}")
            return None

        df_fused = pd.DataFrame(fused_records)
        df_fused["date"] = pd.to_datetime(df_fused["date"])

        # Calcular ETo
        logger.info(f"  ├─ Calculando ETo...")
        df_fused = calculate_eto_for_dataframe(
            df_fused, latitude, altitude, city_name
        )

        logger.info(f"  └─ ✅ {len(df_fused)} dias processados")
        return df_fused

    except Exception as e:
        logger.error(f"  └─ ❌ Erro em {city_name}: {e}")
        return None


def calculate_eto_for_dataframe(
    df: pd.DataFrame, latitude: float, altitude: float, city_name: str
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
            logger.warning(f"Erro cálculo ETo {row['date']}: {e}")
            eto_list.append(np.nan)

    df["et0_mm"] = eto_list
    return df


def compare_with_xavier(
    df_calculated: pd.DataFrame, city_name: str, xavier_dir: Path
) -> Dict[str, Any] | None:
    """
    Compara ETo calculado com dados Xavier.
    """
    xavier_file = xavier_dir / f"{city_name}.csv"

    if not xavier_file.exists():
        logger.warning(f"⚠️  Arquivo Xavier não encontrado: {xavier_file.name}")
        return None

    try:
        # Ler Xavier
        df_xavier = pd.read_csv(xavier_file, parse_dates=["Data"])
        df_xavier = df_xavier.rename(
            columns={"Data": "date", "ETo": "eto_xavier"}
        )
        df_xavier["date"] = pd.to_datetime(df_xavier["date"])

        # Merge
        df_merged = pd.merge(
            df_calculated[["date", "et0_mm"]],
            df_xavier[["date", "eto_xavier"]],
            on="date",
            how="inner",
        )

        df_merged = df_merged.dropna(subset=["et0_mm", "eto_xavier"])

        if len(df_merged) < 30:
            logger.warning(
                f"⚠️  Poucos dados para comparação: {len(df_merged)}"
            )
            return None

        # Métricas
        calculated = df_merged["et0_mm"].values
        xavier = df_merged["eto_xavier"].values

        mae = mean_absolute_error(xavier, calculated)
        rmse = np.sqrt(mean_squared_error(xavier, calculated))
        bias = np.mean(calculated - xavier)

        slope, intercept, r_value, _, _ = linregress(xavier, calculated)
        r2 = r_value**2

        pbias = (np.sum(calculated - xavier) / np.sum(xavier)) * 100

        metrics = {
            "city": city_name,
            "n_days": len(df_merged),
            "mae": mae,
            "rmse": rmse,
            "bias": bias,
            "r2": r2,
            "pbias": pbias,
            "slope": slope,
            "intercept": intercept,
            "mean_calculated": np.mean(calculated),
            "mean_xavier": np.mean(xavier),
        }

        logger.info(
            f"📊 {city_name}: R²={r2:.3f} | MAE={mae:.3f} | RMSE={rmse:.3f} | PBIAS={pbias:.1f}%"
        )

        return metrics

    except Exception as e:
        logger.error(f"❌ Erro comparação Xavier {city_name}: {e}")
        return None


async def process_all_cities(
    start_date: str = "1991-01-01",
    end_date: str = "2020-12-31",
    cities_filter: List[str] | None = None,
):
    """
    Processa todas as cidades: download → ETo → validação Xavier.
    """
    # Ler info_cities.csv
    df_cities = pd.read_csv(INFO_CITIES)
    logger.info(f"📍 {len(df_cities)} cidades encontradas em info_cities.csv")

    if cities_filter:
        df_cities = df_cities[df_cities["city"].isin(cities_filter)]
        logger.info(f"🔍 Filtrando: {len(df_cities)} cidades selecionadas")

    all_metrics = []

    for idx, row in df_cities.iterrows():
        city = row["city"]
        lat = row["lat"]
        lon = row["lon"]
        alt = row["alt"]

        logger.info(f"\n{'='*70}")
        logger.info(f"🏙️  [{idx+1}/{len(df_cities)}] {city}")
        logger.info(f"{'='*70}")

        # Verificar cache
        cache_file = CACHE_DIR / f"{city}_{start_date}_{end_date}.csv"

        if cache_file.exists():
            logger.info(f"📦 Carregando do cache: {cache_file.name}")
            df_calculated = pd.read_csv(cache_file, parse_dates=["date"])
        else:
            # Download + cálculo
            df_calculated = await download_city_data(
                city_name=city,
                latitude=lat,
                longitude=lon,
                altitude=alt,
                start_date=start_date,
                end_date=end_date,
            )

            if df_calculated is None or df_calculated.empty:
                logger.error(f"❌ Falha no download de {city}")
                continue

            # Salvar cache
            df_calculated.to_csv(cache_file, index=False)
            logger.info(f"💾 Cache salvo: {cache_file.name}")

        # Comparar com Xavier
        metrics = compare_with_xavier(df_calculated, city, XAVIER_DIR)

        if metrics:
            all_metrics.append(metrics)

    # Salvar resultados consolidados
    if all_metrics:
        df_results = pd.DataFrame(all_metrics)
        output_file = (
            OUTPUT_DIR
            / f"validation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        df_results.to_csv(output_file, index=False)

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ VALIDAÇÃO COMPLETA!")
        logger.info(f"📊 Resultados salvos: {output_file}")
        logger.info(f"{'='*70}")

        # Estatísticas gerais
        logger.info(f"\n📈 ESTATÍSTICAS GERAIS:")
        logger.info(f"  Cidades validadas: {len(df_results)}")
        logger.info(f"  R² médio: {df_results['r2'].mean():.3f}")
        logger.info(f"  MAE médio: {df_results['mae'].mean():.3f} mm/dia")
        logger.info(f"  RMSE médio: {df_results['rmse'].mean():.3f} mm/dia")
        logger.info(f"  PBIAS médio: {df_results['pbias'].mean():.1f}%")

        return df_results
    else:
        logger.error("❌ Nenhuma validação bem-sucedida")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Batch Download e Validação - Todas as Cidades"
    )
    parser.add_argument(
        "--start-date",
        default="1991-01-01",
        help="Data inicial (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        default="2020-12-31",
        help="Data final (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        help="Cidades específicas (opcional)",
    )

    args = parser.parse_args()

    logger.info("🚀 INICIANDO BATCH DOWNLOAD E VALIDAÇÃO")
    logger.info(f"   Período: {args.start_date} → {args.end_date}")

    asyncio.run(
        process_all_cities(
            start_date=args.start_date,
            end_date=args.end_date,
            cities_filter=args.cities,
        )
    )


if __name__ == "__main__":
    main()
