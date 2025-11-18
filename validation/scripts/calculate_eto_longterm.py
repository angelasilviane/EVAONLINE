"""
EVAonline Long-Term Validation - Optimized for 30+ years of data (1991-2024).

This script is specifically optimized for the REAL validation period:
- Brasil: 1991-2024 (33 years, ~12,000 days) - API limitation
- Mundo: 1991-2024 (33 years, ~12,000 days)

NOTE: Original Xavier dataset covers 1961-2024, but our data fusion APIs
have a minimum date of 1990-01-01. Using 1991-01-01 as safe start date.

KEY OPTIMIZATIONS:
1. **Annual batches**: 365-day chunks for reliability
2. **Incremental cache**: Saves progress after each year
3. **Automatic retry**: 3 attempts per batch with exponential backoff
4. **Rate limiting**: 1-2 seconds between requests to avoid blocking
5. **Progress recovery**: Resume from last successful batch if interrupted
6. **Memory efficient**: Processes year-by-year, not all at once

Usage:
    # Test 1 city (recommended first)
    python validation/scripts/calculate_eto_longterm.py --region brasil --max-cities 1

    # Full Brasil validation (17 cities × 33 years = ~204,000 days!)
    python validation/scripts/calculate_eto_longterm.py --region brasil

    # Full Global validation (10 cities × 33 years = ~120,000 days!)
    python validation/scripts/calculate_eto_longterm.py --region mundo

    # Custom year range (must be >= 1991)
    python validation/scripts/calculate_eto_longterm.py --region brasil --start-year 2010 --end-year 2024
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from loguru import logger
import warnings

warnings.filterwarnings("ignore")

# Import EVAonline production modules
from validation.config import (
    get_all_cities,
    get_eto_file_path,
    get_city_metadata,
    BRASIL_RESULTS_DIR,
    MUNDO_RESULTS_DIR,
)

# Import validation-specific historical data downloader
from validation.data_download_historical import (
    download_historical_weather_data,
)

from validation_logic_eto.api.services.opentopo.opentopo_sync_adapter import (
    OpenTopoSyncAdapter,
)
from validation_logic_eto.core.eto_calculation.eto_services import EToCalculationService
from validation_logic_eto.api.services.weather_utils import ElevationUtils


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)
logger.add(
    project_root / "validation" / "results" / "longterm_validation.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",
    rotation="50 MB",
    retention="14 days",
)


# ============================================================================
# REFERENCE DATA LOADING
# ============================================================================


def load_reference_periods(city_key: str, region: str) -> Dict[str, any]:
    """Load available date ranges from reference ETo CSV."""
    csv_path = get_eto_file_path(city_key, region)

    if not csv_path.exists():
        raise FileNotFoundError(f"Reference file not found: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=[0], nrows=1)
    date_col = df.columns[0]

    # Read first and last line for date range
    df_full = pd.read_csv(csv_path, parse_dates=[date_col])

    start_date = df_full[date_col].min()
    end_date = df_full[date_col].max()

    return {
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d"),
        "total_days": len(df_full),
        "start_year": start_date.year,
        "end_year": end_date.year,
    }


# ============================================================================
# LONG-TERM ETO CALCULATION (OPTIMIZED)
# ============================================================================


async def calculate_eto_longterm(
    city_key: str,
    region: str,
    start_year: int,
    end_year: int,
    rate_limit_seconds: float = 1.5,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Calculate ETo for long periods (30+ years) with optimizations.

    Features:
    - Annual batches (365 days each)
    - Incremental cache (resume from failures)
    - Automatic retry (3 attempts per year)
    - Rate limiting (avoid API blocks)
    - Progress tracking

    Args:
        city_key: City identifier
        region: 'brasil' or 'mundo'
        start_year: Start year (e.g., 1991)
        end_year: End year (e.g., 2024)
        rate_limit_seconds: Delay between API calls (default: 1.5s)

    Returns:
        Tuple (DataFrame with ETo, list of warnings)
    """
    metadata = get_city_metadata(city_key, region)
    lat = metadata["lat"]
    lon = metadata["lon"]
    city_name = metadata.get("name", city_key)

    logger.info(f"\n{'='*80}")
    logger.info(f"🌍 LONG-TERM VALIDATION: {city_name}")
    logger.info(f"📍 Location: ({lat:.2f}, {lon:.2f})")
    logger.info(
        f"📅 Period: {start_year} - {end_year} ({end_year - start_year + 1} years)"
    )
    logger.info(f"{'='*80}")

    all_warnings = []

    # Step 1: Get elevation
    logger.info("\n📐 Step 1/4: Fetching elevation...")
    try:
        opentopo = OpenTopoSyncAdapter()
        elevation_result = opentopo.get_elevation_sync(lat, lon)
        elevation = elevation_result["elevation"]
        logger.info(
            f"   ✅ Elevation: {elevation:.1f}m (source: {elevation_result['source']})"
        )
    except Exception as e:
        elevation = metadata.get("elevation", 500)
        logger.warning(f"   ⚠️  Using fallback elevation: {elevation}m")

    elevation_factors = ElevationUtils.get_elevation_correction_factor(
        elevation
    )

    # Step 2: Setup cache
    output_dir = (
        BRASIL_RESULTS_DIR if region == "brasil" else MUNDO_RESULTS_DIR
    )
    cache_dir = output_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{city_key}_{start_year}_{end_year}.parquet"

    # Check for existing cache
    cached_years = set()
    if cache_file.exists():
        try:
            df_cached = pd.read_parquet(cache_file)
            cached_years = set(df_cached.index.year.unique())
            logger.info(
                f"\n📦 Step 2/4: Found cached data for {len(cached_years)} years"
            )
            logger.info(f"   Years cached: {sorted(cached_years)}")
        except Exception as e:
            logger.warning(f"   ⚠️  Could not load cache: {e}")
            df_cached = pd.DataFrame()
    else:
        df_cached = pd.DataFrame()
        logger.info(f"\n📦 Step 2/4: No cache found, will process all years")

    # Step 3: Download and calculate year-by-year
    logger.info(
        f"\n📡 Step 3/4: Processing {end_year - start_year + 1} years..."
    )

    all_eto_data = []
    if not df_cached.empty:
        all_eto_data.append(df_cached)

    years_to_process = [
        y for y in range(start_year, end_year + 1) if y not in cached_years
    ]

    if not years_to_process:
        logger.success(f"   ✅ All years already cached!")
        return df_cached, all_warnings

    logger.info(f"   Years to process: {len(years_to_process)}")

    for i, year in enumerate(years_to_process, 1):
        year_start = f"{year}-01-01"
        year_end = f"{year}-12-31"

        # Adjust for partial years
        if year == end_year:
            periods = load_reference_periods(city_key, region)
            ref_end = datetime.strptime(periods["end"], "%Y-%m-%d")
            if ref_end.year == end_year:
                year_end = periods["end"]

        logger.info(
            f"\n   [{i}/{len(years_to_process)}] Year {year}: {year_start} to {year_end}"
        )

        # Retry logic
        max_retries = 3
        retry_delay = 5
        df_year_eto = None

        for attempt in range(1, max_retries + 1):
            try:
                # Rate limiting
                if i > 1:
                    await asyncio.sleep(rate_limit_seconds)

                # Download historical data using validation-specific downloader
                # This bypasses mode detection and source manager restrictions
                logger.debug(
                    f"      Downloading climate data (attempt {attempt})..."
                )

                df_weather, warnings = await download_historical_weather_data(
                    latitude=lat,
                    longitude=lon,
                    start_date=year_start,
                    end_date=year_end,
                )

                if warnings:
                    all_warnings.extend(warnings[:2])  # Limit warnings

                if df_weather.empty:
                    if attempt < max_retries:
                        logger.warning(
                            f"      ⚠️  No data, retry {attempt}/{max_retries}..."
                        )
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        raise ValueError("No data after retries")

                # Calculate ETo
                logger.debug(
                    f"      Calculating ETo for {len(df_weather)} days..."
                )
                eto_service = EToCalculationService()
                eto_results = []

                for idx, row in df_weather.iterrows():
                    measurements = {
                        "date": (
                            str(idx.date())
                            if hasattr(idx, "date")
                            else str(idx)
                        ),
                        "latitude": lat,
                        "longitude": lon,
                        "elevation_m": elevation,
                        "T2M_MAX": row.get("T2M_MAX"),
                        "T2M_MIN": row.get("T2M_MIN"),
                        "T2M_MEAN": row.get(
                            "T2M_MEAN",
                            (row.get("T2M_MAX", 0) + row.get("T2M_MIN", 0))
                            / 2,
                        ),
                        "RH2M": row.get("RH2M"),
                        "WS2M": row.get("WS2M"),
                        "ALLSKY_SFC_SW_DWN": row.get("ALLSKY_SFC_SW_DWN"),
                        "PRECTOTCORR": row.get("PRECTOTCORR", 0.0),
                    }

                    result = eto_service.calculate_et0(
                        measurements, elevation_factors=elevation_factors
                    )
                    eto_results.append(
                        {
                            "date": measurements["date"],
                            "ETo": result["et0_mm_day"],
                        }
                    )

                df_year_eto = pd.DataFrame(eto_results)
                df_year_eto["date"] = pd.to_datetime(df_year_eto["date"])
                df_year_eto.set_index("date", inplace=True)

                logger.info(
                    f"      ✅ Calculated {len(df_year_eto)} days (ETo: {df_year_eto['ETo'].mean():.2f} mm/day)"
                )
                break  # Success

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(
                        f"      ⚠️  Error (attempt {attempt}): {str(e)[:100]}"
                    )
                    await asyncio.sleep(
                        retry_delay * attempt
                    )  # Exponential backoff
                else:
                    msg = f"Year {year} failed after {max_retries} attempts: {str(e)}"
                    logger.error(f"      ❌ {msg}")
                    all_warnings.append(msg)

        # Add to results and save incremental progress
        if df_year_eto is not None and not df_year_eto.empty:
            all_eto_data.append(df_year_eto)

            # Save incremental cache
            df_combined = pd.concat(
                all_eto_data, ignore_index=False
            ).sort_index()
            df_combined.to_parquet(cache_file)
            logger.debug(
                f"      💾 Progress saved ({len(df_combined)} days total)"
            )

        # Progress indicator
        progress_pct = 100 * i / len(years_to_process)
        elapsed_years = i
        remaining_years = len(years_to_process) - i
        logger.info(
            f"      📊 Progress: {progress_pct:.1f}% | Completed: {elapsed_years} | Remaining: {remaining_years}"
        )

    # Step 4: Final consolidation
    logger.info(f"\n💾 Step 4/4: Final consolidation...")

    if not all_eto_data:
        raise ValueError("No ETo data calculated")

    df_final = pd.concat(all_eto_data, ignore_index=False).sort_index()
    df_final = df_final[~df_final.index.duplicated(keep="last")]

    # Save final CSV
    timeseries_dir = output_dir / "timeseries"
    timeseries_dir.mkdir(parents=True, exist_ok=True)
    output_file = timeseries_dir / f"{city_key}_eto_calculated.csv"
    df_final.to_csv(output_file, date_format="%Y-%m-%d")

    logger.info(f"   ✅ Saved {len(df_final)} days to: {output_file.name}")
    logger.info(f"   📈 ETo statistics:")
    logger.info(f"      Mean: {df_final['ETo'].mean():.2f} mm/day")
    logger.info(f"      Min:  {df_final['ETo'].min():.2f} mm/day")
    logger.info(f"      Max:  {df_final['ETo'].max():.2f} mm/day")
    logger.info(f"      Std:  {df_final['ETo'].std():.2f} mm/day")

    # Cleanup cache
    try:
        cache_file.unlink()
        logger.debug(f"   🗑️  Cleaned up cache file")
    except:
        pass

    return df_final, all_warnings


