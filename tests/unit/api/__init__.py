"""
Unit tests for Climate API Services.

This package contains comprehensive tests for all climate data sources,
validating data download, sync adapters, and geographic coverage.

Test Organization:
- test_nasa_power.py: NASA POWER API tests
- test_openmeteo_archive.py: Open-Meteo Archive API tests
- test_openmeteo_forecast.py: Open-Meteo Forecast API tests
- test_met_norway.py: MET Norway APIs tests (Locationforecast + FROST)
- test_nws.py: NWS/NOAA APIs tests (Forecast + Stations)
- test_data_download.py: Integration tests for data_download.py
- test_multi_location.py: Cross-location validation tests

Test Locations:
- Global: São Paulo (Brazil), Berlin (Germany), Tokyo (Japan)
- Europe: Oslo (Norway), Paris (France)
- USA: New York (USA), Los Angeles (USA)
- Remote: Antarctica, Pacific Ocean

Each test validates:
1. Data download success
2. Data format and structure
3. Geographic coverage
4. Date range validation
5. Variable completeness
6. Error handling

Author: EVAonline Development Team
Date: November 2025
"""

__version__ = "1.0.0"
__author__ = "EVAonline Development Team"
