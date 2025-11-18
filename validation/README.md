# 📊 EVAonline Validation Framework

## Overview

This directory contains a comprehensive validation framework for EVAonline's FAO-56 Penman-Monteith ETo calculation method. The validation compares our calculations against two authoritative reference datasets:

1. **Brazil (MATOPIBA + Piracicaba)**: Xavier et al. (2016) gridded dataset - 17 cities
2. **Global**: OpenMeteo Archive pre-computed ETo - 10 cities across 5 continents

## Validation Datasets

### 🇧🇷 Brazil Reference (Xavier et al.)
- **Source**: Xavier, A. C., King, C. W., & Scanlon, B. R. (2016). Daily gridded meteorological variables in Brazil (1980-2013). *International Journal of Climatology*, 36(6), 2644-2659.
- **Coverage**: 1980-2020, 0.25° resolution
- **Quality**: Derived from 3,000+ meteorological stations
- **Cities**: 17 locations (16 MATOPIBA + Piracicaba/SP)

| City | State | Lat | Lon | Period |
|------|-------|-----|-----|--------|
| Alvorada do Gurgueia | PI | -8.43 | -43.77 | 2010-2020 |
| Araguaína | TO | -7.19 | -48.21 | 2010-2020 |
| Balsas | MA | -7.53 | -46.04 | 2010-2020 |
| Barreiras | BA | -12.15 | -45.00 | 2010-2020 |
| Bom Jesus | PI | -9.08 | -44.36 | 2010-2020 |
| Campos Lindos | TO | -7.99 | -46.87 | 2010-2020 |
| Carolina | MA | -7.33 | -47.47 | 2010-2020 |
| Corrente | PI | -10.44 | -45.16 | 2010-2020 |
| Formosa do Rio Preto | BA | -11.05 | -45.20 | 2010-2020 |
| Imperatriz | MA | -5.53 | -47.48 | 2010-2020 |
| Luiz Eduardo Magalhães | BA | -12.09 | -45.82 | 2010-2020 |
| Pedro Afonso | TO | -8.97 | -48.17 | 2010-2020 |
| Piracicaba | SP | -22.72 | -47.65 | 2010-2020 |
| Porto Nacional | TO | -10.71 | -48.42 | 2010-2020 |
| São Desidério | BA | -12.36 | -44.97 | 2010-2020 |
| Tasso Fragoso | MA | -8.52 | -46.24 | 2010-2020 |
| Uruçuí | PI | -7.24 | -44.55 | 2010-2020 |

### 🌍 Global Reference (OpenMeteo)
- **Source**: OpenMeteo Archive API (ERA5-Land reanalysis)
- **Coverage**: 1990-present, 11km resolution
- **Quality**: ECMWF operational model, validated globally
- **Cities**: 10 diverse agricultural regions

| City | Country | Lat | Lon | Climate |
|------|---------|-----|-----|---------|
| Addis Ababa | Ethiopia | 9.03 | 38.74 | Tropical highland |
| Des Moines | USA | 41.59 | -93.62 | Humid continental |
| Fresno | USA | 36.75 | -119.77 | Mediterranean hot |
| Hanoi | Vietnam | 21.03 | 105.85 | Humid subtropical |
| Krasnodar | Russia | 45.04 | 38.98 | Humid subtropical |
| Ludhiana | India | 30.90 | 75.85 | Semi-arid |
| Mendoza | Argentina | -32.89 | -68.83 | Arid cold |
| Polokwane | South Africa | -23.90 | 29.47 | Semi-arid |
| Seville | Spain | 37.39 | -5.98 | Mediterranean |
| Wagga Wagga | Australia | -35.12 | 147.37 | Semi-arid |

## Validation Metrics

