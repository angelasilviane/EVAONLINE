"""
Calculate validation metrics comparing EVAonline ETo with reference datasets.

This script computes statistical metrics (MAE, RMSE, r², NSE, etc.) for:
- Brazil: EVAonline vs Xavier et al. (2016)
- Global: EVAonline vs OpenMeteo Archive

Usage:
    python validation/scripts/compare_metrics.py --region brasil
    python validation/scripts/compare_metrics.py --region mundo
    python validation/scripts/compare_metrics.py --region both
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import argparse
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict
import warnings

warnings.filterwarnings("ignore")

from validation.config import (
    get_all_cities,
    get_eto_file_path,
    get_city_metadata,
    VALIDATION_METRICS,
    QUALITY_THRESHOLDS,
    BRASIL_RESULTS_DIR,
    MUNDO_RESULTS_DIR,
    CONSOLIDATED_DIR,
)


# ============================================================================
# METRICS CALCULATION FUNCTIONS
# ============================================================================


def calculate_mae(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Error (mm/day)"""
    return np.mean(np.abs(observed - predicted))


def calculate_rmse(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Square Error (mm/day)"""
    return np.sqrt(np.mean((observed - predicted) ** 2))


def calculate_mbe(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Bias Error (mm/day)"""
    return np.mean(predicted - observed)


def calculate_mape(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Percentage Error (%)"""
    # Avoid division by zero
    mask = observed != 0
    if not np.any(mask):
        return np.nan
    return (
        np.mean(np.abs((observed[mask] - predicted[mask]) / observed[mask]))
        * 100
    )


def calculate_r(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Pearson correlation coefficient"""
    if len(observed) < 2:
        return np.nan
    r, _ = stats.pearsonr(observed, predicted)
    return r


def calculate_r2(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Coefficient of determination"""
    r = calculate_r(observed, predicted)
    return r**2 if not np.isnan(r) else np.nan


def calculate_nse(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Nash-Sutcliffe Efficiency"""
    mean_observed = np.mean(observed)
    numerator = np.sum((observed - predicted) ** 2)
    denominator = np.sum((observed - mean_observed) ** 2)

    if denominator == 0:
        return np.nan

    return 1 - (numerator / denominator)


def calculate_d(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Willmott's Index of Agreement"""
    mean_observed = np.mean(observed)
    numerator = np.sum((observed - predicted) ** 2)
    denominator = np.sum(
        (np.abs(predicted - mean_observed) + np.abs(observed - mean_observed))
        ** 2
    )

    if denominator == 0:
        return np.nan

    return 1 - (numerator / denominator)


def calculate_kge(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Kling-Gupta Efficiency"""
    r = calculate_r(observed, predicted)

    mean_sim = np.mean(predicted)
    mean_obs = np.mean(observed)
    std_sim = np.std(predicted)
    std_obs = np.std(observed)

    if std_obs == 0 or np.isnan(r):
        return np.nan

    # KGE components
    beta = mean_sim / mean_obs if mean_obs != 0 else np.nan
    gamma = (
        (std_sim / mean_sim) / (std_obs / mean_obs)
        if (mean_obs != 0 and mean_sim != 0)
        else np.nan
    )

    if np.isnan(beta) or np.isnan(gamma):
        return np.nan

    # KGE calculation
    kge = 1 - np.sqrt((r - 1) ** 2 + (beta - 1) ** 2 + (gamma - 1) ** 2)

    return kge


def calculate_pbias(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Percent Bias (%)"""
    sum_obs = np.sum(observed)
    if sum_obs == 0:
        return np.nan

    pbias = 100 * np.sum(predicted - observed) / sum_obs
    return pbias


def calculate_all_metrics(
    observed: np.ndarray, predicted: np.ndarray
) -> Dict[str, float]:
    """
    Calculate all validation metrics.

    Args:
        observed: Reference ETo values (mm/day)
        predicted: EVAonline calculated ETo values (mm/day)

    Returns:
        Dictionary with all metrics
    """
    # Remove NaN values
    mask = ~(np.isnan(observed) | np.isnan(predicted))
    obs = observed[mask]
    pred = predicted[mask]

    if len(obs) < 10:  # Minimum sample size
        return {
            metric: np.nan for metric in VALIDATION_METRICS + ["n_samples"]
        }

    metrics = {
        "mae": calculate_mae(obs, pred),
        "rmse": calculate_rmse(obs, pred),
        "mbe": calculate_mbe(obs, pred),
        "mape": calculate_mape(obs, pred),
        "r": calculate_r(obs, pred),
        "r2": calculate_r2(obs, pred),
        "nse": calculate_nse(obs, pred),
        "d": calculate_d(obs, pred),
        "kge": calculate_kge(obs, pred),
        "pbias": calculate_pbias(obs, pred),
        "n_samples": len(obs),
    }

    return metrics


def assess_quality(metrics: Dict[str, float]) -> str:
    """
    Assess validation quality based on metric thresholds.

    Args:
        metrics: Dictionary with calculated metrics

    Returns:
        Quality level: 'excellent', 'good', 'acceptable', or 'poor'
    """
    mae = metrics.get("mae", np.inf)
    rmse = metrics.get("rmse", np.inf)
    r2 = metrics.get("r2", 0)
    nse = metrics.get("nse", -np.inf)
    d = metrics.get("d", 0)

    # Check excellent thresholds
    if (
        mae <= QUALITY_THRESHOLDS["excellent"]["mae"]
        and rmse <= QUALITY_THRESHOLDS["excellent"]["rmse"]
        and r2 >= QUALITY_THRESHOLDS["excellent"]["r2"]
        and nse >= QUALITY_THRESHOLDS["excellent"]["nse"]
        and d >= QUALITY_THRESHOLDS["excellent"]["d"]
    ):
        return "excellent"

    # Check good thresholds
    if (
        mae <= QUALITY_THRESHOLDS["good"]["mae"]
        and rmse <= QUALITY_THRESHOLDS["good"]["rmse"]
        and r2 >= QUALITY_THRESHOLDS["good"]["r2"]
        and nse >= QUALITY_THRESHOLDS["good"]["nse"]
        and d >= QUALITY_THRESHOLDS["good"]["d"]
    ):
        return "good"

    # Check acceptable thresholds
    if (
        mae <= QUALITY_THRESHOLDS["acceptable"]["mae"]
        and rmse <= QUALITY_THRESHOLDS["acceptable"]["rmse"]
        and r2 >= QUALITY_THRESHOLDS["acceptable"]["r2"]
        and nse >= QUALITY_THRESHOLDS["acceptable"]["nse"]
        and d >= QUALITY_THRESHOLDS["acceptable"]["d"]
    ):
        return "acceptable"

    return "poor"


# ============================================================================
# DATA LOADING AND COMPARISON
# ============================================================================


def load_reference_eto(city_key: str, region: str) -> pd.DataFrame:
    """
    Load reference ETo data from CSV.

    Args:
        city_key: City identifier
        region: 'brasil' or 'mundo'

    Returns:
        DataFrame with date index and ETo_reference column
    """
    file_path = get_eto_file_path(city_key, region)

    if not file_path.exists():
        raise FileNotFoundError(f"Reference ETo file not found: {file_path}")

    # Read CSV (assuming columns: date, ETo)
    df = pd.read_csv(file_path, parse_dates=["date"])
    df.set_index("date", inplace=True)
    df.rename(columns={"ETo": "ETo_reference"}, inplace=True)

    return df[["ETo_reference"]]


def load_calculated_eto(city_key: str, region: str) -> pd.DataFrame:
    """
    Load calculated ETo data from validation results.

    Args:
        city_key: City identifier
        region: 'brasil' or 'mundo'

    Returns:
        DataFrame with date index and ETo_calculated column
    """
    # Path to calculated ETo file (generated by calculate_eto_validation.py)
    output_dir = (
        BRASIL_RESULTS_DIR if region == "brasil" else MUNDO_RESULTS_DIR
    )
    file_path = output_dir / "timeseries" / f"{city_key}_eto_calculated.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Calculated ETo file not found: {file_path}\n"
            f"Run 'python validation/scripts/calculate_eto_validation.py' first."
        )

    df = pd.read_csv(file_path, parse_dates=["date"])
    df.set_index("date", inplace=True)
    df.rename(columns={"ETo": "ETo_calculated"}, inplace=True)

    return df[["ETo_calculated"]]


def compare_city_eto(city_key: str, region: str) -> Dict[str, any]:
    """
    Compare reference and calculated ETo for a single city.

    Args:
        city_key: City identifier
        region: 'brasil' or 'mundo'

    Returns:
        Dictionary with comparison results and metrics
    """
    print(f"  Processing {city_key}...", end=" ")

    try:
        # Load data
        df_ref = load_reference_eto(city_key, region)
        df_calc = load_calculated_eto(city_key, region)

        # Merge on date index
        df = df_ref.join(df_calc, how="inner")

        if df.empty:
            print("❌ No overlapping dates")
            return None

        # Calculate metrics
        observed = df["ETo_reference"].values
        predicted = df["ETo_calculated"].values

        metrics = calculate_all_metrics(observed, predicted)
        quality = assess_quality(metrics)

        # Get city metadata
        metadata = get_city_metadata(city_key, region)

        result = {
            "city_key": city_key,
            "city_name": metadata.get("name", city_key),
            "region": region,
            **metrics,
            "quality": quality,
        }

        # Add metadata fields
        if region == "brasil":
            result["state"] = metadata.get("state", "")
            result["climate_region"] = metadata.get("region", "")
        else:
            result["country"] = metadata.get("country", "")
            result["continent"] = metadata.get("continent", "")

        result["latitude"] = metadata.get("lat", np.nan)
        result["longitude"] = metadata.get("lon", np.nan)
        result["elevation"] = metadata.get("elevation", np.nan)
        result["climate"] = metadata.get("climate", "")

        quality_icon = {
            "excellent": "🌟",
            "good": "✅",
            "acceptable": "⚠️",
            "poor": "❌",
        }

        print(
            f"{quality_icon[quality]} {quality.upper()} (r²={metrics['r2']:.3f}, MAE={metrics['mae']:.3f})"
        )

        return result

    except FileNotFoundError as e:
        print(f"❌ {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


# ============================================================================
# BATCH PROCESSING
# ============================================================================


def compare_region(region: str) -> pd.DataFrame:
    """
    Compare all cities in a region.

    Args:
        region: 'brasil' or 'mundo'

    Returns:
        DataFrame with metrics for all cities
    """
    cities = get_all_cities(region)

    print(f"\n{'='*70}")
    print(f"Validating {region.upper()} region ({len(cities)} cities)")
    print(f"{'='*70}")

    results = []

    for city_key in cities:
        result = compare_city_eto(city_key, region)
        if result is not None:
            results.append(result)

    if not results:
        print(
            "\n❌ No results obtained. Check that calculated ETo files exist."
        )
        return pd.DataFrame()

    df_results = pd.DataFrame(results)

    # Save individual city metrics
    output_dir = (
        BRASIL_RESULTS_DIR if region == "brasil" else MUNDO_RESULTS_DIR
    )
    metrics_dir = output_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    output_file = metrics_dir / f"metrics_{region}.csv"
    df_results.to_csv(output_file, index=False)

    print(f"\n✅ Results saved to: {output_file}")

    # Print summary statistics
    print_summary_statistics(df_results, region)

    return df_results


def print_summary_statistics(df: pd.DataFrame, region: str):
    """Print summary statistics for the region."""
    print(f"\n{'='*70}")
    print(f"SUMMARY STATISTICS - {region.upper()}")
    print(f"{'='*70}")

    print(f"\nNumber of cities: {len(df)}")
    print(f"Total samples: {df['n_samples'].sum():.0f}")

    print("\n📊 Metric Ranges:")
    for metric in ["mae", "rmse", "r2", "nse", "d"]:
        if metric in df.columns:
            print(
                f"  {metric.upper():6s}: {df[metric].min():.3f} - {df[metric].max():.3f} "
                f"(mean: {df[metric].mean():.3f})"
            )

    print("\n🏆 Quality Distribution:")
    quality_counts = df["quality"].value_counts()
    for quality in ["excellent", "good", "acceptable", "poor"]:
        count = quality_counts.get(quality, 0)
        pct = 100 * count / len(df) if len(df) > 0 else 0
        print(f"  {quality.capitalize():12s}: {count:2d} cities ({pct:5.1f}%)")

    print("\n⭐ Top 5 Cities (by r²):")
    top5 = df.nlargest(5, "r2")[["city_name", "r2", "mae", "rmse", "quality"]]
    for idx, row in top5.iterrows():
        print(
            f"  {row['city_name']:30s} r²={row['r2']:.3f}  MAE={row['mae']:.3f}  ({row['quality']})"
        )


# ============================================================================
# CONSOLIDATED ANALYSIS
# ============================================================================


def create_consolidated_report(
    df_brasil: pd.DataFrame, df_mundo: pd.DataFrame
):
    """
    Create consolidated report comparing Brasil and Global validations.

    Args:
        df_brasil: Brazil validation results
        df_mundo: Global validation results
    """
    print(f"\n{'='*70}")
    print("CREATING CONSOLIDATED REPORT")
    print(f"{'='*70}")

    # Combine datasets
    df_all = pd.concat([df_brasil, df_mundo], ignore_index=True)

    # Save combined metrics
    output_file = CONSOLIDATED_DIR / "global_metrics.csv"
    df_all.to_csv(output_file, index=False)
    print(f"\n✅ Global metrics saved to: {output_file}")

    # Regional comparison
    regional_stats = (
        df_all.groupby("region")
        .agg(
            {
                "mae": ["mean", "std", "min", "max"],
                "rmse": ["mean", "std", "min", "max"],
                "r2": ["mean", "std", "min", "max"],
                "nse": ["mean", "std", "min", "max"],
                "d": ["mean", "std", "min", "max"],
                "n_samples": "sum",
            }
        )
        .round(3)
    )

    output_file = CONSOLIDATED_DIR / "regional_comparison.csv"
    regional_stats.to_csv(output_file)
    print(f"✅ Regional comparison saved to: {output_file}")

    # Print comparison
    print("\n" + "=" * 70)
    print("BRASIL vs MUNDO COMPARISON")
    print("=" * 70)
    print(regional_stats)

    # Quality distribution by region
    print("\n📊 Quality Distribution by Region:")
    quality_dist = pd.crosstab(
        df_all["region"], df_all["quality"], margins=True
    )
    print(quality_dist)


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Calculate validation metrics for EVAonline ETo calculations"
    )
    parser.add_argument(
        "--region",
        choices=["brasil", "mundo", "both"],
        default="both",
        help="Region to validate (default: both)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("EVAonline Validation - Metrics Calculation")
    print("=" * 70)

    df_brasil = pd.DataFrame()
    df_mundo = pd.DataFrame()

    if args.region in ["brasil", "both"]:
        df_brasil = compare_region("brasil")

    if args.region in ["mundo", "both"]:
        df_mundo = compare_region("mundo")

    if args.region == "both" and not df_brasil.empty and not df_mundo.empty:
        create_consolidated_report(df_brasil, df_mundo)

    print("\n" + "=" * 70)
    print("✅ VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
