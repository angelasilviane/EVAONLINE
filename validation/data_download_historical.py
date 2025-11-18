"""
Historical Data Download for Validation (1990-2024).

Uses validation-specific modules from validation_logic_eto/ to avoid
DB/Redis/Celery dependencies while maintaining full scientific accuracy.

Key features:
1. NO INFRASTRUCTURE DEPS - no PostgreSQL, Redis, Celery, Docker
2. FULL SCIENTIFIC PIPELINE - preprocessing, Kalman fusion, ETo calculation
3. USES HISTORICAL JSON FILES - replaces DB queries with file access
4. SUPPORTS 1990-2024 period (NASA POWER + OpenMeteo Archive)
5. REAL KALMAN ENSEMBLE - adaptive fusion with historical data

Pipeline:
1. Download from NASA POWER + OpenMeteo Archive
2. Preprocess each source (outlier detection, physical validation)
3. Kalman Ensemble fusion using historical JSON data
4. Quality assessment and completeness checks
"""

from typing import List, Tuple

import numpy as np
import pandas as pd
from loguru import logger

# Import validation-specific modules (no DB/Redis deps)
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


async def download_historical_weather_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    use_fusion: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Download historical weather data for validation (1990-2024).

    COMPLETE PRODUCTION FLOW:
    1. Download from NASA POWER (global, 1990+)
    2. Download from OpenMeteo Archive (global, 1940+)
    3. Preprocess both datasets (outliers, physical validation)
    4. Apply Kalman Ensemble fusion (adaptive weighting)
    5. Return fused dataset ready for ETo calculation

    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        start_date: Start date (YYYY-MM-DD), must be >= 1990-01-01
        end_date: End date (YYYY-MM-DD)
        use_fusion: If True, uses multi-source fusion (default).
            If False, OpenMeteo only.

    Returns:
        Tuple of (DataFrame with climate data, list of warnings)

    Raises:
        ValueError: If coordinates invalid or dates before 1990
    """
    logger.info(
        f"Historical download - "
        f"Period: {start_date} to {end_date}, "
        f"Coord: ({latitude}, {longitude}), "
        f"Fusion: {'ON' if use_fusion else 'OFF'}"
    )
    warnings_list = []

    # Basic validation
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Invalid latitude: {latitude}")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Invalid longitude: {longitude}")

    # Convert dates
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    # Use string format for API calls (avoid Pandas Timestamp issues)
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")

    # Validate minimum date
    MIN_DATE = pd.to_datetime("1990-01-01")
    if start_dt < MIN_DATE:
        raise ValueError(
            f"Start date {start_date} is before minimum supported date "
            f"(1990-01-01)"
        )

    weather_sources = []

    # ============================================================
    # 1. DOWNLOAD NASA POWER (if fusion enabled)
    # ============================================================
    if use_fusion:
        try:
            logger.debug("   Downloading from NASA POWER...")

            # Use ThreadPoolExecutor to avoid asyncio.run() conflicts
            from concurrent.futures import ThreadPoolExecutor

            def download_nasa_in_thread():
                """Run NASA POWER download in separate thread"""
                nasa_adapter = NASAPowerSyncAdapter()
                return nasa_adapter.get_daily_data_sync(
                    lat=latitude,
                    lon=longitude,
                    start_date=start_dt,
                    end_date=end_dt,
                )

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(download_nasa_in_thread)
                nasa_data = future.result(timeout=60)  # 60 second timeout

            if nasa_data:
                # Convert to DataFrame
                data_records = []
                for record in nasa_data:
                    data_records.append(
                        {
                            "date": record.date,  # Already a string
                            "T2M_MAX": record.temp_max,
                            "T2M_MIN": record.temp_min,
                            "T2M": record.temp_mean,
                            "RH2M": record.humidity,
                            "WS2M": record.wind_speed,
                            "ALLSKY_SFC_SW_DWN": record.solar_radiation,
                            "PRECTOTCORR": record.precipitation,
                        }
                    )

                df_nasa = pd.DataFrame(data_records)
                df_nasa["date"] = pd.to_datetime(df_nasa["date"])
                df_nasa.set_index("date", inplace=True)
                df_nasa = df_nasa.replace(-999.00, np.nan)

                # Salvar DataFrame original NASA POWER para depuração
                try:
                    df_nasa.head(30).to_csv("temp/df_nasa_original_head30.csv")
                except Exception as e:
                    logger.warning(
                        f"Falha ao salvar df_nasa_original_head30.csv: {e}"
                    )

                weather_sources.append(df_nasa)
                logger.success(f"   ✅ NASA POWER: {len(df_nasa)} days")
                logger.info(
                    f"   📅 NASA POWER date range: "
                    f"{df_nasa.index.min()} to {df_nasa.index.max()}"
                )
                logger.info("\n" + "=" * 70)
                logger.info("NASA POWER DataFrame (first 5 rows):")
                logger.info(f"\n{df_nasa.head().to_string()}")
                logger.info(f"\nColumns: {list(df_nasa.columns)}")
                logger.info("=" * 70 + "\n")
            else:
                logger.warning("   ⚠️  NASA POWER: No data returned")
                warnings_list.append("NASA POWER returned no data")

        except Exception as e:
            logger.warning(f"   ⚠️  NASA POWER error: {str(e)}")
            warnings_list.append(f"NASA POWER error: {str(e)}")

    # ============================================================
    # 2. DOWNLOAD OPENMETEO ARCHIVE (always)
    # ============================================================
    try:
        logger.debug("Downloading from OpenMeteo Archive...")
        archive_adapter = OpenMeteoArchiveSyncAdapter()

        climate_data = archive_adapter.get_daily_data_sync(
            lat=latitude,
            lon=longitude,
            start_date=start_str,
            end_date=end_str,
        )

        if not climate_data:
            raise ValueError("No data returned from OpenMeteo Archive")

        # Convert to DataFrame
        df_openmeteo = pd.DataFrame(climate_data)

        if "date" in df_openmeteo.columns:
            df_openmeteo["date"] = pd.to_datetime(df_openmeteo["date"])
            df_openmeteo.set_index("date", inplace=True)

        # Harmonize variable names to NASA POWER format
        harmonization = {
            "temperature_2m_max": "T2M_MAX",
            "temperature_2m_min": "T2M_MIN",
            "temperature_2m_mean": "T2M",
            "relative_humidity_2m_mean": "RH2M",
            "wind_speed_10m_mean": "WS2M",
            "shortwave_radiation_sum": "ALLSKY_SFC_SW_DWN",
            "precipitation_sum": "PRECTOTCORR",
        }

        for openmeteo_var, nasa_var in harmonization.items():
            if openmeteo_var in df_openmeteo.columns:
                df_openmeteo.rename(
                    columns={openmeteo_var: nasa_var}, inplace=True
                )

        df_openmeteo = df_openmeteo.replace(-999.00, np.nan)

        # REMOVE OpenMeteo's pre-calculated ETo - we calculate our own
        columns_to_drop = [
            "et0_fao_evapotranspiration",
            "relative_humidity_2m_max",
            "relative_humidity_2m_min",
            "wind_speed_2m_mean",
        ]
        df_openmeteo = df_openmeteo.drop(
            columns=[
                col for col in columns_to_drop if col in df_openmeteo.columns
            ],
            errors="ignore",
        )

        logger.info(
            "   📝 Kept only meteorological variables for ETo calculation"
        )

        # Salvar DataFrame original OpenMeteo para depuração
        try:
            df_openmeteo.head(30).to_csv(
                "temp/df_openmeteo_original_head30.csv"
            )
        except Exception as e:
            logger.warning(
                f"Falha ao salvar df_openmeteo_original_head30.csv: {e}"
            )

        weather_sources.append(df_openmeteo)
        logger.success(f"✅ OpenMeteo Archive: {len(df_openmeteo)} days")
        logger.info(
            f"📅 OpenMeteo date range: "
            f"{df_openmeteo.index.min()} to {df_openmeteo.index.max()}"
        )
        logger.info("\n" + "=" * 70)
        logger.info("OpenMeteo Archive DataFrame (first 5 rows):")
        logger.info(f"\n{df_openmeteo.head().to_string()}")
        logger.info(f"\nColumns: {list(df_openmeteo.columns)}")
        logger.info("=" * 70 + "\n")

    except Exception as e:
        logger.error(f"❌ OpenMeteo Archive error: {str(e)}")
        # OpenMeteo is critical - if it fails and we have no NASA, fail
        if not weather_sources:
            raise
        warnings_list.append(f"OpenMeteo Archive error: {str(e)}")

    if not weather_sources:
        raise ValueError("No data sources returned valid data")

    # ============================================================
    # 3. PREPROCESS DATA (outlier detection, physical validation)
    # ============================================================
    logger.debug("   Preprocessing data...")
    preprocessed_sources = []

    for idx, df_source in enumerate(weather_sources):
        try:
            # Use production preprocessing function
            df_clean, preprocess_warnings = preprocessing(
                weather_df=df_source,
                latitude=latitude,
                cache_key=None,  # No cache for validation
                region="global",  # Use global validation limits
            )
            # Salvar DataFrame pós-pré-processamento para depuração
            try:
                df_clean.head(30).to_csv(
                    f"temp/df_preprocessed_source{idx+1}_head30.csv"
                )
            except Exception as e:
                logger.warning(
                    f"Falha ao salvar df_preprocessed_source{idx+1}_head30.csv: {e}"
                )

            preprocessed_sources.append(df_clean)

            # Add preprocessing warnings to main list
            if preprocess_warnings:
                warnings_list.extend(
                    [f"Source {idx + 1}: {w}" for w in preprocess_warnings]
                )

        except Exception as e:
            import traceback

            logger.warning(
                f" ⚠️  Preprocessing failed for source {idx + 1}: " f"{str(e)}"
            )
            logger.debug(f"Traceback: {traceback.format_exc()}")
            # Use original if preprocessing fails
            preprocessed_sources.append(df_source)

    # ============================================================
    # 4. KALMAN ENSEMBLE FUSION (if multiple sources available)
    # ============================================================
    # Fusion requires at least 2 sources for meaningful averaging
    if use_fusion and len(preprocessed_sources) > 1:
        logger.debug(
            f"Applying Kalman Ensemble fusion "
            f"({len(preprocessed_sources)} sources)..."
        )

        # Log preprocessed data BEFORE fusion
        logger.info("\n" + "=" * 70)
        logger.info(
            f"PREPROCESSED DATA BEFORE FUSION "
            f"({len(preprocessed_sources)} sources):"
        )
        for idx, df_prep in enumerate(preprocessed_sources):
            logger.info(f"\n--- Source {idx + 1} (first 5 rows) ---")
            logger.info(f"\n{df_prep.head().to_string()}")
            logger.info(f"Columns: {list(df_prep.columns)}")
            logger.info(
                f"Date range: {df_prep.index.min()} "
                f"to {df_prep.index.max()}"
            )
            logger.info(f"Shape: {df_prep.shape}")
        logger.info("=" * 70 + "\n")

        try:
            # Initialize new Kalman Ensemble
            kalman_ensemble = ClimateKalmanEnsemble()

            # Verify historical data availability
            logger.info(
                f"\nChecking historical data for "
                f"({latitude:.4f}, {longitude:.4f})..."
            )
            has_ref, ref_data = (
                kalman_ensemble.loader.get_reference_for_location(
                    lat=latitude,
                    lon=longitude,
                    max_dist_km=120,
                )
            )
            if has_ref and ref_data:
                city = ref_data.get("city", "Unknown")
                dist = ref_data.get("distance_km", 0)
                normals = ref_data.get("eto_normal", {})
                logger.info(f"   Historical reference: {city} ({dist} km)")
                logger.info(f"   Found {len(normals)} monthly normals")
                jan_normal = normals.get(1, 0)
                logger.info(f"   Sample normal (Jan): {jan_normal:.3f} mm/day")
            else:
                logger.warning("   No historical data found within 120km")

            # Prepare measurements dict for each day
            # We'll process day by day for proper Kalman filtering
            df_fused_list = []

            # Get date range from first source
            date_index = preprocessed_sources[0].index

            for current_date in date_index:
                # Collect measurements from all sources for this date
                measurements = {}

                for idx, df_source in enumerate(preprocessed_sources):
                    if current_date in df_source.index:
                        row = df_source.loc[current_date]

                        # Map to measurement dict (using Kalman expected keys)
                        source_measurements = {
                            f"temperature_2m_max_src{idx}": row.get("T2M_MAX"),
                            f"temperature_2m_min_src{idx}": row.get("T2M_MIN"),
                            f"temperature_2m_mean_src{idx}": row.get("T2M"),
                            f"relative_humidity_src{idx}": row.get("RH2M"),
                            f"wind_speed_src{idx}": row.get("WS2M"),
                            f"radiation_src{idx}": row.get(
                                "ALLSKY_SFC_SW_DWN"
                            ),
                            f"precipitation_src{idx}": row.get("PRECTOTCORR"),
                        }
                        measurements.update(source_measurements)

                # Skip if no valid measurements
                if not measurements or all(
                    pd.isna(v) for v in measurements.values()
                ):
                    continue

                # LOG: Medidas de entrada para o Kalman
                logger.info(f"KALMAN INPUT | {current_date}: {measurements}")

                try:
                    fused_result = kalman_ensemble.auto_fuse_sync(
                        latitude=latitude,
                        longitude=longitude,
                        measurements=measurements,
                        date=current_date,
                    )

                    # LOG: Resultado bruto do Kalman
                    logger.info(
                        f"KALMAN OUTPUT | {current_date}: {fused_result}"
                    )

                    # Log first result to debug
                    if current_date == date_index[0]:
                        logger.info(
                            f"DEBUG: Fused result type: {type(fused_result)}"
                        )
                        if isinstance(fused_result, dict):
                            keys_str = str(list(fused_result.keys()))
                            logger.info(
                                f"DEBUG: Fused result keys: {keys_str}"
                            )
                            items_sample = dict(list(fused_result.items())[:3])
                            logger.info(f"DEBUG: First values: {items_sample}")

                    # Extract fused values from new structure
                    fused_data = fused_result.get("fused", {})

                    fused_row = {
                        "date": current_date,
                        "T2M_MAX": fused_data.get("T2M_MAX", np.nan),
                        "T2M_MIN": fused_data.get("T2M_MIN", np.nan),
                        "T2M": fused_data.get(
                            "T2M",
                            np.nanmean(
                                [
                                    fused_data.get("T2M_MAX", np.nan),
                                    fused_data.get("T2M_MIN", np.nan),
                                ]
                            ),
                        ),
                        "RH2M": fused_data.get("RH2M", np.nan),
                        "WS2M": fused_data.get("WS2M", np.nan),
                        "ALLSKY_SFC_SW_DWN": fused_data.get(
                            "ALLSKY_SFC_SW_DWN", np.nan
                        ),
                        "PRECTOTCORR": fused_data.get("PRECTOTCORR", np.nan),
                    }
                    df_fused_list.append(fused_row)

                except Exception as e_kalman:
                    # Fallback to simple mean if Kalman fails
                    logger.warning(
                        f"⚠️  Kalman failed for {current_date}: {e_kalman}, "
                        f"using mean"
                    )
                    # Simple average across sources
                    fused_row = {"date": current_date}
                    for var in [
                        "T2M_MAX",
                        "T2M_MIN",
                        "T2M",
                        "RH2M",
                        "WS2M",
                        "ALLSKY_SFC_SW_DWN",
                        "PRECTOTCORR",
                    ]:
                        values = [
                            df[var].loc[current_date]
                            for df in preprocessed_sources
                            if current_date in df.index and var in df.columns
                        ]
                        fused_row[var] = (
                            np.nanmean(values) if values else np.nan
                        )
                    df_fused_list.append(fused_row)

            # Create fused DataFrame
            if df_fused_list:
                df_fused = pd.DataFrame(df_fused_list)
                df_fused["date"] = pd.to_datetime(df_fused["date"])
                df_fused.set_index("date", inplace=True)

                # Salvar DataFrame pós-fusão Kalman para depuração
                try:
                    df_fused.head(30).to_csv("temp/df_fused_kalman_head30.csv")
                except Exception as e:
                    logger.warning(
                        f"Falha ao salvar df_fused_kalman_head30.csv: {e}"
                    )

                logger.success(
                    f"   ✅ Kalman Ensemble fusion: {len(df_fused)} days"
                )
                logger.info("\n" + "=" * 70)
                logger.info("Kalman Fused DataFrame (first 5 rows):")
                logger.info(f"\n{df_fused.head().to_string()}")
                logger.info(f"\nColumns: {list(df_fused.columns)}")
                logger.info("=" * 70 + "\n")
                final_df = df_fused
            else:
                raise ValueError("No fused data generated")

        except Exception as e:
            logger.warning(
                f"   ⚠️  Kalman fusion failed: {str(e)}, "
                f"using first source only"
            )
            warnings_list.append(f"Kalman Ensemble fusion failed: {str(e)}")
            final_df = preprocessed_sources[0]
    else:
        # Single source or fusion disabled
        # Use first preprocessed source directly
        final_df = preprocessed_sources[0]
        logger.info(
            f"   ℹ️  Using preprocessed data directly "
            f"(single source available: {len(preprocessed_sources)})"
        )

    # ============================================================
    # 5. QUALITY CHECKS
    # ============================================================
    # Check for missing data
    missing_pct = final_df.isna().mean() * 100
    for var, pct in missing_pct.items():
        if pct > 25:
            warning = (
                f"Variable {var} has {pct:.1f}% missing data "
                f"for period {start_date} to {end_date}"
            )
            warnings_list.append(warning)
            logger.warning(f"   ⚠️  {warning}")

    # Check data completeness
    expected_days = (end_dt - start_dt).days + 1
    actual_days = len(final_df)
    if actual_days < expected_days:
        warning = f"Expected {expected_days} days, got {actual_days} days"
        warnings_list.append(warning)
        logger.warning(f"   ⚠️  {warning}")

    logger.success(
        f"   ✅ Final dataset: {len(final_df)} days, "
        f"{len(weather_sources)} source(s), "
        f"Fusion: {'YES' if use_fusion and len(weather_sources) > 1 else 'NO'}"
    )

    return final_df, warnings_list


def download_historical_weather_data_sync(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Synchronous wrapper for download_historical_weather_data.

    This is a convenience function that can be called from sync code.
    For async code, use download_historical_weather_data directly.
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context, create new loop in thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    download_historical_weather_data(
                        latitude, longitude, start_date, end_date
                    ),
                )
                return future.result()
        else:
            return loop.run_until_complete(
                download_historical_weather_data(
                    latitude, longitude, start_date, end_date
                )
            )
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(
            download_historical_weather_data(
                latitude, longitude, start_date, end_date
            )
        )
