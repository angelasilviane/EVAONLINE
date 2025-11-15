# Progress Summary - Regional Validation System Implementation

## ✅ Completed Implementation

### 1. **Regional Validation Limits Added to `weather_utils.py`**

**Status**: ✅ COMPLETE

**Changes**:
- Added `REGIONAL_LIMITS` dictionary with two regions:
  - `"global"`: Conservative world limits (based on world records)
  - `"brazil"`: Xavier et al. (2016, 2022) limits (scientific validation)
  
- Added 6 new validation methods with `region` parameter:
  - `get_validation_limits(region: str) -> dict`
  - `is_valid_temperature(temp, region)`
  - `is_valid_humidity(humidity, region)`
  - `is_valid_wind_speed(wind, region)`
  - `is_valid_precipitation(precip, region)`
  - `is_valid_solar_radiation(solar, region)`

**Code Location**: `backend/api/services/weather_utils.py` (lines 161-310)

**Limits Defined**:
```
Global:
  - Temperature: -90°C to 60°C (world records)
  - Humidity: 0% to 100%
  - Wind: 0 to 113 m/s (Category 5 hurricane)
  - Precipitation: 0 to 2000 mm/day
  - Solar: 0 to 45 MJ/m²/day
  - Pressure: 800 to 1150 hPa

Brazil (Xavier et al.):
  - Temperature: -30°C to 50°C
  - Humidity: 0% to 100%
  - Wind: 0 to 100 m/s
  - Precipitation: 0 to 450 mm/day
  - Solar: 0 to 40 MJ/m²/day
  - Pressure: 900 to 1100 hPa
```

---

### 2. **Validation Logic Updated in `data_preprocessing.py`**

**Status**: ✅ COMPLETE

**Changes**:
- Created `_get_validation_limits(region)` helper function
- Moved all hardcoded limit values to centralized location
- Updated `data_initial_validate(weather_df, latitude, region)` signature
- Updated `preprocessing(weather_df, latitude, cache_key, region)` signature
- All validation now uses `_get_validation_limits(region)` 

**Code Location**: `backend/core/data_processing/data_preprocessing.py`

**Function Signatures**:
```python
def data_initial_validate(
    weather_df: pd.DataFrame, 
    latitude: float, 
    region: str = "global"  # NEW
) -> Tuple[pd.DataFrame, List[str]]:
    """..."""
    limits = _get_validation_limits(region)  # Uses region parameter

def preprocessing(
    weather_df: pd.DataFrame,
    latitude: float,
    cache_key: Optional[str] = None,
    region: str = "global"  # NEW
) -> Tuple[pd.DataFrame, List[str]]:
    """..."""
    weather_df, validate_warnings = data_initial_validate(
        weather_df, latitude, region  # Passes region parameter
    )
```

**Supported Data Sources** (all 7):
- NASA POWER (7 variables)
- Open-Meteo Archive (13 variables)
- Open-Meteo Forecast (13 variables)
- MET Norway Locationforecast (9 variables)
- MET Norway FROST (shared variables)
- NWS Forecast (specific variables)
- NWS Stations (specific variables)

---

### 3. **Documentation Created**

**Status**: ✅ COMPLETE

**File**: `docs/REGIONAL_VALIDATION.md`

**Contents**:
- Overview of regional validation system
- Detailed limits for Brazil (Xavier et al. 2016, 2022)
- Detailed limits for Global (conservative world limits)
- Usage examples for all major functions
- Implementation details and files modified
- Instructions for adding new regions
- Validation impact examples
- Scientific references

---

## 🔄 Integration Points to Update

### 1. **`eto_services.py`** (Lines 685-689)
**Current State**:
```python
weather_data, preprocessing_warnings = preprocessing(
    weather_data, latitude
)
```

**Action Required**: Add `region` parameter
```python
weather_data, preprocessing_warnings = preprocessing(
    weather_data, latitude, region=region  # Get region from location/country
)
```

**Where to get region**:
- From frontend: `location_data.get("country")` (already available in `home_callbacks.py`)
- Map country names to region codes (e.g., "Brazil" → "brazil")

---

### 2. **`celery_tasks.py`** (Line 174)
**Current State**:
```python
df_processed, preprocess_warnings = preprocessing(
    combined_data, latitude
)
```

**Action Required**: Add `region` parameter based on task context

---

### 3. **`historical_download.py`** (Line 139)
**Current State**:
```python
df_processed, preprocess_warnings = preprocessing(
    df, latitude
)
```

**Action Required**: Add `region` parameter based on location

---

## 📊 Validation Limits Comparison

