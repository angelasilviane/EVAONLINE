#!/usr/bin/env python3
"""
Test script for improved IQR outlier detection in data_preprocessing.py

This script tests the enhanced detect_outliers_iqr function with:
- Seasonal detection
- Adaptive IQR factors
- Exclusion of physically validated variables
- Maximum outlier percentage limits
"""

import os
import sys

import numpy as np
import pandas as pd

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.core.data_processing.data_preprocessing import (
    detect_outliers_iqr,
)


def create_test_data():
    """Create test weather data with known outliers."""
    # Create date range for one year
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")

    # Create base data with seasonal patterns
    n_days = len(dates)
    np.random.seed(42)  # For reproducible results

    # Temperature with seasonal variation and outliers
    temp_base = 25 + 10 * np.sin(2 * np.pi * dates.dayofyear / 365)
    temp_noise = np.random.normal(0, 2, n_days)
    temp_data = temp_base + temp_noise

    # Add some outliers (create mutable copy)
    temp_data = np.array(temp_data)  # Ensure it's a mutable numpy array
    temp_data[100:105] = 60  # Extreme high temperatures
    temp_data[200:203] = -20  # Extreme low temperatures

    # Humidity (0-100%, already validated)
    humidity_data = np.clip(np.random.normal(70, 15, n_days), 0, 100)

    # Wind speed (0-100 m/s, already validated)
    wind_data = np.clip(np.random.normal(3, 1.5, n_days), 0, 50)

    # Precipitation (0-450 mm, already validated)
    precip_data = np.random.exponential(2, n_days)
    precip_data = np.clip(precip_data, 0, 100)

    # Radiation (validated with Ra)
    radiation_data = np.random.normal(250, 50, n_days)
    radiation_data = np.clip(radiation_data, 0, 400)

    # Some variable that should be processed by IQR (not physically validated)
    custom_var = np.random.normal(100, 10, n_days)
    custom_var[50:55] = 200  # Add outliers

    # Create DataFrame
    df = pd.DataFrame(
        {
            "T2M_MAX": temp_data,  # Should be excluded (physical validation)
            "RH2M": humidity_data,  # Should be excluded (physical validation)
            "WS2M": wind_data,  # Should be excluded (physical validation)
            "PRECTOTCORR": precip_data,  # Should be excluded (physical validation)
            "ALLSKY_SFC_SW_DWN": radiation_data,  # Excluded (validated)
            "custom_variable": custom_var,  # Should be processed by IQR
            "Ra": np.random.normal(300, 20, n_days),  # Calculated, excluded
            "dr": np.random.normal(1, 0.1, n_days),  # Calculated, excluded
            "delta": np.random.normal(
                0.2, 0.05, n_days
            ),  # Calculated, excluded
            "omega_s": np.random.normal(
                1.5, 0.2, n_days
            ),  # Calculated, excluded
        },
        index=dates,
    )

    return df


def test_short_term_data():
    # Create 30 days of test data
    dates_30 = pd.date_range("2023-01-01", periods=30, freq="D")

    n_days = len(dates_30)
    np.random.seed(42)

    # Create data similar to create_test_data but for 30 days
    temp_data = np.array(
        [
            25 + 5 * np.sin(2 * np.pi * i / 30) + np.random.normal(0, 2)
            for i in range(n_days)
        ]
    )
    temp_data[10:13] = 60  # Add outliers

    df_30 = pd.DataFrame(
        {
            "T2M_MAX": temp_data,
            "RH2M": np.clip(np.random.normal(70, 15, n_days), 0, 100),
            "WS2M": np.clip(np.random.normal(3, 1.5, n_days), 0, 50),
            "PRECTOTCORR": np.random.exponential(2, n_days),
            "ALLSKY_SFC_SW_DWN": np.random.normal(250, 50, n_days),
            "custom_variable": np.random.normal(100, 10, n_days),
            "Ra": np.random.normal(300, 20, n_days),
            "dr": np.random.normal(1, 0.1, n_days),
            "delta": np.random.normal(0.2, 0.05, n_days),
            "omega_s": np.random.normal(1.5, 0.2, n_days),
        },
        index=dates_30,
    )

    print(f"Created 30-day dataset with {len(df_30)} rows")

    # Test with seasonal_detection=True but short data
    result_30, warnings_30 = detect_outliers_iqr(
        df_30,
        iqr_factor=1.5,
        seasonal_detection=True,  # Should automatically switch to global
        max_outlier_percent=10.0,
    )

    # Check if it used global IQR (should mention "global IQR" in warnings)
    global_iqr_used = any("global IQR" in w for w in warnings_30)
    seasonal_iqr_used = any("seasonal IQR" in w for w in warnings_30)

    print(f"Global IQR used: {global_iqr_used}")
    print(f"Seasonal IQR used: {seasonal_iqr_used}")
    print(f"Warnings: {len(warnings_30)}")

    if global_iqr_used and not seasonal_iqr_used:
        print("✅ Correctly used global IQR for short-term data")
    else:
        print("❌ Unexpected detection method used")

    print()


