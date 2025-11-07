#!/usr/bin/env python3
"""
Test script for improved IQR outlier detection - Short term data test
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


def test_short_term_iqr():
    """Test IQR detection with short-term data (30 days)."""
    print("Testing IQR with short-term data (30 days)")
    print("=" * 50)

    # Create 30 days of test data
    dates_30 = pd.date_range("2023-01-01", periods=30, freq="D")

    n_days = len(dates_30)
    np.random.seed(42)

    # Create test data with outliers
    temp_data = np.array(
        [
            25 + 5 * np.sin(2 * np.pi * i / 30) + np.random.normal(0, 2)
            for i in range(n_days)
        ]
    )
    temp_data[10:13] = 60  # Add outliers

    # Add outliers to custom_variable that will be processed
    custom_var = np.random.normal(100, 10, n_days)
    custom_var = np.array(custom_var)  # Make mutable
    custom_var[5:8] = 200  # Add clear outliers

    df_30 = pd.DataFrame(
        {
            "T2M_MAX": temp_data,  # Excluded (physical validation)
            "RH2M": np.clip(
                np.random.normal(70, 15, n_days), 0, 100
            ),  # Excluded
            "WS2M": np.clip(
                np.random.normal(3, 1.5, n_days), 0, 50
            ),  # Excluded
            "PRECTOTCORR": np.random.exponential(2, n_days),  # Excluded
            "ALLSKY_SFC_SW_DWN": np.random.normal(250, 50, n_days),  # Excluded
            "custom_variable": custom_var,  # Should be processed
            "Ra": np.random.normal(300, 20, n_days),  # Excluded
            "dr": np.random.normal(1, 0.1, n_days),  # Excluded
            "delta": np.random.normal(0.2, 0.05, n_days),  # Excluded
            "omega_s": np.random.normal(1.5, 0.2, n_days),  # Excluded
        },
        index=dates_30,
    )

    print(f"Created 30-day dataset with {len(df_30)} rows")

    # Test with seasonal_detection=True but short data
    result_30, warnings_30 = detect_outliers_iqr(
        df_30, iqr_factor=1.5, max_outlier_percent=10.0
    )

    # Check if it used global IQR (should mention "global IQR" in warnings)
    global_iqr_used = any("global IQR" in w for w in warnings_30)
    seasonal_iqr_used = any("seasonal IQR" in w for w in warnings_30)

    print(f"Global IQR used: {global_iqr_used}")
    print(f"Seasonal IQR used: {seasonal_iqr_used}")
    print(f"Total warnings: {len(warnings_30)}")

    for warning in warnings_30:
        print(f"  - {warning}")

    if global_iqr_used and not seasonal_iqr_used:
        print("✅ SUCCESS: Correctly used global IQR for short-term data")
        print("   With 30 days of data, only global IQR is supported.")
    else:
        print("❌ FAILURE: Unexpected detection method used")

    print("\nConclusion: The IQR method is optimized for 7-30 day periods.")
    print("- Always uses global IQR (no seasonal analysis)")
    print("- Validates data is within supported range (7-30 days)")
    print("- Excludes physically validated variables from IQR processing")


if __name__ == "__main__":
    test_short_term_iqr()
