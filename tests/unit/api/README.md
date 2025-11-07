"""
Climate API Unit Tests
======================

Comprehensive test suite for all climate data APIs and sync adapters.

Test Structure
--------------

tests/unit/api/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── test_nasa_power.py            # NASA POWER API tests
├── test_openmeteo_archive.py     # Open-Meteo Archive tests
├── test_openmeteo_forecast.py    # Open-Meteo Forecast tests (if needed)
├── test_met_norway.py            # MET Norway tests (if needed)
├── test_nws.py                   # NWS APIs tests (Forecast + Stations)
└── test_data_download.py         # Integration tests

Test Coverage
-------------

### Data Sources Tested:
1. **NASA POWER** (Global, 1981+)
   - Historical data downloads
   - Multi-location validation
   - Date range limits
   - Data quality checks

2. **Open-Meteo Archive** (Global, 1940+)
   - Historical data from 1940
   - Full year downloads
   - Extended variables validation
   - Date limits (1940 minimum)

3. **Open-Meteo Forecast** (Global, up to 16 days)
   - Short-term forecasts
   - Future date validation

4. **NWS Forecast** (USA only, up to 7 days)
   - USA Continental coverage
   - Non-USA rejection
   - Forecast data quality

5. **NWS Stations** (USA only, real-time)
   - Weather station observations
   - USA-only validation
   - Recent data downloads

### Test Locations:
- **Global**: São Paulo (Brazil), Berlin (Germany), Tokyo (Japan)
- **USA**: New York, Los Angeles, Chicago, Miami
- **Europe**: Oslo, Paris, Berlin
- **Edge Cases**: Arctic, Antarctic, Pacific Ocean

Running Tests
-------------

### Run All API Tests:
```bash
pytest tests/unit/api/ -v
```

### Run Specific API Tests:
```bash
# NASA POWER only
pytest tests/unit/api/test_nasa_power.py -v

# NWS APIs only
pytest tests/unit/api/test_nws.py -v

# Integration tests
pytest tests/unit/api/test_data_download.py -v
```

### Run with Output:
```bash
pytest tests/unit/api/ -v -s
```

### Run Specific Test Class:
```bash
pytest tests/unit/api/test_nasa_power.py::TestNASAPowerBasicDownload -v
```

### Run Single Test:
```bash
pytest tests/unit/api/test_nasa_power.py::TestNASAPowerBasicDownload::test_download_one_week -v
```

### Run Tests by Location:
```bash
# Test all sources for São Paulo
pytest tests/unit/api/ -k "sao_paulo" -v

# Test all USA-specific tests
pytest tests/unit/api/ -k "usa" -v
```

Test Categories
---------------

### 1. Basic Download Tests
- Single day, week, month, year downloads
- Different date ranges
- Recent vs historical data

### 2. Coverage Validation
- Geographic bounds checking
- USA-only sources (NWS)
- Global sources (NASA, Open-Meteo)
- Regional sources (MET Norway)

### 3. Data Quality Tests
- Temperature range validation
- Precipitation non-negativity
- Solar radiation bounds
- Variable completeness
- Data consistency (T_max >= T_min)

### 4. Date Limit Tests
- Earliest date validation (1981, 1940, etc.)
- Future date rejection
- Forecast horizon limits
- Historical data availability

### 5. Error Handling Tests
- Invalid coordinates
- Non-covered locations
- Invalid date formats
- End date before start date
- Invalid source names

### 6. Integration Tests (data_download.py)
- Complete workflow validation
- Source selection logic
- Multi-location support
- Warning generation

Expected Test Results
--------------------

### Passing Tests:
- **NASA POWER**: All global locations, 1981+ dates
- **Open-Meteo Archive**: All locations, 1940+ dates
- **Open-Meteo Forecast**: All locations, up to 16 days ahead
- **NWS**: USA locations only
- **Data Download**: Correct source routing

### Expected Failures (by design):
- **NWS with non-USA locations**: Should raise ValueError
- **Dates before 1981 (NASA)**: Should raise ValueError
- **Dates before 1940 (Open-Meteo)**: Should raise ValueError
- **Invalid coordinates**: Should raise ValueError
- **Invalid source names**: Should raise ValueError

Test Data
---------

### No External Dependencies:
- Tests use real APIs (no mocking)
- Validates actual API responses
- Tests real-world scenarios

### Rate Limiting:
- Tests are designed to respect API rate limits
- Use recent dates to avoid cache misses
- Parametrized tests run sequentially

### Data Validation:
- Physical bounds checking (temps, radiation, etc.)
- Structural validation (required fields)
- Temporal validation (date ordering)

Troubleshooting
---------------

### Tests Timing Out:
```bash
# Increase timeout
pytest tests/unit/api/ -v --timeout=60
```

### API Temporarily Unavailable:
- Check individual API status
- Health checks run first
- Retry failed tests after a few minutes

### Coverage Errors:
- NWS tests will fail outside USA (expected)
- MET Norway FROST needs OAuth2 credentials
- Check geographic coordinates

Adding New Tests
----------------

### Template for New API Tests:
```python
import pytest
from backend.api.services.your_api_sync_adapter import YourAdapter

@pytest.fixture
def adapter():
    return YourAdapter()

class TestYourAPIBasic:
    def test_download_data(self, adapter):
        data = adapter.get_data_sync(...)
        assert len(data) > 0
```

### Best Practices:
1. Test multiple locations
2. Validate data structure
3. Check physical bounds
4. Test error conditions
5. Add descriptive print statements
6. Use parametrize for similar tests

Performance Benchmarks
---------------------

Expected test execution times:
- **Single test**: ~2-5 seconds
- **Full test class**: ~30-60 seconds
- **All API tests**: ~5-10 minutes
- **With integration**: ~10-15 minutes

CI/CD Integration
-----------------

These tests are designed for CI/CD pipelines:
- No external credentials required (except FROST)
- Public APIs with generous rate limits
- Deterministic results
- Clear pass/fail conditions

For CI/CD, consider:
```yaml
- name: Run API Tests
  run: pytest tests/unit/api/ -v --tb=short
  timeout-minutes: 15
```

Maintenance
-----------

### Regular Updates Needed:
- API endpoint changes
- Coverage boundary updates
- New variable validation
- Date limit adjustments

### Monitoring:
- Watch for API deprecations
- Check rate limit changes
- Validate new API versions
- Update test locations if needed

Contact
-------

For issues or questions:
- Check API documentation first
- Review test output carefully
- Check GitHub issues
- Contact EVAonline team

Last Updated: November 2025
Author: EVAonline Development Team
"""
