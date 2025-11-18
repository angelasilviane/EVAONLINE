"""
User Request Simulator for End-to-End Validation.

Simulates the complete flow when a user clicks on the map interface:
1. User clicks coordinates (lat, lon) -> get from info_cities.csv
2. Backend fetches altitude from OpenTopo API
3. Backend downloads weather data (NASA POWER + OpenMeteo)
4. Backend applies preprocessing (outliers, validation)
5. Backend applies Kalman Ensemble fusion
6. Backend calculates ETo (FAO-56 Penman-Monteith)
7. Compare calculated ETo with reference data

This validates the ENTIRE production pipeline without infrastructure.
"""

import asyncio
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

# Import validation modules
from historical_data_loader import HistoricalDataLoader
from data_download_historical import download_historical_weather_data
from validation_logic_eto.api.services.opentopo.opentopo_sync_adapter import (
    OpenTopoSyncAdapter,
)
from validation_logic_eto.core.eto_calculation.eto_services import (
    calculate_eto_timeseries,
)


class UserRequestSimulator:
    """
    Simulates user requests to validate the complete backend pipeline.

    Each "request" represents a user clicking on the map and requesting
    climate data and ETo calculation for specific coordinates.
    """

    def __init__(self):
        """Initialize simulator with data loader."""
        self.data_loader = HistoricalDataLoader()
        self.opentopo_adapter = OpenTopoSyncAdapter()

        logger.info("🎯 User Request Simulator initialized")

    async def simulate_user_click(
        self,
        city_name: str,
        start_date: str,
        end_date: str,
        validate_altitude: bool = True,
        validate_eto: bool = True,
    ) -> Dict:
        """
        Simulate a complete user request flow.

        Args:
            city_name: City from info_cities.csv
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            validate_altitude: If True, compare OpenTopo vs info_cities.csv
            validate_eto: If True, compare calculated vs reference ETo

        Returns:
            Dict with results and validation metrics
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🎯 SIMULATING USER REQUEST: {city_name}")
        logger.info(f"   Period: {start_date} to {end_date}")
        logger.info(f"{'='*70}\n")

        results = {
            "city_name": city_name,
            "start_date": start_date,
            "end_date": end_date,
            "success": False,
            "errors": [],
            "warnings": [],
        }

        # ========================================================
        # STEP 1: Get coordinates from info_cities.csv
        # (simulates user clicking on map)
        # ========================================================
        logger.info("📍 STEP 1: Getting coordinates from user click...")
        city_info = self.data_loader.get_city_info(city_name)

        if city_info is None:
            error = f"City {city_name} not found in info_cities.csv"
            logger.error(f"   ❌ {error}")
            results["errors"].append(error)
            return results

        latitude = city_info["lat"]
        longitude = city_info["lon"]
        altitude_reference = city_info["alt"]
        region = city_info["region"]

        logger.success(
            f"   ✅ User clicked: ({latitude:.4f}, {longitude:.4f})"
        )
        results["latitude"] = latitude
        results["longitude"] = longitude
        results["altitude_reference"] = altitude_reference
        results["region"] = region

        # ========================================================
        # STEP 2: Fetch altitude from OpenTopo API
        # (simulates backend API call)
        # ========================================================
        logger.info("🏔️  STEP 2: Fetching altitude from OpenTopo API...")

        try:
            altitude_api = self.opentopo_adapter.get_elevation_sync(
                lat=latitude, lon=longitude
            )

            if altitude_api is None:
                raise ValueError("OpenTopo returned None")

            # Garantir que altitude_api_value seja sempre float
            if hasattr(altitude_api, "elevation"):
                altitude_api_value: float = float(altitude_api.elevation)
            elif isinstance(altitude_api, (int, float)):
                altitude_api_value: float = float(altitude_api)
            else:
                raise TypeError(
                    f"Unexpected altitude type: {type(altitude_api)}"
                )

            logger.success(
                f"✅✅✅✅✅ OpenTopo altitude: {altitude_api_value}m"
            )
            results["altitude_api"] = altitude_api_value

            # Validate altitude if requested
            if validate_altitude:
                altitude_diff = abs(altitude_api_value - altitude_reference)
                altitude_pct_diff = (
                    (altitude_diff / altitude_reference) * 100
                    if altitude_reference > 0
                    else 0
                )

                logger.info(
                    f"📊 Altitude validation: "
                    f"API={altitude_api_value}m vs "
                    f"Reference={altitude_reference}m "
                    f"(diff={altitude_diff:.1f}m, "
                    f"{altitude_pct_diff:.1f}%)"
                )

                results["altitude_validation"] = {
                    "api": altitude_api_value,
                    "reference": altitude_reference,
                    "difference_m": altitude_diff,
                    "difference_pct": altitude_pct_diff,
                }

                if altitude_pct_diff > 10:
                    warning = (
                        f"Altitude difference > 10%: {altitude_pct_diff:.1f}%"
                    )
                    logger.warning(f"⚠️{warning}")
                    results["warnings"].append(warning)

        except Exception as e:
            error = f"OpenTopo API error: {str(e)}"
            logger.error(f"   ❌ {error}")
            results["errors"].append(error)
            altitude_api_value = altitude_reference  # Fallback

        # ========================================================
        # STEP 3-5: Download weather data with preprocessing + Kalman
        # (simulates complete backend pipeline)
        # ========================================================
        logger.info(
            "🌦️  STEPS 3-5: Downloading weather + preprocessing + "
            "Kalman fusion..."
        )

        try:
            df_weather, download_warnings = (
                await download_historical_weather_data(
                    latitude=latitude,
                    longitude=longitude,
                    start_date=start_date,
                    end_date=end_date,
                    use_fusion=True,  # Enable Kalman Ensemble
                )
            )

            logger.success(
                f"✅ Downloaded {len(df_weather)} days of weather data"
            )
            results["weather_days"] = len(df_weather)
            results["warnings"].extend(download_warnings)

        except Exception as e:
            error = f"Weather download error: {str(e)}"
            logger.error(f"❌ {error}")
            results["errors"].append(error)
            return results

        # ========================================================
        # STEP 6: Calculate ETo (FAO-56)
        # (simulates ETo calculation service)
        # ========================================================
        logger.info("🌱 STEP 6: Calculating ETo (FAO-56)...")

        try:
            df_eto = calculate_eto_timeseries(
                df=df_weather,
                latitude=latitude,
                longitude=longitude,
                elevation_m=altitude_api_value,
            )

            logger.success(f"✅ Calculated ETo for {len(df_eto)} days")
            results["eto_days"] = len(df_eto)
            results["eto_calculated"] = df_eto

            logger.info("\n" + "=" * 70)
            logger.info("Final ETo DataFrame (first 10 rows):")
            # Show our calculated ETo and OpenMeteo's ETo if available
            if "et0_fao_evapotranspiration" in df_eto.columns:
                logger.info(
                    f"\n{df_eto[['et0_mm', 'et0_fao_evapotranspiration']].head(10).to_string()}"
                )
            else:
                logger.info(f"\n{df_eto[['et0_mm']].head(10).to_string()}")
            logger.info(f"\nETo Statistics:")
            logger.info(f"  Mean: {df_eto['et0_mm'].mean():.2f} mm/day")
            logger.info(f"  Std:  {df_eto['et0_mm'].std():.2f} mm/day")
            logger.info(f"  Min:  {df_eto['et0_mm'].min():.2f} mm/day")
            logger.info(f"  Max:  {df_eto['et0_mm'].max():.2f} mm/day")
            logger.info("=" * 70 + "\n")

            # Basic ETo statistics (coluna 'et0_mm')
            eto_stats = {
                "mean": df_eto["et0_mm"].mean(),
                "std": df_eto["et0_mm"].std(),
                "min": df_eto["et0_mm"].min(),
                "max": df_eto["et0_mm"].max(),
            }
            logger.info(
                f"   📊 ETo stats: mean={eto_stats['mean']:.2f} mm/day, "
                f"std={eto_stats['std']:.2f}, "
                f"range=[{eto_stats['min']:.2f}, {eto_stats['max']:.2f}]"
            )
            results["eto_stats"] = eto_stats

        except Exception as e:
            error = f"ETo calculation error: {str(e)}"
            logger.error(f"   ❌ {error}")
            results["errors"].append(error)
            return results

        # ========================================================
        # STEP 7: Validate against reference ETo
        # (simulates accuracy assessment)
        # ========================================================
        if validate_eto:
            logger.info("📊 STEP 7: Validating ETo against reference data...")

            try:
                comparison = self.data_loader.compare_eto_results(
                    calculated_eto=df_eto,
                    city_name=city_name,
                    region=region,
                )

                if comparison:
                    results["eto_validation"] = comparison
                    logger.success(
                        f"   ✅ Validation complete: "
                        f"MAE={comparison['mae']:.3f} mm/day, "
                        f"R²={comparison['r2']:.3f}"
                    )
                else:
                    warning = "No reference ETo data for comparison"
                    logger.warning(f"   ⚠️  {warning}")
                    results["warnings"].append(warning)

            except Exception as e:
                error = f"ETo validation error: {str(e)}"
                logger.error(f"   ❌ {error}")
                results["errors"].append(error)

        # ========================================================
        # FINAL SUMMARY
        # ========================================================
        results["success"] = len(results["errors"]) == 0

        logger.info(f"\n{'='*70}")
        if results["success"]:
            logger.success(f"✅ REQUEST COMPLETED SUCCESSFULLY: {city_name}")
        else:
            logger.error(
                f"❌ REQUEST FAILED: {city_name} "
                f"({len(results['errors'])} errors)"
            )
        logger.info(f"{'='*70}\n")

        return results

    async def simulate_multiple_requests(
        self,
        cities: Optional[List[str]] = None,
        start_date: str = "1991-01-01",
        end_date: str = "1991-12-31",
        max_cities: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Simulate multiple user requests for batch validation.

        Args:
            cities: List of city names. If None, uses all from info_cities.csv
            start_date: Start date
            end_date: End date
            max_cities: Maximum number of cities to test

        Returns:
            DataFrame with validation results for all cities
        """
        # Get city list
        if cities is None:
            df_cities = self.data_loader.get_all_cities_info()
            if df_cities is None:
                logger.error("No cities found in info_cities.csv")
                return pd.DataFrame()
            cities = df_cities["city"].tolist()

        if max_cities:
            cities = cities[:max_cities]

        logger.info(
            f"🚀 Starting batch validation: {len(cities)} cities, "
            f"period {start_date} to {end_date}"
        )

        all_results = []

        for idx, city in enumerate(cities, 1):
            logger.info(f"\n[{idx}/{len(cities)}] Processing {city}...")

            result = await self.simulate_user_click(
                city_name=city,
                start_date=start_date,
                end_date=end_date,
            )

            # Extract key metrics for summary
            summary = {
                "city": city,
                "success": result["success"],
                "weather_days": result.get("weather_days", 0),
                "eto_days": result.get("eto_days", 0),
                "errors_count": len(result.get("errors", [])),
                "warnings_count": len(result.get("warnings", [])),
            }

            # Add altitude validation
            if "altitude_validation" in result:
                alt_val = result["altitude_validation"]
                summary["altitude_diff_m"] = alt_val["difference_m"]
                summary["altitude_diff_pct"] = alt_val["difference_pct"]

            # Add ETo validation
            if "eto_validation" in result:
                eto_val = result["eto_validation"]
                summary["eto_mae"] = eto_val["mae"]
                summary["eto_rmse"] = eto_val["rmse"]
                summary["eto_r2"] = eto_val["r2"]
                summary["eto_bias"] = eto_val["bias"]

            all_results.append(summary)

        df_results = pd.DataFrame(all_results)

        logger.info(f"\n{'='*70}")
        logger.success(
            f"✅ BATCH VALIDATION COMPLETE: {len(cities)} cities processed"
        )

        # Summary statistics
        success_count = df_results["success"].sum()
        logger.info(f"   Success rate: {success_count}/{len(cities)}")

        if "eto_mae" in df_results.columns:
            logger.info(
                f"   Average MAE: "
                f"{df_results['eto_mae'].mean():.3f} mm/day"
            )
            logger.info(f"   Average R²: {df_results['eto_r2'].mean():.3f}")

        logger.info(f"{'='*70}\n")

        return df_results


# Example usage
async def main():
    """Example: Simulate validation for Brasil cities (1 year)."""
    simulator = UserRequestSimulator()

    # Test single city first
    result = await simulator.simulate_user_click(
        city_name="Alvorada_do_Gurgueia_PI",
        start_date="1991-01-01",
        end_date="1991-12-31",
    )

    print("\n" + "=" * 70)
    print("SINGLE CITY TEST RESULT:")
    print("=" * 70)
    print(f"Success: {result['success']}")
    if "eto_validation" in result:
        print(f"MAE: {result['eto_validation']['mae']:.3f} mm/day")
        print(f"R²: {result['eto_validation']['r2']:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
