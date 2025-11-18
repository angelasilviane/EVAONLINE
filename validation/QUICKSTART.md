# EVAonline Validation - Quick Start Commands

## 🚀 Recommended Workflow

### Step 1: Test API Connections (30 seconds)
```bash
python validation/scripts/test_api_connections.py
```
**Expected**: ✅ 7/7 services OK

---

### Step 2: Quick Test (1 city, 2 years - 5 minutes)
```bash
# Brasil: Barreiras/BA
python validation/scripts/calculate_eto_validation.py --region brasil --max-cities 1

# Global: Addis Ababa
python validation/scripts/calculate_eto_validation.py --region mundo --max-cities 1
```
**Expected output**: `validation/results/brasil/timeseries/Barreiras_BA_eto_calculated.csv`

---

### Step 3: Compare with Reference (10 seconds)
```bash
python validation/scripts/compare_metrics.py --region brasil --max-cities 1
```
**Expected**: MAE < 0.5 mm/day, r² > 0.80

---

### Step 4: Generate Plots (20 seconds)
```bash
python validation/scripts/visualize_results.py --region brasil
```
**Expected**: Scatter plot, time series, residuals in `validation/results/brasil/plots/`

---

## 🌎 Full Validation (Production Ready)

### Short Period (Last 2 years - RECOMMENDED)
```bash
# Brasil: 17 cities × 730 days = 12,410 days (~30-60 minutes)
python validation/scripts/calculate_eto_validation.py --region brasil

# Mundo: 10 cities × 730 days = 7,300 days (~20-40 minutes)
python validation/scripts/calculate_eto_validation.py --region mundo

# Metrics
python validation/scripts/compare_metrics.py --region both

# Visualizations
python validation/scripts/visualize_results.py --region both
```

---

### Long-Term Historical (1991-2024 - HOURS!)

#### Test First (1 city, full history - 30-60 minutes)
```bash
# Barreiras: 1961-2024 (63 years = 23,000+ days)
python validation/scripts/calculate_eto_longterm.py --region brasil --max-cities 1

# Addis Ababa: 1991-2024 (33 years = 12,000+ days)
python validation/scripts/calculate_eto_longterm.py --region mundo --max-cities 1
```

#### Full Historical Validation
```bash
# Brasil: 17 cities × 63 years = 391,000+ days (4-8 HOURS)
python validation/scripts/calculate_eto_longterm.py --region brasil

# Mundo: 10 cities × 33 years = 120,500+ days (2-4 HOURS)
python validation/scripts/calculate_eto_longterm.py --region mundo

# Custom range (e.g., 2000-2024 only)
python validation/scripts/calculate_eto_longterm.py --region brasil --start-year 2000 --end-year 2024
```

---

## 📊 Analysis Commands

### View Metrics Summary
```bash
# Brasil summary
cat validation/results/brasil/metrics/metrics_brasil.csv | column -t -s,

# Mundo summary
cat validation/results/mundo/metrics/metrics_mundo.csv | column -t -s,

# Consolidated report
cat validation/results/consolidated/global_metrics.csv | column -t -s,
```

### Check Logs
```bash
# Short validation log
tail -f validation/results/validation_pipeline.log

# Long-term validation log
tail -f validation/results/longterm_validation.log
```

### List Generated Files
```bash
# Calculated ETo files
ls -lh validation/results/brasil/timeseries/
ls -lh validation/results/mundo/timeseries/

# Plots
ls -lh validation/results/brasil/plots/
ls -lh validation/results/mundo/plots/
```

---

## 🐛 Troubleshooting Commands

### Test Single Year
```bash
# Test only 2023 for Barreiras
python validation/scripts/calculate_eto_longterm.py --region brasil --max-cities 1 --start-year 2023 --end-year 2023
```

### Resume Interrupted Validation
```bash
# Just re-run the same command - cache will resume automatically
python validation/scripts/calculate_eto_longterm.py --region brasil
```

### Clear Cache and Restart
```bash
# Remove cache directory
rm -rf validation/results/brasil/cache/
rm -rf validation/results/mundo/cache/

# Re-run validation
python validation/scripts/calculate_eto_longterm.py --region brasil
```

### Check API Rate Limits
```bash
# Test with increased delay (2.5s instead of 1.5s)
# Edit calculate_eto_longterm.py line 179:
# rate_limit_seconds: float = 2.5
```

---

## 📈 Expected Results

### Brasil (Xavier Reference)
```
MAE:  0.30-0.40 mm/day
RMSE: 0.40-0.55 mm/day
r²:   0.82-0.92
NSE:  0.80-0.90
```

### Mundo (OpenMeteo Reference)
```
MAE:  0.35-0.50 mm/day
RMSE: 0.50-0.70 mm/day
r²:   0.75-0.88
NSE:  0.70-0.85
```

---

## 🎯 Publication Quality Validation

### Complete Pipeline for Paper
```bash
# 1. Test connections
python validation/scripts/test_api_connections.py

# 2. Full historical validation (both regions)
python validation/scripts/calculate_eto_longterm.py --region brasil
python validation/scripts/calculate_eto_longterm.py --region mundo

# 3. Calculate all metrics
python validation/scripts/compare_metrics.py --region both

# 4. Generate all plots
python validation/scripts/visualize_results.py --region both

# 5. Results ready in:
# - validation/results/consolidated/global_metrics.csv
# - validation/results/brasil/plots/
# - validation/results/mundo/plots/
```

---

## 💡 Performance Tips

1. **Start small**: Always test 1 city first
2. **Use short period**: 2 years is enough for testing methodology
3. **Monitor logs**: Watch for API errors or rate limiting
4. **Incremental cache**: Long-term script saves progress automatically
5. **Parallel validation**: Run Brasil and Mundo in separate terminals
6. **Disk space**: Full validation needs ~500MB per region
7. **Network**: Stable internet required (thousands of API calls)
8. **Time**: Schedule long validations overnight

---

## 📝 Citation Data for Zenodo

After full validation, upload these files to Zenodo:

```
validation/results/
├── brasil/
│   ├── timeseries/          # 17 CSV files with calculated ETo
│   └── metrics/
│       └── metrics_brasil.csv
├── mundo/
│   ├── timeseries/          # 10 CSV files with calculated ETo
│   └── metrics/
│       └── metrics_mundo.csv
└── consolidated/
    ├── global_metrics.csv   # Summary table
    └── comparison_brasil_mundo.png
```

**Recommended Zenodo title**:
> EVAonline Validation Dataset: FAO-56 ETo Calculations (1991-2024) with Multi-Source Data Fusion and Kalman Ensemble

**Keywords**: Evapotranspiration, FAO-56 Penman-Monteith, Data Fusion, Kalman Filter, Climate Data, Xavier Dataset, OpenMeteo, NASA POWER
