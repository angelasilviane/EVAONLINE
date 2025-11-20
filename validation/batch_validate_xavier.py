"""
Validação Completa - Compara dados baixados com Xavier
Lê dados do cache e compara com Xavier ETo
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger
from scipy.stats import linregress
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
from datetime import datetime


# ==================== CONFIGURAÇÃO ====================
BASE_DIR = Path(__file__).parent
INFO_CITIES = BASE_DIR / "data_validation/data/info_cities.csv"
CACHE_DIR = BASE_DIR / "results/brasil/cache"
XAVIER_DIR = BASE_DIR / "data_validation/data/csv/BRASIL/ETo"
OUTPUT_DIR = BASE_DIR / "results/brasil/validation"
PLOTS_DIR = OUTPUT_DIR / "plots"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def compare_with_xavier(
    city_name: str,
    start_year: int,
    end_year: int,
    create_plot: bool = False,
):
    """
    Compara dados calculados com Xavier para uma cidade.
    """
    # Ler dados calculados do cache
    cache_file = CACHE_DIR / f"{city_name}_{start_year}_{end_year}.csv"

    if not cache_file.exists():
        logger.warning(f"⚠️  Cache não encontrado: {cache_file.name}")
        return None

    df_calc = pd.read_csv(cache_file, parse_dates=["date"])

    if "et0_mm" not in df_calc.columns:
        logger.warning(f"⚠️  Coluna et0_mm não encontrada em {city_name}")
        return None

    # Ler Xavier
    xavier_file = XAVIER_DIR / f"{city_name}.csv"

    if not xavier_file.exists():
        logger.warning(f"⚠️  Xavier não encontrado: {xavier_file.name}")
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
        logger.warning(f"⚠️  Poucos dados: {len(df_merged)}")
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
    nse = 1 - (
        np.sum((calculated - xavier) ** 2)
        / np.sum((xavier - np.mean(xavier)) ** 2)
    )

    metrics = {
        "city": city_name,
        "n_days": len(df_merged),
        "period": f"{start_year}-{end_year}",
        "mae": mae,
        "rmse": rmse,
        "bias": bias,
        "r2": r2,
        "nse": nse,
        "pbias": pbias,
        "slope": slope,
        "intercept": intercept,
        "mean_calculated": np.mean(calculated),
        "mean_xavier": np.mean(xavier),
        "std_calculated": np.std(calculated),
        "std_xavier": np.std(xavier),
    }

    logger.info(
        f"📊 {city_name}: R²={r2:.3f} | NSE={nse:.3f} | "
        f"MAE={mae:.3f} | RMSE={rmse:.3f} | PBIAS={pbias:.1f}%"
    )

    # Criar gráfico
    if create_plot:
        create_validation_plot(
            df_merged, metrics, city_name, start_year, end_year
        )

    return metrics


def create_validation_plot(
    df: pd.DataFrame,
    metrics: dict,
    city_name: str,
    start_year: int,
    end_year: int,
):
    """
    Cria gráfico de dispersão e série temporal.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Scatter plot
    ax1 = axes[0]
    ax1.scatter(
        df["eto_xavier"],
        df["et0_mm"],
        alpha=0.3,
        s=10,
        label="Dados",
    )

    # Linha 1:1
    min_val = min(df["eto_xavier"].min(), df["et0_mm"].min())
    max_val = max(df["eto_xavier"].max(), df["et0_mm"].max())
    ax1.plot([min_val, max_val], [min_val, max_val], "k--", lw=1, label="1:1")

    # Linha de regressão
    slope = metrics["slope"]
    intercept = metrics["intercept"]
    x_line = np.array([min_val, max_val])
    y_line = slope * x_line + intercept
    ax1.plot(
        x_line,
        y_line,
        "r-",
        lw=2,
        label=f"Regressão (y={slope:.2f}x+{intercept:.2f})",
    )

    ax1.set_xlabel("ETo Xavier (mm/dia)")
    ax1.set_ylabel("ETo Calculado (mm/dia)")
    ax1.set_title(f"{city_name} - Scatter Plot")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Estatísticas no gráfico
    textstr = f"n = {metrics['n_days']}\n"
    textstr += f"R² = {metrics['r2']:.3f}\n"
    textstr += f"NSE = {metrics['nse']:.3f}\n"
    textstr += f"MAE = {metrics['mae']:.3f} mm\n"
    textstr += f"RMSE = {metrics['rmse']:.3f} mm\n"
    textstr += f"PBIAS = {metrics['pbias']:.1f}%"

    ax1.text(
        0.05,
        0.95,
        textstr,
        transform=ax1.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    # Série temporal (primeiros 365 dias)
    ax2 = axes[1]
    df_plot = df.head(365)
    ax2.plot(
        df_plot["date"],
        df_plot["eto_xavier"],
        label="Xavier",
        linewidth=1,
        alpha=0.7,
    )
    ax2.plot(
        df_plot["date"],
        df_plot["et0_mm"],
        label="Calculado",
        linewidth=1,
        alpha=0.7,
    )
    ax2.set_xlabel("Data")
    ax2.set_ylabel("ETo (mm/dia)")
    ax2.set_title(f"{city_name} - Série Temporal (primeiro ano)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    plt.tight_layout()

    # Salvar
    plot_file = PLOTS_DIR / f"{city_name}_{start_year}_{end_year}.png"
    plt.savefig(plot_file, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"  📈 Gráfico salvo: {plot_file.name}")


def validate_all_cities(
    start_year: int = 1991,
    end_year: int = 2020,
    cities_filter: list[str] | None = None,
    create_plots: bool = True,
):
    """
    Valida todas as cidades que têm dados em cache.
    """
    df_cities = pd.read_csv(INFO_CITIES)

    if cities_filter:
        df_cities = df_cities[df_cities["city"].isin(cities_filter)]

    logger.info(f"🔍 Validando {len(df_cities)} cidades")

    all_metrics = []

    for idx, row in df_cities.iterrows():
        city = row["city"]

        logger.info(f"\n[{idx+1}/{len(df_cities)}] {city}")

        metrics = compare_with_xavier(
            city_name=city,
            start_year=start_year,
            end_year=end_year,
            create_plot=create_plots,
        )

        if metrics:
            all_metrics.append(metrics)

    if not all_metrics:
        logger.error("❌ Nenhuma validação bem-sucedida")
        return None

    # Salvar resultados
    df_results = pd.DataFrame(all_metrics)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"validation_summary_{timestamp}.csv"
    df_results.to_csv(output_file, index=False)

    logger.info(f"\n{'='*70}")
    logger.info(f"✅ VALIDAÇÃO COMPLETA!")
    logger.info(f"📊 Resultados: {output_file}")
    logger.info(f"{'='*70}")

    # Estatísticas
    logger.info(f"\n📈 ESTATÍSTICAS GERAIS:")
    logger.info(f"  Cidades validadas: {len(df_results)}")
    logger.info(f"  R² médio: {df_results['r2'].mean():.3f}")
    logger.info(f"  NSE médio: {df_results['nse'].mean():.3f}")
    logger.info(f"  MAE médio: {df_results['mae'].mean():.3f} mm/dia")
    logger.info(f"  RMSE médio: {df_results['rmse'].mean():.3f} mm/dia")
    logger.info(f"  PBIAS médio: {df_results['pbias'].mean():.1f}%")

    # Melhor e pior
    best = df_results.loc[df_results["r2"].idxmax()]
    worst = df_results.loc[df_results["r2"].idxmin()]

    logger.info(f"\n🏆 Melhor R²: {best['city']} (R²={best['r2']:.3f})")
    logger.info(f"⚠️  Pior R²: {worst['city']} (R²={worst['r2']:.3f})")

    return df_results


def main():
    parser = argparse.ArgumentParser(
        description="Validação Completa - Compara com Xavier"
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
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Não gerar gráficos",
    )

    args = parser.parse_args()

    logger.info("🚀 INICIANDO VALIDAÇÃO")
    logger.info(f"   Período: {args.start_year} → {args.end_year}")

    validate_all_cities(
        start_year=args.start_year,
        end_year=args.end_year,
        cities_filter=args.cities,
        create_plots=not args.no_plots,
    )


if __name__ == "__main__":
    main()
