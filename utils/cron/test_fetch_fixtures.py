# test_fetch_fixtures.py

from fetch_latest_data import fetch_fixtures

# Run the fetch_fixtures function directly
fixtures = fetch_fixtures()

if fixtures:
    print(f"✅ Test Passed: Retrieved {len(fixtures)} fixtures.")
else:
    print("❌ Test Failed: No fixtures found.")
