"""
Generate validation visualizations comparing EVAonline ETo with reference datasets.

Creates scatter plots, time series, residual plots, and Taylor diagrams.

Usage:
    python validation/scripts/visualize_results.py --region brasil
    python validation/scripts/visualize_results.py --region mundo
    python validation/scripts/visualize_results.py --region both
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

warnings.filterwarnings("ignore")

from validation.config import (
    get_all_cities,
    get_eto_file_path,
    get_city_metadata,
    BRASIL_RESULTS_DIR,
    MUNDO_RESULTS_DIR,
    CONSOLIDATED_DIR,
    PLOT_CONFIG,
)

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = PLOT_CONFIG["dpi"]
plt.rcParams["font.size"] = PLOT_CONFIG["font_size"]


# ============================================================================
# SCATTER PLOT: Observed vs Predicted
# ============================================================================


def plot_scatter(city_key: str, region: str, df: pd.DataFrame):
    """
    Create scatter plot of observed vs predicted ETo with 1:1 line.

    Args:
        city_key: City identifier
        region: 'brasil' or 'mundo'
        df: DataFrame with ETo_reference and ETo_calculated columns
    """
    metadata = get_city_metadata(city_key, region)
    city_name = metadata.get("name", city_key)

    fig, ax = plt.subplots(figsize=(10, 10))

    # Extract data
    obs = df["ETo_reference"].values
    pred = df["ETo_calculated"].values

    # Scatter plot
    ax.scatter(
        obs,
        pred,
        alpha=0.5,
        s=20,
        c="steelblue",
        edgecolors="navy",
        linewidth=0.5,
    )

    # 1:1 line
    min_val = min(obs.min(), pred.min())
    max_val = max(obs.max(), pred.max())
    ax.plot(
        [min_val, max_val], [min_val, max_val], "r--", lw=2, label="1:1 Line"
    )

    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(obs, pred)
    line_x = np.array([min_val, max_val])
    line_y = slope * line_x + intercept
    ax.plot(
        line_x,
        line_y,
        "g-",
        lw=2,
        label=f"Linear Fit: y={slope:.3f}x+{intercept:.3f}",
    )

    # Calculate metrics
    mae = np.mean(np.abs(obs - pred))
    rmse = np.sqrt(np.mean((obs - pred) ** 2))
    r2 = r_value**2

    # Add metrics text
    textstr = (
        f"n = {len(obs)}\n"
        f"MAE = {mae:.3f} mm/day\n"
        f"RMSE = {rmse:.3f} mm/day\n"
        f"r² = {r2:.3f}\n"
        f"r = {r_value:.3f}"
    )

    props = dict(boxstyle="round", facecolor="wheat", alpha=0.8)
    ax.text(
        0.05,
        0.95,
        textstr,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=props,
    )

    ax.set_xlabel("Reference ETo (mm/day)", fontsize=13, fontweight="bold")
    ax.set_ylabel("EVAonline ETo (mm/day)", fontsize=13, fontweight="bold")
    ax.set_title(
        f"ETo Validation: {city_name} ({region.upper()})",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="lower right", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="box")

    plt.tight_layout()

    # Save plot
    output_dir = (
        BRASIL_RESULTS_DIR if region == "brasil" else MUNDO_RESULTS_DIR
    )
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    output_file = plots_dir / f"{city_key}_scatter.png"
    plt.savefig(output_file, dpi=PLOT_CONFIG["dpi"], bbox_inches="tight")
    plt.close()

    print(f"  ✅ Scatter plot saved: {output_file.name}")


# ============================================================================
# TIME SERIES PLOT
# ============================================================================


def plot_timeseries(
    city_key: str, region: str, df: pd.DataFrame, max_days: int = 365
):
    """
    Create time series plot comparing reference and calculated ETo.

    Args:
        city_key: City identifier
        region: 'brasil' or 'mundo'
        df: DataFrame with date index and ETo columns
        max_days: Maximum number of days to plot (default: 365)
    """
    metadata = get_city_metadata(city_key, region)
    city_name = metadata.get("name", city_key)

    # Limit to max_days for readability
    df_plot = df.tail(max_days) if len(df) > max_days else df

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 10), gridspec_kw={"height_ratios": [3, 1]}
    )

    # Time series
    ax1.plot(
        df_plot.index,
        df_plot["ETo_reference"],
        label="Reference",
        color="navy",
        linewidth=1.5,
        alpha=0.7,
    )
    ax1.plot(
        df_plot.index,
        df_plot["ETo_calculated"],
        label="EVAonline",
        color="orangered",
        linewidth=1.5,
        alpha=0.7,
    )

    ax1.set_ylabel("ETo (mm/day)", fontsize=12, fontweight="bold")
    ax1.set_title(
        f"Daily ETo Time Series: {city_name} ({region.upper()})",
        fontsize=14,
        fontweight="bold",
    )
    ax1.legend(loc="upper right", fontsize=11)
    ax1.grid(True, alpha=0.3)

    # Residuals
    residuals = df_plot["ETo_calculated"] - df_plot["ETo_reference"]
    ax2.bar(df_plot.index, residuals, color="gray", alpha=0.6, width=1)
    ax2.axhline(y=0, color="r", linestyle="--", linewidth=2)

    ax2.set_xlabel("Date", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Residuals (mm/day)", fontsize=12, fontweight="bold")
    ax2.set_title("Residuals (EVAonline - Reference)", fontsize=12)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save plot
    output_dir = (
        BRASIL_RESULTS_DIR if region == "brasil" else MUNDO_RESULTS_DIR
    )
    plots_dir = output_dir / "plots"

    output_file = plots_dir / f"{city_key}_timeseries.png"
    plt.savefig(output_file, dpi=PLOT_CONFIG["dpi"], bbox_inches="tight")
    plt.close()

    print(f"  ✅ Time series plot saved: {output_file.name}")


# ============================================================================
# RESIDUAL ANALYSIS PLOT
# ============================================================================


def plot_residuals(city_key: str, region: str, df: pd.DataFrame):
    """
    Create residual analysis plots.

    Args:
        city_key: City identifier
        region: 'brasil' or 'mundo'
        df: DataFrame with ETo columns
    """
    metadata = get_city_metadata(city_key, region)
    city_name = metadata.get("name", city_key)

    residuals = df["ETo_calculated"] - df["ETo_reference"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Residuals vs Predicted
    axes[0, 0].scatter(
        df["ETo_calculated"], residuals, alpha=0.5, s=20, c="steelblue"
    )
    axes[0, 0].axhline(y=0, color="r", linestyle="--", linewidth=2)
    axes[0, 0].set_xlabel("Predicted ETo (mm/day)", fontweight="bold")
    axes[0, 0].set_ylabel("Residuals (mm/day)", fontweight="bold")
    axes[0, 0].set_title("Residuals vs Predicted", fontweight="bold")
    axes[0, 0].grid(True, alpha=0.3)

    # 2. Histogram of residuals
    axes[0, 1].hist(
        residuals, bins=50, color="steelblue", alpha=0.7, edgecolor="black"
    )
    axes[0, 1].axvline(x=0, color="r", linestyle="--", linewidth=2)
    axes[0, 1].set_xlabel("Residuals (mm/day)", fontweight="bold")
    axes[0, 1].set_ylabel("Frequency", fontweight="bold")
    axes[0, 1].set_title(
        f"Residuals Distribution (mean={residuals.mean():.3f})",
        fontweight="bold",
    )
    axes[0, 1].grid(True, alpha=0.3, axis="y")

    # 3. Q-Q plot
    stats.probplot(residuals, dist="norm", plot=axes[1, 0])
    axes[1, 0].set_title("Normal Q-Q Plot", fontweight="bold")
    axes[1, 0].grid(True, alpha=0.3)

    # 4. Box plot by month
    df_month = df.copy()
    df_month["month"] = df_month.index.month
    df_month["residuals"] = residuals

    months = range(1, 13)
    month_data = [
        df_month[df_month["month"] == m]["residuals"].values for m in months
    ]

    bp = axes[1, 1].boxplot(
        month_data,
        labels=[f"{m:02d}" for m in months],
        patch_artist=True,
        showmeans=True,
    )

    for patch in bp["boxes"]:
        patch.set_facecolor("lightblue")

    axes[1, 1].axhline(y=0, color="r", linestyle="--", linewidth=2)
    axes[1, 1].set_xlabel("Month", fontweight="bold")
    axes[1, 1].set_ylabel("Residuals (mm/day)", fontweight="bold")
    axes[1, 1].set_title("Monthly Residuals Distribution", fontweight="bold")
    axes[1, 1].grid(True, alpha=0.3, axis="y")

    fig.suptitle(
        f"Residual Analysis: {city_name} ({region.upper()})",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    plt.tight_layout()

    # Save plot
    output_dir = (
        BRASIL_RESULTS_DIR if region == "brasil" else MUNDO_RESULTS_DIR
    )
    plots_dir = output_dir / "plots"

    output_file = plots_dir / f"{city_key}_residuals.png"
    plt.savefig(output_file, dpi=PLOT_CONFIG["dpi"], bbox_inches="tight")
    plt.close()

    print(f"  ✅ Residual analysis saved: {output_file.name}")


# ============================================================================
# REGIONAL SUMMARY PLOTS
# ============================================================================


def plot_regional_summary(region: str):
    """
    Create summary plots for all cities in a region.

    Args:
        region: 'brasil' or 'mundo'
    """
    # Load metrics
    output_dir = (
        BRASIL_RESULTS_DIR if region == "brasil" else MUNDO_RESULTS_DIR
    )
    metrics_file = output_dir / "metrics" / f"metrics_{region}.csv"

    if not metrics_file.exists():
        print(f"❌ Metrics file not found: {metrics_file}")
        return

    df = pd.read_csv(metrics_file)

    print(f"\n{'='*70}")
    print(f"Creating regional summary plots for {region.upper()}")
    print(f"{'='*70}")

    # 1. Bar plot of metrics by city
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    cities = df["city_name"].values
    metrics_to_plot = ["mae", "rmse", "r2", "nse"]
    titles = [
        "Mean Absolute Error (mm/day)",
        "Root Mean Square Error (mm/day)",
        "Coefficient of Determination",
        "Nash-Sutcliffe Efficiency",
    ]

    for idx, (metric, title) in enumerate(zip(metrics_to_plot, titles)):
        ax = axes[idx // 2, idx % 2]

        values = df[metric].values
        colors = (
            [
                "green" if v >= 0.8 else "orange" if v >= 0.6 else "red"
                for v in values
            ]
            if metric in ["r2", "nse"]
            else [
                "green" if v <= 0.4 else "orange" if v <= 0.6 else "red"
                for v in values
            ]
        )

        ax.barh(cities, values, color=colors, alpha=0.7, edgecolor="black")
        ax.set_xlabel(title, fontweight="bold")
        ax.set_title(title, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="x")

        # Add threshold lines
        if metric in ["r2", "nse"]:
            ax.axvline(
                x=0.8,
                color="darkgreen",
                linestyle="--",
                linewidth=1.5,
                alpha=0.5,
            )
            ax.axvline(
                x=0.6, color="orange", linestyle="--", linewidth=1.5, alpha=0.5
            )
        elif metric in ["mae", "rmse"]:
            ax.axvline(
                x=0.4,
                color="darkgreen",
                linestyle="--",
                linewidth=1.5,
                alpha=0.5,
            )
            ax.axvline(
                x=0.6, color="orange", linestyle="--", linewidth=1.5, alpha=0.5
            )

    fig.suptitle(
        f"Validation Metrics Summary: {region.upper()}",
        fontsize=16,
        fontweight="bold",
    )
    plt.tight_layout()

    output_file = output_dir / "plots" / f"summary_{region}_metrics.png"
    plt.savefig(output_file, dpi=PLOT_CONFIG["dpi"], bbox_inches="tight")
    plt.close()

    print(f"✅ Summary metrics plot saved: {output_file.name}")

    # 2. Quality distribution pie chart
    fig, ax = plt.subplots(figsize=(10, 8))

    quality_counts = df["quality"].value_counts()
    colors_pie = {
        "excellent": "darkgreen",
        "good": "lightgreen",
        "acceptable": "orange",
        "poor": "red",
    }
    colors = [colors_pie.get(q, "gray") for q in quality_counts.index]

    ax.pie(
        quality_counts.values,
        labels=quality_counts.index,
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
        textprops={"fontsize": 12, "fontweight": "bold"},
    )
    ax.set_title(
        f"Validation Quality Distribution: {region.upper()}",
        fontsize=14,
        fontweight="bold",
    )

    output_file = output_dir / "plots" / f"summary_{region}_quality.png"
    plt.savefig(output_file, dpi=PLOT_CONFIG["dpi"], bbox_inches="tight")
    plt.close()

    print(f"✅ Quality distribution plot saved: {output_file.name}")


# ============================================================================
# CONSOLIDATED COMPARISON
# ============================================================================


def plot_consolidated_comparison():
    """Create consolidated comparison plots for Brasil vs Mundo."""
    print(f"\n{'='*70}")
    print("Creating consolidated comparison plots")
    print(f"{'='*70}")

    # Load metrics
    global_metrics_file = CONSOLIDATED_DIR / "global_metrics.csv"

    if not global_metrics_file.exists():
        print(f"❌ Global metrics file not found: {global_metrics_file}")
        return

    df = pd.read_csv(global_metrics_file)

    # Box plots comparing regions
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    metrics = ["mae", "rmse", "r2", "nse"]
    titles = ["MAE (mm/day)", "RMSE (mm/day)", "r²", "NSE"]

    for idx, (metric, title) in enumerate(zip(metrics, titles)):
        ax = axes[idx // 2, idx % 2]

        data = [
            df[df["region"] == "brasil"][metric].dropna(),
            df[df["region"] == "mundo"][metric].dropna(),
        ]

        bp = ax.boxplot(
            data, labels=["Brasil", "Mundo"], patch_artist=True, showmeans=True
        )

        for patch, color in zip(bp["boxes"], ["lightblue", "lightcoral"]):
            patch.set_facecolor(color)

        ax.set_ylabel(title, fontweight="bold")
        ax.set_title(title, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle(
        "Brasil vs Global Validation Comparison",
        fontsize=16,
        fontweight="bold",
    )
    plt.tight_layout()

    output_file = CONSOLIDATED_DIR / "comparison_brasil_mundo.png"
    plt.savefig(output_file, dpi=PLOT_CONFIG["dpi"], bbox_inches="tight")
    plt.close()

    print(f"✅ Consolidated comparison saved: {output_file.name}")


# ============================================================================
# BATCH PROCESSING
# ============================================================================


def visualize_city(city_key: str, region: str):
    """Generate all plots for a single city."""
    print(f"\nGenerating plots for {city_key}...")

    try:
        # Load combined data
        output_dir = (
            BRASIL_RESULTS_DIR if region == "brasil" else MUNDO_RESULTS_DIR
        )
        file_path = (
            output_dir / "timeseries" / f"{city_key}_eto_calculated.csv"
        )

        if not file_path.exists():
            print(f"  ❌ Data file not found: {file_path.name}")
            return

        df_calc = pd.read_csv(file_path, parse_dates=["date"])
        df_calc.set_index("date", inplace=True)

        # Load reference
        ref_path = get_eto_file_path(city_key, region)
        df_ref = pd.read_csv(ref_path, parse_dates=["date"])
        df_ref.set_index("date", inplace=True)

        # Merge
        df = df_ref.join(df_calc, how="inner", rsuffix="_calculated")
        df.rename(
            columns={
                "ETo": "ETo_reference",
                "ETo_calculated": "ETo_calculated",
            },
            inplace=True,
        )

        if df.empty:
            print(f"  ❌ No overlapping data")
            return

        # Generate plots
        plot_scatter(city_key, region, df)
        plot_timeseries(city_key, region, df)
        plot_residuals(city_key, region, df)

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")


def visualize_region(region: str):
    """Generate all plots for a region."""
    cities = get_all_cities(region)

    print(f"\n{'='*70}")
    print(
        f"Generating visualizations for {region.upper()} ({len(cities)} cities)"
    )
    print(f"{'='*70}")

    for city_key in cities:
        visualize_city(city_key, region)

    plot_regional_summary(region)


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate validation visualizations for EVAonline"
    )
    parser.add_argument(
        "--region",
        choices=["brasil", "mundo", "both"],
        default="both",
        help="Region to visualize (default: both)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("EVAonline Validation - Visualization")
    print("=" * 70)

    if args.region in ["brasil", "both"]:
        visualize_region("brasil")

    if args.region in ["mundo", "both"]:
        visualize_region("mundo")

    if args.region == "both":
        plot_consolidated_comparison()

    print("\n" + "=" * 70)
    print("✅ VISUALIZATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
