# Regional Validation Limits

## Overview

The EVAONLINE system now supports **regional validation strategies** for weather data. Different regions may have different valid ranges for meteorological variables based on scientific literature and historical data.

## Implemented Regions

### 1. Brazil (Xavier et al. 2016, 2022)

Based on **"New improved Brazilian daily weather gridded data (1961–2020)"** by Xavier et al.

#### Temperature Limits
- **Tmax**: -30°C < T < 50°C
- **Tmin**: -30°C < T < 50°C
- **T (mean)**: -30°C < T < 50°C

#### Humidity Limits
- **RH**: 0% ≤ RH ≤ 100%

#### Wind Speed Limits
- **Wind (u2)**: 0 m/s ≤ u2 < 100 m/s

#### Precipitation Limits
- **Precipitation**: 0 mm < pr < 450 mm/day

#### Solar Radiation Limits
- **Rs (shortwave)**: 0 ≤ Rs < 40 MJ/m²/day
- **Special validation**: 0.03×Ra ≤ Rs < Ra (Xavier et al. validation)

#### Pressure Limits
- **P**: 900 hPa ≤ P ≤ 1100 hPa

**Use case**: Processing historical or current weather data for Brazil.

### 2. Global (Conservative World Limits)

Based on **world records and physical limits**.

#### Temperature Limits
- **Tmax**: -90°C < T < 60°C (world records)
- **Tmin**: -90°C < T < 60°C
- **T (mean)**: -90°C < T < 60°C

#### Humidity Limits
- **RH**: 0% ≤ RH ≤ 100%

#### Wind Speed Limits
- **Wind (u2)**: 0 m/s ≤ u2 ≤ 113 m/s (Category 5 hurricane)

#### Precipitation Limits
- **Precipitation**: 0 mm < pr < 2000 mm/day (record: ~1825 mm)

#### Solar Radiation Limits
- **Rs (shortwave)**: 0 ≤ Rs < 45 MJ/m²/day (theoretical limit)

#### Pressure Limits
- **P**: 800 hPa ≤ P ≤ 1150 hPa

**Use case**: Processing weather data for any global location outside Brazil.

## Usage

### 1. Validating Data with Region Parameter

```python
from backend.core.data_processing.data_preprocessing import data_initial_validate

# For Brazil data
weather_df, warnings = data_initial_validate(
    weather_df, 
    latitude=-10.0, 
    region="brazil"  # Use Xavier et al. limits
)

# For global data
weather_df, warnings = data_initial_validate(
    weather_df, 
    latitude=40.0, 
    region="global"  # Use conservative world limits (default)
)
```

### 2. Using Preprocessing Pipeline with Region

```python
from backend.core.data_processing.data_preprocessing import preprocessing

# For Brazil
df_clean, warnings = preprocessing(
    weather_df,
    latitude=-10.0,
    region="brazil"
)

# For global (default)
df_clean, warnings = preprocessing(
    weather_df,
    latitude=40.0
)
```

### 3. Using WeatherValidationUtils Directly

```python
from backend.api.services.weather_utils import WeatherValidationUtils

# Get Brazil limits
brazil_limits = WeatherValidationUtils.get_validation_limits("brazil")

# Validate temperature for Brazil
is_valid = WeatherValidationUtils.is_valid_temperature(
    temp=25.5, 
    region="brazil"
)

# Get global limits
global_limits = WeatherValidationUtils.get_validation_limits("global")
```

## Implementation Details

### Files Modified

1. **`backend/api/services/weather_utils.py`**
   - Added `REGIONAL_LIMITS` dictionary with Brazil and global limits
   - Added `get_validation_limits(region)` classmethod
   - Updated all validation methods to accept optional `region` parameter:
     - `is_valid_temperature(temp, region)`
     - `is_valid_humidity(humidity, region)`
     - `is_valid_wind_speed(wind, region)`
     - `is_valid_precipitation(precip, region)`
     - `is_valid_solar_radiation(solar, region)`

2. **`backend/core/data_processing/data_preprocessing.py`**
   - Added `_get_validation_limits(region)` helper function
   - Updated `data_initial_validate(weather_df, latitude, region)` signature
   - Updated `preprocessing(weather_df, latitude, cache_key, region)` signature
   - All validation now uses `_get_validation_limits(region)` instead of hardcoded values

### Data Sources Covered

Both regional limit sets support all 7 data sources for ETo calculations:
- **NASA POWER**: 7 variables
- **Open-Meteo Archive**: 13 variables
- **Open-Meteo Forecast**: 13 variables
- **MET Norway Locationforecast**: 9 variables
- **MET Norway FROST**: shared variables
- **NWS Forecast**: specific variables
- **NWS Stations**: specific variables

## Adding New Regions

To add support for a new region (e.g., "australia"), follow these steps:

### 1. Add to `weather_utils.py`

Add new limits to the `REGIONAL_LIMITS` dictionary:

```python
# In WeatherValidationUtils class
REGIONAL_LIMITS = {
    "brazil": {...},
    "global": {...},
    "australia": {  # NEW
        "temperature": (-50, 55),
        "humidity": (0, 100),
        "wind": (0, 100),
        "precipitation": (0, 500),
        "solar": (0, 42),
        "pressure": (950, 1050),
    }
}
```

### 2. Add to `data_preprocessing.py`

Extend the `_get_validation_limits()` function:

```python
def _get_validation_limits(region: str = "global") -> dict:
    """..."""
    australia_limits = {
        "T2M_MAX": (-50, 55, "neither"),
        "T2M_MIN": (-50, 55, "neither"),
        ...
    }
    
    if region.lower() == "australia":
        return australia_limits
    elif region.lower() == "brazil":
        return brazil_limits
    else:
        return global_limits
```

### 3. Update Integration Points

Update any API endpoints or services that call `preprocessing()` to accept and pass the `region` parameter.

## Validation Impact

Different limits can significantly affect data quality assessment:

### Example: Brazil vs Global for Temperature
- **Brazil limits**: -30°C to 50°C (more restrictive)
- **Global limits**: -90°C to 60°C (less restrictive)
- **Impact**: Some global data points valid in "global" mode would be flagged as invalid in "brazil" mode.

### Example: Precipitation
- **Brazil limits**: 0 mm < pr < 450 mm/day
- **Global limits**: 0 mm < pr < 2000 mm/day
- **Impact**: Extreme rainfall events (500-1000 mm/day) valid globally but invalid for Brazil.

## Scientific References

- **Xavier et al. (2016, 2022)**: "New improved Brazilian daily weather gridded data (1961–2020)"
  - Validates limits based on 60+ years of Brazilian climate data
  - Most appropriate for Brazilian historical data and forecasts
  
- **FAO-56**: Allen et al. (1998), "Crop Evapotranspiration (ETo)"
  - Recommended method for solar radiation validation
  - Constraint: 0.03×Ra ≤ Rs < Ra

## Future Work

- [ ] Add support for regional subdivisions (e.g., "brazil_northeast", "brazil_southeast")
- [ ] Add seasonal validation limits (different limits for wet vs dry season)
- [ ] Add elevation-dependent limits
- [ ] Integrate with climate classification systems (Köppen-Geiger)
- [ ] Add data source-specific limits (e.g., NOAA, INMET)