# ============================================================================
# BATCH PROCESSING
# ============================================================================


async def validate_region_longterm(
    region: str,
    max_cities: Optional[int] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
):
    """Validate all cities in a region with long-term data."""
    cities = get_all_cities(region)

    if max_cities:
        cities = cities[:max_cities]

    # Determine date range
    if not start_year or not end_year:
        # Use reference dataset periods
        sample_city = cities[0]
        periods = load_reference_periods(sample_city, region)
        start_year = start_year or periods["start_year"]
        end_year = end_year or periods["end_year"]

    # API LIMITATION: Start date cannot be before 1991-01-01
    # OpenMeteo Archive supports from 1940, but our data fusion
    # has minimum date of 1990-01-01 (or 1991 to be safe)
    MIN_SUPPORTED_YEAR = 1991
    if start_year < MIN_SUPPORTED_YEAR:
        logger.warning(
            f"⚠️  Start year {start_year} is before API minimum "
            f"({MIN_SUPPORTED_YEAR}). Adjusting to {MIN_SUPPORTED_YEAR}."
        )
        start_year = MIN_SUPPORTED_YEAR

    total_years = end_year - start_year + 1

    logger.info(f"\n{'='*80}")
    logger.info(f"🌎 LONG-TERM VALIDATION - {region.upper()}")
    logger.info(f"{'='*80}")
    logger.info(f"📍 Cities: {len(cities)}")
    logger.info(f"📅 Period: {start_year}-{end_year} ({total_years} years)")
    logger.info(f"📊 Total days: ~{total_years * 365 * len(cities):,}")
    logger.info(
        f"⏱️  Estimated time: {len(cities) * total_years * 2 / 60:.0f}-{len(cities) * total_years * 4 / 60:.0f} minutes"
    )
    logger.info(f"{'='*80}")

    results = {"success": [], "failed": []}
    overall_start = time.time()

    for i, city_key in enumerate(cities, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"[{i}/{len(cities)}] {city_key}")
        logger.info(f"{'='*80}")

        city_start = time.time()

        try:
            df_eto, warnings = await calculate_eto_longterm(
                city_key, region, start_year, end_year
            )

            results["success"].append(city_key)

            city_elapsed = time.time() - city_start
            logger.success(f"\n✅ Completed in {city_elapsed/60:.1f} minutes")

            if warnings:
                logger.warning(f"⚠️  {len(warnings)} warnings")

        except Exception as e:
            results["failed"].append(city_key)
            logger.error(f"\n❌ Failed: {str(e)}")

    # Summary
    overall_elapsed = time.time() - overall_start

    logger.info(f"\n{'='*80}")
    logger.info(f"📊 FINAL SUMMARY - {region.upper()}")
    logger.info(f"{'='*80}")
    logger.info(f"✅ Successful: {len(results['success'])}/{len(cities)}")
    logger.info(f"❌ Failed: {len(results['failed'])}/{len(cities)}")
    logger.info(
        f"⏱️  Total time: {overall_elapsed/60:.1f} minutes ({overall_elapsed/3600:.2f} hours)"
    )

    if results["failed"]:
        logger.warning(f"\nFailed cities: {', '.join(results['failed'])}")

    return results


# ============================================================================
# MAIN
# ============================================================================


async def main():
    parser = argparse.ArgumentParser(
        description="Long-term ETo validation (1991-2024) with optimizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--region", choices=["brasil", "mundo", "both"], default="brasil"
    )
    parser.add_argument(
        "--max-cities", type=int, default=None, help="Limit number of cities"
    )
    parser.add_argument(
        "--start-year", type=int, default=None, help="Override start year"
    )
    parser.add_argument(
        "--end-year", type=int, default=None, help="Override end year"
    )

    args = parser.parse_args()

    logger.info("\n" + "=" * 80)
    logger.info("🚀 EVAonline Long-Term Validation Pipeline")
    logger.info("=" * 80)

    if args.region in ["brasil", "both"]:
        await validate_region_longterm(
            args.region if args.region != "both" else "brasil",
            args.max_cities,
            args.start_year,
            args.end_year,
        )

    if args.region in ["mundo", "both"]:
        await validate_region_longterm(
            "mundo", args.max_cities, args.start_year, args.end_year
        )

    logger.success("\n✅ ALL DONE!")


if __name__ == "__main__":
    asyncio.run(main())
