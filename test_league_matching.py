# test_league_matching.py
#
# This script tests if the league matching works for all supported leagues
# It verifies that our solution can find fixtures for all leagues, not just EPL

import logging
import sys
from fetch_data import fetch_fixture_inputs
import argparse

# Setup logging to show detailed information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# All supported leagues from the bot
SUPPORTED_LEAGUES = {
    "EPL": "English Premier League",
    "LaLiga": "Spanish La Liga",
    "SerieA": "Italian Serie A",
    "Bundesliga": "German Bundesliga",
    "Ligue1": "French Ligue 1",
    "PrimeiraLiga": "Portuguese Primeira Liga",
    "Eredivisie": "Dutch Eredivisie",
    "ProLeague": "Belgian Pro League",
    "SPL": "Scottish Premiership",
    "SuperLig": "Turkish Süper Lig",
    "BundesligaAT": "Austrian Bundesliga",
    "SuperLeagueCH": "Swiss Super League",
    "Superliga": "Danish Superliga",
    "Eliteserien": "Norwegian Eliteserien",
    "Allsvenskan": "Swedish Allsvenskan",
    "UPL": "Ukrainian Premier League",
    "SuperLeagueGR": "Greek Super League",
    "FortunaLiga": "Czech Fortuna Liga",
    "HNL": "Croatian Prva HNL",
    "SuperLigaRS": "Serbian SuperLiga",
    "Ekstraklasa": "Polish Ekstraklasa"
}

def test_league_fixtures(league_name, for_tomorrow=False):
    """Test if we can find fixtures for a specific league"""
    print(f"\n{'='*40}")
    print(f"Testing {SUPPORTED_LEAGUES.get(league_name, league_name)}")
    print(f"{'='*40}")
    
    fixtures = fetch_fixture_inputs(league_name, for_tomorrow=for_tomorrow)
    if isinstance(fixtures, list):
        if fixtures:
            print(f"✅ Success! Found {len(fixtures)} fixtures for {league_name}")
            print("Sample matches:")
            for i, fx in enumerate(fixtures[:3]):  # Show first 3 fixtures
                print(f"  {i+1}. {fx['home_team']} vs {fx['away_team']}")
            return True
        else:
            print(f"⚠️ No fixtures found for {league_name} (this might be expected if there are no games)")
            return False
    else:
        print(f"❌ Error: {fixtures}")
        return False

def test_all_leagues(for_tomorrow=False):
    """Test fixture finding for all supported leagues"""
    day_str = "tomorrow" if for_tomorrow else "today"
    print(f"\n📊 Testing fixture matching for all leagues ({day_str})")
    
    success_count = 0
    total_count = len(SUPPORTED_LEAGUES)
    
    for league_code in SUPPORTED_LEAGUES:
        if test_league_fixtures(league_code, for_tomorrow):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: Successfully found fixtures for {success_count}/{total_count} leagues")
    print(f"{'='*60}")
    
    # Note: Not all leagues will have fixtures every day, so success_count may be legitimately lower

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test league fixture matching")
    parser.add_argument("--league", "-l", default=None, help="Test a specific league code (e.g., EPL)")
    parser.add_argument("--tomorrow", "-t", action="store_true", help="Test fixtures for tomorrow")
    
    args = parser.parse_args()
    
    if args.league:
        test_league_fixtures(args.league, args.tomorrow)
    else:
        test_all_leagues(args.tomorrow)