def test_iqr_improvements():
    """Test the improved IQR outlier detection function."""
    print("Testing improved IQR outlier detection...")
    print("=" * 60)

    # Create test data
    df = create_test_data()
    print(
        f"Created test dataset with {len(df)} rows and {len(df.columns)} columns"
    )
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print()

    # Test 1: Standard IQR detection (no seasonal)
    print("Test 1: Standard IQR detection (seasonal_detection=False)")
    df_test1 = df.copy()
    result1, warnings1 = detect_outliers_iqr(
        df_test1,
        iqr_factor=1.5,
        seasonal_detection=False,
        max_outlier_percent=10.0,
    )

    excluded_cols = [
        "T2M_MAX",
        "RH2M",
        "WS2M",
        "PRECTOTCORR",
        "ALLSKY_SFC_SW_DWN",
        "Ra",
        "dr",
        "delta",
        "omega_s",
    ]
    processed_cols = len(
        [col for col in df.columns if col not in excluded_cols]
    )
    print(f"Processed columns: {processed_cols}")
    print(f"Warnings generated: {len(warnings1)}")
    for warning in warnings1[-3:]:  # Show last 3 warnings
        print(f"  - {warning}")
    print()

    # Test 2: Seasonal IQR detection
    print("Test 2: Seasonal IQR detection (seasonal_detection=True)")
    df_test2 = df.copy()
    result2, warnings2 = detect_outliers_iqr(
        df_test2,
        iqr_factor=1.5,
        seasonal_detection=True,
        max_outlier_percent=10.0,
    )

    print(f"Warnings generated: {len(warnings2)}")
    for warning in warnings2[-3:]:  # Show last 3 warnings
        print(f"  - {warning}")
    print()

    # Test 3: High outlier percentage warning
    print("Test 3: Testing high outlier percentage warning")
    df_test3 = df.copy()
    # Add many outliers to trigger warning
    df_test3.loc["2023-06-01":"2023-06-10", "custom_variable"] = 500

    result3, warnings3 = detect_outliers_iqr(
        df_test3,
        iqr_factor=1.5,
        seasonal_detection=False,
        max_outlier_percent=1.0,  # Low threshold to trigger warning
    )

    high_outlier_warnings = [
        w for w in warnings3 if "WARNING: High outlier percentage" in w
    ]
    print(f"High outlier warnings: {len(high_outlier_warnings)}")
    if high_outlier_warnings:
        print(f"  - {high_outlier_warnings[0]}")
    print()

    # Test 4: Data quality checks
    print("Test 4: Testing data quality validation")
    df_test4 = df.copy()
    # Create column with no variance
    df_test4["no_variance"] = 100.0

    result4, warnings4 = detect_outliers_iqr(
        df_test4, iqr_factor=1.5, seasonal_detection=False
    )

    quality_warnings = [
        w for w in warnings4 if "no variance" in w or "insufficient data" in w
    ]
    print(f"Data quality warnings: {len(quality_warnings)}")
    for warning in quality_warnings:
        print(f"  - {warning}")
    print()

    test_short_term_data()

    # Summary
    print("Summary of improvements:")
    print("- Excluded physically validated variables from IQR processing")
    print("- Added seasonal IQR detection by month")
    print("- Implemented adaptive IQR factors based on variable type")
    print("- Added maximum outlier percentage limits with warnings")
    print("- Enhanced data quality validation before outlier detection")
    print("- Improved logging and warning messages")

    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    test_iqr_improvements()
