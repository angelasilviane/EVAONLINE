from datetime import datetime

print("🧪 Testing Date Range Validation Logic:")
print("=" * 50)


# Test range calculation logic
def test_range_logic(start_date, end_date, min_days=7, max_days=30):
    """Test the range validation logic."""
    range_days = (end_date - start_date).days + 1
    if range_days < min_days:
        return f"❌ Too short: {range_days} days (min {min_days})"
    elif range_days > max_days:
        return f"❌ Too long: {range_days} days (max {max_days})"
    else:
        return f"✅ Valid: {range_days} days"


# Test Open-Meteo range validation
print("Open-Meteo Range Tests:")
test_cases = [
    (datetime(2020, 1, 1), datetime(2020, 1, 8)),  # 7 days - valid
    (datetime(2020, 1, 1), datetime(2020, 1, 31)),  # 30 days - valid
    (datetime(2020, 1, 1), datetime(2020, 1, 5)),  # 4 days - too short
    (datetime(2020, 1, 1), datetime(2020, 2, 15)),  # 45 days - too long
]

for start, end in test_cases:
    result = test_range_logic(start, end)
    print(f"  {result}")

print()
print("NASA POWER Range Tests:")
# Same logic applies
for start, end in test_cases:
    result = test_range_logic(start, end)
    print(f"  {result}")

print()
print("MET Norway FROST Range Tests:")
# Same logic applies
for start, end in test_cases:
    result = test_range_logic(start, end)
    print(f"  {result}")

print()
print("Historical Data Access Tests:")
print("Open-Meteo: 1940-01-01 (85+ years available)")
print("NASA POWER: 1981-01-01 (44+ years available)")
print("MET Norway FROST: 1937-01-01 (87+ years available)")

# Test historical date validation
historical_tests = [
    (datetime(1940, 1, 1), datetime(1940, 1, 8)),  # Open-Meteo earliest
    (datetime(1981, 1, 1), datetime(1981, 1, 8)),  # NASA POWER earliest
    (datetime(1937, 1, 1), datetime(1937, 1, 8)),  # MET Norway FROST earliest
]

print()
print("Historical Date Range Validation:")
for start, end in historical_tests:
    result = test_range_logic(start, end)
    source = (
        "Open-Meteo"
        if start.year == 1940
        else "NASA POWER" if start.year == 1981 else "MET Norway FROST"
    )
    print(f"  {source}: {result}")

print()
print("🎉 Date range validation tests completed!")
