"""
Historical Data Loader for Validation.

Loads climate normals from JSON files in data/historical/cities/
to replace database queries in Kalman Ensemble fusion.

Also loads reference ETo data from CSV files for validation comparison.

Example usage:

    # Initialize loader
    loader = HistoricalDataLoader()

    # Get historical normals for Kalman Ensemble
    has_history, normals, stds = loader.get_historical_stats_for_kalman(
        latitude=-8.44, longitude=-43.86, max_distance_km=50
    )

    # Load reference ETo for comparison
    city_name, df_reference = loader.get_reference_eto_for_coords(
        latitude=-8.44, longitude=-43.86, max_distance_km=50
    )

    # Compare calculated ETo against reference
    metrics = loader.compare_eto_results(
        calculated_eto=df_calculated,  # Your calculated results
        city_name=city_name,
        region="brasil"
    )
    print(f"MAE: {metrics['mae']:.3f} mm/day")
    print(f"R²: {metrics['r2']:.3f}")
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
from loguru import logger


class HistoricalDataLoader:
    """
    Loads historical climate data from JSON files.

    Replaces PostgreSQL queries in production Kalman Ensemble
    with direct file access for validation purposes.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize loader.

        Args:
            data_dir: Path to data_validation/data directory.
                     If None, uses default relative path.
        """
        if data_dir is None:
            # Default: validation/data_validation/data
            self.data_root = Path(__file__).parent / "data_validation" / "data"
        else:
            self.data_root = Path(data_dir)

        # Paths for historical climate normals (JSON)
        self.historical_dir = self.data_root / "historical"
        self.cities_dir = self.historical_dir / "cities"
        self.summary_file = (
            self.historical_dir / "summary" / "cities_summary.csv"
        )

        # Paths for reference ETo data (CSV) - NEW LOCATION
        self.csv_dir = self.data_root / "csv"
        self.brasil_eto_dir = self.csv_dir / "BRASIL" / "ETo"
        self.mundo_eto_dir = self.csv_dir / "MUNDO" / "ETo"
        self.brasil_pr_dir = self.csv_dir / "BRASIL" / "pr"
        self.mundo_pr_dir = self.csv_dir / "MUNDO" / "pr"

        # Path for city info (coordinates + altitude)
        self.info_cities_file = self.data_root / "info_cities.csv"

        # Load cities info for simulation
        self._cities_info = None
        if self.info_cities_file.exists():
            try:
                self._cities_info = pd.read_csv(self.info_cities_file)
                logger.info(
                    f"✅ Loaded {len(self._cities_info)} cities "
                    f"from info_cities.csv"
                )
            except Exception as e:
                logger.warning(f"Could not load info_cities.csv: {e}")

        # Load cities summary for quick lookup
        self._cities_summary = None
        if self.summary_file.exists():
            try:
                self._cities_summary = pd.read_csv(self.summary_file)
                logger.info(
                    f"✅ Loaded {len(self._cities_summary)} cities "
                    f"from summary"
                )
            except Exception as e:
                logger.warning(f"Could not load cities summary: {e}")

    def get_all_cities_info(self) -> Optional[pd.DataFrame]:
        """
        Get all cities from info_cities.csv for simulation.

        Returns:
            DataFrame with columns: city, region, lat, lon, alt
        """
        return self._cities_info

    def get_city_info(self, city_name: str) -> Optional[Dict]:
        """
        Get info for a specific city from info_cities.csv.

        Args:
            city_name: City name (e.g., "Alvorada_do_Gurgueia_PI")

        Returns:
            Dict with keys: city, region, lat, lon, alt
        """
        if self._cities_info is None:
            return None

        city_row = self._cities_info[self._cities_info["city"] == city_name]

        if city_row.empty:
            return None

        return city_row.iloc[0].to_dict()

    def find_city_by_coords(
        self, latitude: float, longitude: float, max_distance_km: float = 50
    ) -> Optional[str]:
        """
        Find closest city to given coordinates.

        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            max_distance_km: Maximum distance in km to consider a match

        Returns:
            City name if found within distance, None otherwise
        """
        if self._cities_summary is None:
            return None

        # Haversine distance approximation
        df = self._cities_summary.copy()
        df["dist_lat"] = (df["lat"] - latitude).abs()
        df["dist_lon"] = (df["lon"] - longitude).abs()

        # Quick filter (1 degree ≈ 111km)
        df = df[
            (df["dist_lat"] < max_distance_km / 111)
            & (df["dist_lon"] < max_distance_km / 111)
        ]

        if df.empty:
            return None

        # Haversine formula for accurate distance
        import numpy as np

        df["lat_rad"] = np.radians(df["lat"])
        df["lon_rad"] = np.radians(df["lon"])
        lat_rad = np.radians(latitude)
        lon_rad = np.radians(longitude)

        df["dlat"] = df["lat_rad"] - lat_rad
        df["dlon"] = df["lon_rad"] - lon_rad

        df["a"] = (
            np.sin(df["dlat"] / 2) ** 2
            + np.cos(lat_rad)
            * np.cos(df["lat_rad"])
            * np.sin(df["dlon"] / 2) ** 2
        )
        df["c"] = 2 * np.arcsin(np.sqrt(df["a"]))
        df["distance_km"] = 6371 * df["c"]  # Earth radius in km

        # Find closest
        closest = df.loc[df["distance_km"].idxmin()]

        if closest["distance_km"].iloc[0] <= max_distance_km:
            logger.debug(
                f"Found city {closest['city'].iloc[0]} at "
                f"{closest['distance_km'].iloc[0]:.1f}km from "
                f"({latitude:.4f}, {longitude:.4f})"
            )
            return closest["city"].iloc[0]

        return None

    def load_city_data(self, city_name: str) -> Optional[Dict]:
        """
        Load full historical data for a city.

        Args:
            city_name: City name (e.g., "Alvorada_do_Gurgueia_PI")

        Returns:
            Dict with climate normals or None if not found
        """
        report_file = self.cities_dir / f"report_{city_name}.json"

        if not report_file.exists():
            logger.warning(f"No historical data found for {city_name}")
            return None

        try:
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.debug(
                f"Loaded historical data for {city_name}: "
                f"{data.get('total_records', 0)} records, "
                f"period {data.get('data_period', 'unknown')}"
            )
            return data

        except Exception as e:
            logger.error(f"Error loading {city_name}: {e}")
            return None

    def get_monthly_normals(
        self,
        city_name: str,
        variable: str = "ETo",
        period: str = "1991-2020",
    ) -> Optional[Dict[int, Dict]]:
        """
        Get monthly climate normals for a variable.

        Args:
            city_name: City name
            variable: "ETo" or other climate variable
            period: Reference period (e.g., "1991-2020", "1961-1990")

        Returns:
            Dict mapping month (1-12) to statistics dict with keys:
            - normal: monthly mean
            - daily_std: daily standard deviation
            - daily_median: daily median
            - p05, p95: percentiles
        """
        data = self.load_city_data(city_name)
        if data is None:
            return None

        # Navigate to monthly normals
        try:
            normals = (
                data.get("climate_normals_all_periods", {})
                .get(period, {})
                .get("monthly", {})
            )

            if not normals:
                logger.warning(
                    f"No monthly normals for {city_name} "
                    f"in period {period}"
                )
                return None

            # Convert month keys from string to int
            monthly_dict = {}
            for month_str, stats in normals.items():
                month = int(month_str)
                monthly_dict[month] = stats

            return monthly_dict

        except Exception as e:
            logger.error(
                f"Error extracting monthly normals for {city_name}: {e}"
            )
            return None

    def get_historical_stats_for_kalman(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 50,
        period: str = "1991-2020",
    ) -> Tuple[bool, Optional[Dict[int, float]], Optional[Dict[int, float]]]:
        """
        Get historical data formatted for Kalman Ensemble.

        This replaces the database query in production KalmanEnsembleStrategy.

        Args:
            latitude: Latitude
            longitude: Longitude
            max_distance_km: Maximum search distance
            period: Reference period

        Returns:
            Tuple of (has_history, monthly_normals, monthly_stds)
            - has_history: True if historical data found
            - monthly_normals: Dict[month -> mean ETo]
            - monthly_stds: Dict[month -> std ETo]
        """
        # Find closest city
        city_name = self.find_city_by_coords(
            latitude, longitude, max_distance_km
        )

        if city_name is None:
            logger.debug(
                f"No historical city found within {max_distance_km}km "
                f"of ({latitude:.4f}, {longitude:.4f})"
            )
            return False, None, None

        # Get monthly normals
        monthly_data = self.get_monthly_normals(city_name, "ETo", period)

        if monthly_data is None:
            return False, None, None

        # Extract normals and stds
        monthly_normals = {}
        monthly_stds = {}

        for month, stats in monthly_data.items():
            monthly_normals[month] = stats.get("normal")
            monthly_stds[month] = stats.get("daily_std", None)

        # Check if we have complete data
        if len(monthly_normals) != 12 or None in monthly_normals.values():
            logger.warning(f"Incomplete monthly normals for {city_name}")
            return False, None, None

        logger.info(
            f"✅ Using historical data from {city_name} "
            f"for Kalman Ensemble (period {period})"
        )

        return True, monthly_normals, monthly_stds

    def load_reference_eto(
        self, city_name: str, region: str = "brasil"
    ) -> Optional[pd.DataFrame]:
        """
        Load reference ETo data from CSV files.

        These are the ground truth ETo values calculated from station
        data for validation purposes (Xavier et al. 2016, 2022 for Brasil;
        FAO-56 reference for MUNDO).

        Args:
            city_name: City name (e.g., "Alvorada_do_Gurgueia_PI")
            region: "brasil" or "mundo"

        Returns:
            DataFrame with columns ['date', 'ETo'] or None if not found
        """
        # Select directory based on region
        if region.lower() == "brasil":
            eto_dir = self.brasil_eto_dir
        elif region.lower() == "mundo":
            eto_dir = self.mundo_eto_dir
        else:
            logger.error(f"Unknown region: {region}")
            return None

        # Construct file path
        eto_file = eto_dir / f"{city_name}.csv"

        if not eto_file.exists():
            logger.warning(f"No reference ETo found for {city_name}")
            return None

        try:
            # Load CSV
            df = pd.read_csv(eto_file)

            # Ensure proper column names (Data -> date if needed)
            if "Data" in df.columns:
                df.rename(columns={"Data": "date"}, inplace=True)

            # Parse date column
            df["date"] = pd.to_datetime(df["date"])

            # Set date as index
            df.set_index("date", inplace=True)

            logger.debug(
                f"Loaded reference ETo for {city_name}: "
                f"{len(df)} records from "
                f"{df.index.min()} to {df.index.max()}"
            )

            return df

        except Exception as e:
            logger.error(f"Error loading reference ETo for {city_name}: {e}")
            return None

    def get_reference_eto_for_coords(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 50,
    ) -> Optional[Tuple[str, pd.DataFrame]]:
        """
        Get reference ETo data for the closest city to given coordinates.

        Args:
            latitude: Latitude
            longitude: Longitude
            max_distance_km: Maximum search distance

        Returns:
            Tuple of (city_name, eto_dataframe) or None if not found
        """
        # Find closest city
        city_name = self.find_city_by_coords(
            latitude, longitude, max_distance_km
        )

        if city_name is None:
            return None

        # Determine region (brasil or mundo)
        if self._cities_summary is not None:
            city_row = self._cities_summary[
                self._cities_summary["city"] == city_name
            ]
            if not city_row.empty:
                region = city_row.iloc[0]["region"]
            else:
                region = "brasil"  # Default
        else:
            region = "brasil"  # Default

        # Load reference ETo
        df_eto = self.load_reference_eto(city_name, region)

        if df_eto is None:
            return None

        return city_name, df_eto

    def compare_eto_results(
        self,
        calculated_eto: pd.DataFrame,
        city_name: str,
        region: str = "brasil",
    ) -> Optional[Dict]:
        """
        Compare calculated ETo against reference values.

        Args:
            calculated_eto: DataFrame with calculated ETo (must have 'ETo' col)
            city_name: City name for reference data
            region: "brasil" or "mundo"

        Returns:
            Dict with comparison metrics:
            - mae: Mean Absolute Error
            - rmse: Root Mean Square Error
            - r2: R-squared coefficient
            - bias: Mean bias (calculated - reference)
            - n_compared: Number of days compared
        """
        import numpy as np
        from sklearn.metrics import mean_absolute_error, r2_score

        # Load reference ETo
        df_reference = self.load_reference_eto(city_name, region)

        if df_reference is None:
            logger.error(f"Cannot compare: no reference data for {city_name}")
            return None

        # Ensure calculated_eto has date index
        if not isinstance(calculated_eto.index, pd.DatetimeIndex):
            if "date" in calculated_eto.columns:
                calculated_eto = calculated_eto.set_index("date")
            else:
                logger.error("calculated_eto must have date index or column")
                return None

        # Align dataframes (inner join on dates)
        # Support both 'ETo' and 'et0_mm' column names
        eto_col = "ETo" if "ETo" in calculated_eto.columns else "et0_mm"

        df_merged = pd.merge(
            calculated_eto[[eto_col]],
            df_reference[["ETo"]],
            left_index=True,
            right_index=True,
            how="inner",
            suffixes=("_calc", "_ref"),
        )

        # Rename columns for consistency
        if eto_col == "et0_mm":
            df_merged = df_merged.rename(columns={"et0_mm": "ETo_calc"})
        else:
            df_merged = df_merged.rename(columns={"ETo": "ETo_calc"})
        df_merged = df_merged.rename(columns={"ETo": "ETo_ref"})

        # Remove NaN values
        df_merged = df_merged.dropna()

        if len(df_merged) == 0:
            logger.warning("No overlapping dates for comparison")
            return None

        # Extract arrays
        eto_calc = df_merged["ETo_calc"].to_numpy()
        eto_ref = df_merged["ETo_ref"].to_numpy()

        # DEBUG: Print sample comparison
        logger.debug(f"Sample comparison (first 5 days):")
        logger.debug(
            f"\n{df_merged[['ETo_calc', 'ETo_ref']].head(10).to_string()}"
        )

        # Calculate metrics
        mae = mean_absolute_error(eto_ref, eto_calc)
        rmse = np.sqrt(np.mean((eto_calc - eto_ref) ** 2))
        r2 = r2_score(eto_ref, eto_calc)
        bias = np.mean(eto_calc - eto_ref)

        metrics = {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "bias": bias,
            "n_compared": len(df_merged),
            "period_start": df_merged.index.min().strftime("%Y-%m-%d"),
            "period_end": df_merged.index.max().strftime("%Y-%m-%d"),
        }

        logger.info(
            f"📊 Comparison for {city_name}: "
            f"MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}, "
            f"Bias={bias:.3f}, N={len(df_merged)}"
        )

        return metrics