### Statistical Metrics
- **MAE** (Mean Absolute Error): Average absolute difference (mm/day)
- **RMSE** (Root Mean Square Error): Square root of mean squared differences (mm/day)
- **MBE** (Mean Bias Error): Average systematic over/underestimation (mm/day)
- **MAPE** (Mean Absolute Percentage Error): Percentage relative error (%)
- **r** (Pearson Correlation): Linear correlation coefficient
- **r²** (Coefficient of Determination): Proportion of variance explained
- **NSE** (Nash-Sutcliffe Efficiency): Model efficiency (-∞ to 1, 1 = perfect)
- **d** (Willmott's Index of Agreement): Degree of model prediction accuracy (0 to 1)

### Visual Diagnostics
- **Scatter plots**: Observed vs. Predicted with 1:1 line
- **Time series**: Daily ETo comparison
- **Residual plots**: Error distribution over time
- **Taylor diagrams**: Multi-metric visualization
- **Box plots**: Error distribution by season/city

## Directory Structure

```
validation/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── config.py                    # Central configuration
├── scripts/
│   ├── calculate_eto_validation.py   # Recalculate ETo with our method
│   ├── compare_metrics.py            # Compute validation metrics
│   ├── generate_reports.py           # Generate summary reports
│   └── visualize_results.py          # Create validation plots
├── results/
│   ├── brasil/                  # Brazil validation results
│   ├── mundo/                   # Global validation results
│   └── consolidated/            # Combined analysis
├── notebooks/                   # Jupyter notebooks for exploration
└── tests/                       # Unit tests for validation code
```

## Usage

### 1. Install Dependencies
```bash
pip install -r validation/requirements.txt
```

### 2. Test API Connections (RECOMMENDED FIRST)
```bash
# Test all 6 climate APIs before starting validation
python validation/scripts/test_api_connections.py

# Expected output: ✅ 7/7 services OK
# Critical: OpenMeteo Archive, NASA POWER, OpenTopo must work
```

### 3. Run REAL Validation Pipeline

#### 🚀 Quick Test (1 city, last 2 years - 5 minutes)
```bash
# Test Brasil: Barreiras/BA
python validation/scripts/calculate_eto_validation.py --region brasil --max-cities 1

# Test Global: Addis Ababa
python validation/scripts/calculate_eto_validation.py --region mundo --max-cities 1
```

#### 📊 Short Validation (Recent years only - RECOMMENDED for testing)
```bash
# Last 2 years only (17 cities × 730 days = 12,410 days)
python validation/scripts/calculate_eto_validation.py --region brasil

# Last 2 years global (10 cities × 730 days = 7,300 days)
python validation/scripts/calculate_eto_validation.py --region mundo
```

#### 🕐 FULL HISTORICAL VALIDATION (30+ years - HOURS!)

**⚠️ WARNING: This processes MILLIONS of data points!**
- Brasil: 1961-2024 (63 years × 17 cities = 391,000+ days)
- Mundo: 1991-2024 (33 years × 10 cities = 120,500+ days)

```bash
# Use the OPTIMIZED script for long periods:

# Test 1 city first (Barreiras: 1961-2024 = 23,000 days)
python validation/scripts/calculate_eto_longterm.py --region brasil --max-cities 1

# Full Brasil validation (expect 4-8 HOURS)
python validation/scripts/calculate_eto_longterm.py --region brasil

# Full Global validation (expect 2-4 HOURS)
python validation/scripts/calculate_eto_longterm.py --region mundo

# Custom year range (e.g., 2010-2024 only)
python validation/scripts/calculate_eto_longterm.py --region brasil --start-year 2010 --end-year 2024
```

**Long-term script features:**
- ✅ **Annual batches**: 365-day chunks (more reliable than 90-day limit)
- ✅ **Incremental cache**: Saves progress after each year (resume if interrupted)
- ✅ **Automatic retry**: 3 attempts per batch with exponential backoff
- ✅ **Rate limiting**: 1.5s delay between requests (avoid API blocking)
- ✅ **Progress tracking**: Real-time ETA and completion percentage
- ✅ **Memory efficient**: Year-by-year processing (not all at once)

**What both scripts do (REAL PRODUCTION CODE):**
1. 📐 **Elevation**: Fetches from OpenTopo API (SRTM 30m resolution)
2. 📡 **Climate Data**: Downloads from 6 real APIs:
   - OpenMeteo Archive (historical)
   - OpenMeteo Forecast (recent + future)
   - NASA POWER (global coverage)
   - MET Norway (Nordic region)
   - NWS Forecast (USA)
   - NWS Stations (USA real-time)
3. ✅ **Validation**: Physical ranges (WMO/NOAA), outlier detection (IQR)
4. 🔀 **Fusion**: Kalman Ensemble (adaptive with historical DB or simple)
5. 🧮 **ETo Calculation**: FAO-56 Penman-Monteith with elevation corrections
6. 💾 **Save**: CSV files in `validation/results/{brasil|mundo}/timeseries/`

### 4. Compute Validation Metrics
```bash
# After calculating ETo, compare with reference datasets
python validation/scripts/compare_metrics.py --region brasil
python validation/scripts/compare_metrics.py --region mundo
python validation/scripts/compare_metrics.py --region both

# This computes 10 statistical metrics:
# MAE, RMSE, MBE, MAPE, r, r², NSE, d, KGE, PBIAS
```

### 5. Generate Visualizations
```bash
# Create scatter plots, time series, residuals, Taylor diagrams
python validation/scripts/visualize_results.py --region brasil
python validation/scripts/visualize_results.py --region mundo
python validation/scripts/visualize_results.py --region both

# Generates:
# - Scatter plots (observed vs predicted)
# - Time series with residuals
# - Residual analysis (histogram, Q-Q plot, monthly boxplots)
# - Regional summaries (bar charts, pie charts)
```

### 6. View Results
- **Calculated ETo**: `validation/results/{brasil|mundo}/timeseries/*.csv`
- **Incremental cache**: `validation/results/{brasil|mundo}/cache/*.parquet` (auto-cleanup)
- **Metrics**: `validation/results/{brasil|mundo}/metrics/metrics_{region}.csv`
- **Plots**: `validation/results/{brasil|mundo}/plots/*.png`
- **Consolidated**: `validation/results/consolidated/global_metrics.csv`
- **Logs**: 
  - Short validation: `validation/results/validation_pipeline.log`
  - Long-term: `validation/results/longterm_validation.log`

### 7. Troubleshooting

#### APIs not responding?
```bash
# Re-run connection test
python validation/scripts/test_api_connections.py

# If OpenMeteo or NASA POWER fail:
# - Check internet connection
# - Wait 5 minutes (rate limiting)
# - Check API status: https://open-meteo.com/
```

#### Interrupted during long validation?
```bash
# The script automatically resumes from cache!
# Just re-run the same command - it will skip completed years
python validation/scripts/calculate_eto_longterm.py --region brasil
```

#### Out of memory?
```bash
# The long-term script is already optimized
# If still fails, process fewer cities:
python validation/scripts/calculate_eto_longterm.py --region brasil --max-cities 5
```

#### Rate limited by APIs?
```bash
# Increase delay between requests (default: 1.5s)
# Edit calculate_eto_longterm.py:
# rate_limit_seconds: float = 2.5  # Increase to 2.5 seconds
```

## Expected Results

### Brazil (Xavier Reference)
- **MAE**: 0.30-0.35 mm/day
- **RMSE**: 0.40-0.50 mm/day
- **r²**: > 0.85
- **NSE**: > 0.80

### Global (OpenMeteo Reference)
- **MAE**: 0.35-0.45 mm/day
- **RMSE**: 0.50-0.65 mm/day
- **r²**: > 0.80
- **NSE**: > 0.75

## Interpretation Guidelines

### Excellent Agreement
- MAE < 0.3 mm/day
- RMSE < 0.4 mm/day
- r² > 0.90
- NSE > 0.85

### Good Agreement
- MAE: 0.3-0.5 mm/day
- RMSE: 0.4-0.7 mm/day
- r²: 0.80-0.90
- NSE: 0.75-0.85

### Acceptable Agreement
- MAE: 0.5-0.8 mm/day
- RMSE: 0.7-1.0 mm/day
- r²: 0.70-0.80
- NSE: 0.60-0.75

### Poor Agreement (Requires Investigation)
- MAE > 0.8 mm/day
- RMSE > 1.0 mm/day
- r² < 0.70
- NSE < 0.60

## References

1. Xavier, A. C., King, C. W., & Scanlon, B. R. (2016). Daily gridded meteorological variables in Brazil (1980-2013). *International Journal of Climatology*, 36(6), 2644-2659.

2. Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). *Crop evapotranspiration-Guidelines for computing crop water requirements*. FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.

3. Nash, J. E., & Sutcliffe, J. V. (1970). River flow forecasting through conceptual models part I—A discussion of principles. *Journal of Hydrology*, 10(3), 282-290.

4. Willmott, C. J. (1981). On the validation of models. *Physical Geography*, 2(2), 184-194.

## Contributing

To add new validation cities or metrics:
1. Add city data to `data/csv/BRASIL/` or `data/csv/MUNDO/`
2. Update `validation/config.py` with city metadata
3. Run validation pipeline
4. Document results in this README

## License

This validation framework is part of EVAonline (AGPL-3.0). Reference datasets:
- Xavier data: CC-BY-4.0
- OpenMeteo: CC-BY-4.0