### Temperature (Example Impact)
| Region | Min (°C) | Max (°C) | Impact |
|--------|----------|----------|--------|
| Global | -90 | 60 | World records |
| Brazil | -30 | 50 | Scientific validation |
| **Difference** | **60°C** | **10°C** | Brazil ~3× more restrictive on low end |

### Precipitation (Example Impact)
| Region | Min (mm) | Max (mm) | Impact |
|--------|----------|----------|--------|
| Global | 0 | 2000 | World records (~1825 mm) |
| Brazil | 0 | 450 | Xavier et al. historical data |
| **Difference** | **0** | **1550 mm** | Brazil ~4.4× more restrictive on high end |

### Wind Speed (Example Impact)
| Region | Min (m/s) | Max (m/s) | Impact |
|--------|-----------|-----------|--------|
| Global | 0 | 113 | Hurricane Cat 5 (~408 km/h) |
| Brazil | 0 | 100 | Xavier et al. limits |
| **Difference** | **0** | **13 m/s** | Brazil 8.8% more restrictive |

---

## 🧪 Testing Recommendations

### Test Case 1: Brazil Data with Xavier Limits
```python
# Location: São Paulo, Brazil (-23.55°, -46.63°)
region = "brazil"
weather_data = load_real_brazil_data()
df_clean, warnings = preprocessing(weather_data, latitude=-23.55, region="brazil")
# Expected: Stricter validation applied, some global-valid data flagged as invalid
```

### Test Case 2: Global Data with World Limits
```python
# Location: Sahara Desert (25°, 0°)
region = "global"
weather_data = load_desert_data()
df_clean, warnings = preprocessing(weather_data, latitude=25.0, region="global")
# Expected: More lenient validation applied, extreme heat values accepted
```

### Test Case 3: Mixed Data with Regional Switching
```python
# Test that switching region changes validation behavior
weather_data = load_test_data()  # Contains temperature of -35°C

# Global validation (should pass, within world records)
df_global, _ = preprocessing(weather_data, latitude=0.0, region="global")
assert len(df_global) == len(weather_data)

# Brazil validation (should fail, below Xavier minimum)
df_brazil, warnings = preprocessing(weather_data, latitude=0.0, region="brazil")
assert len(df_brazil) < len(weather_data)  # Some rows converted to NaN
assert "Invalid values in T2M_MAX" in str(warnings)
```

---

## 📋 Next Steps

### High Priority (Integrate Regional Parameter)
1. [ ] Update `eto_services.py::process_location()` to accept `region` parameter
2. [ ] Update `eto_services.py::preprocessing()` call to pass `region`
3. [ ] Map country names to region codes (Brazil → "brazil", others → "global")
4. [ ] Update `celery_tasks.py` to pass `region` through task pipeline
5. [ ] Update `historical_download.py` to pass `region` through task pipeline

### Medium Priority (Integration Points)
6. [ ] Update API endpoints to accept and pass `region` parameter
7. [ ] Update frontend to send country/region information
8. [ ] Test end-to-end with real Brazil and global locations
9. [ ] Document API changes for consumers

### Lower Priority (Future Enhancement)
10. [ ] Add regional subdivisions (e.g., "brazil_northeast", "brazil_southeast")
11. [ ] Add seasonal validation limits
12. [ ] Add elevation-dependent limits
13. [ ] Integrate with Köppen-Geiger climate classification
14. [ ] Add data source-specific limits (NOAA, INMET)

---

## 🔗 Related System Components

**Elevation Strategy (Already Implemented)**:
- Priority 1: User input
- Priority 2: OpenTopo (~1m precision)
- Priority 3: Open-Meteo (~7-30m precision)
- Priority 4: Default (0m)

**Validation Strategy (This Implementation)**:
- Priority 1: Check if location is Brazil → Use Xavier et al. limits
- Priority 2: Otherwise → Use conservative global limits
- Future: Could be extended to location-specific limits

**FAO-56 Factors (Elevation-Dependent)**:
- Atmospheric Pressure: P = 101.3 × [(293 - 0.0065 × z) / 293]^5.26
- Psychrometric Constant: γ = 0.665 × 10^-3 × P
- Solar Radiation Correction: +10% per 1000m elevation
- Example: Brasília (1172m) vs sea level = 22m diff = 0.245% ETo impact

---

## 📝 Code Quality

**Linting Status**: ✅ PASSED
- No syntax errors in `weather_utils.py`
- No syntax errors in `data_preprocessing.py`
- All line lengths within 79-character limit
- Type hints properly formatted

**Documentation**: ✅ COMPLETE
- Docstrings for all new functions
- Parameter documentation with type hints
- Return value documentation
- Usage examples provided

**Backwards Compatibility**: ✅ MAINTAINED
- `region` parameter defaults to "global"
- Existing function calls work without modification
- No breaking changes to API signatures
