# fetch_latest_data.py
# -*- coding: utf-8 -*-

import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path
import time
import argparse
from datetime import timezone

load_dotenv()

# Create necessary folders
Path("data/live").mkdir(parents=True, exist_ok=True)
Path("cache").mkdir(parents=True, exist_ok=True)
Path("utils/cron/cache").mkdir(parents=True, exist_ok=True)

# Cache directories
MAIN_CACHE_DIR = Path("cache")
CRON_CACHE_DIR = Path("utils/cron/cache")

# Function to ensure both cache directories are synchronized
def update_both_caches(filename, data):
    """Write data to both main and cron cache directories"""
    for cache_dir in [MAIN_CACHE_DIR, CRON_CACHE_DIR]:
        file_path = cache_dir / filename
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f)
            print(f"✅ Updated {file_path}")
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")

# Clear old fixture files before fetching new ones
def clear_fixture_cache():
    """Remove old fixture files to avoid stale data"""
    for cache_dir in [MAIN_CACHE_DIR, CRON_CACHE_DIR]:
        try:
            for fixture_file in cache_dir.glob("fixtures_*.json"):
                try:
                    fixture_file.unlink()
                    print(f"🗑️ Removed old fixture file: {fixture_file}")
                except Exception as e:
                    print(f"⚠️ Failed to remove {fixture_file}: {e}")
        except Exception as e:
            print(f"⚠️ Error clearing fixture cache in {cache_dir}: {e}")

# Supported leagues with API-Football league IDs
SUPPORTED_LEAGUES = {
    "EPL": 39,
    "LaLiga": 140,
    "SerieA": 135,
    "Bundesliga": 78,
    "Ligue1": 61,
    "PrimeiraLiga": 94,
    "Eredivisie": 88,
    "ProLeague": 144,
    "SPL": 179,
    "SuperLig": 203,
    "BundesligaAT": 218,
    "SuperLeagueCH": 222,
    "Superliga": 197,
    "Eliteserien": 106,
    "Allsvenskan": 121,
    "UPL": 332,
    "SuperLeagueGR": 200,
    "FortunaLiga": 233,
    "HNL": 241,
    "SuperLigaRS": 237,
    "Ekstraklasa": 205,
    "NBI": 218,
    "Liga1": 94,
    "FirstDivisionCY": 222,
    "PremierLeagueIL": 208
}

# Mapping of your SUPPORTED_LEAGUES keys to The Odds API sports keys
SPORTS_MAPPING = {
    "EPL": "E0",
    "LaLiga": "SP1",
    "SerieA": "I1",
    "Bundesliga": "D1",
    "Ligue1": "F1",
    "PrimeiraLiga": "P1",
    "Eredivisie": "N1",
    "ProLeague": "B1",
    "SPL": "SC0",
    "SuperLig": "T1",
    "BundesligaAT": "A1",
    "SuperLeagueCH": "SW1",
    "Superliga": "DK1",
    "Eliteserien": "NW1",
    "Allsvenskan": "S1",
    "UPL": "UKR1",
    "SuperLeagueGR": "G1",
    "FortunaLiga": "CZ1",
    "HNL": "HR1",
    "SuperLigaRS": "SRB1",
    "Ekstraklasa": "PL1",
    "NBI": "HU1",
    "Liga1": "RO1",
    "FirstDivisionCY": "CY1",
    "PremierLeagueIL": "ISR1"
}



buffer_start = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
buffer_end = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")


def is_cache_valid(filepath: str, max_age_seconds: int = 86400) -> bool:
    if not os.path.exists(filepath):
        return False
    file_mtime = os.path.getmtime(filepath)
    return (time.time() - file_mtime) < max_age_seconds


def retry_request(url, headers=None, params=None, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise Exception(f"❌ All {retries} attempts failed for {url}")


def get_cached_active_leagues(cache_path="cache/active_leagues.json", max_age_hours=6):
    if is_cache_valid(cache_path, max_age_seconds=max_age_hours * 3600):
        with open(cache_path, "r") as f:
            cached = json.load(f)
            print("🛡️ Using cached active leagues.")
            return set(cached["league_ids"])
    return None


def cache_active_leagues(league_ids, cache_path="cache/active_leagues.json"):
    with open(cache_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "league_ids": list(league_ids)
        }, f)


def fetch_active_leagues() -> set:
    cache_path = "cache/active_leagues.json"
    cached = get_cached_active_leagues(cache_path=cache_path)

    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        raise ValueError("❌ Missing API_FOOTBALL_KEY in .env")

    try:
        print("📡 Fetching active leagues from API-Football...")
        response = retry_request(
            "https://v3.football.api-sports.io/leagues",
            headers={"x-apisports-key": api_key}
        )
        leagues = response.json().get("response", [])
        active_leagues = set()
        current_year = datetime.now().year

        for league_info in leagues:
            for season in league_info.get("seasons", []):
                if (
                    season.get("year") in {current_year, current_year - 1}
                    and season.get("coverage", {}).get("fixtures", {}).get("events", False)
                ):
                    active_leagues.add(league_info["league"]["id"])

        print(f"✅ Found {len(active_leagues)} active leagues.")
        cache_active_leagues(active_leagues, cache_path=cache_path)

        # Filter only supported ones
        supported_ids = set(SUPPORTED_LEAGUES.values())
        targeted = active_leagues.intersection(supported_ids)
        print(f"🎯 Targeting {len(targeted)} supported leagues from {len(active_leagues)} active.")
        return targeted

    except Exception as e:
        print(f"⚠️ Error fetching active leagues: {e}")
        if cached:
            print("⚠️ Using cached active leagues as fallback due to API failure.")
            return cached
        else:
            print("❌ No cached active leagues available.")
            return set()


def fetch_odds():
    odds_api_key = os.getenv("ODDS_API_KEY")
    if not odds_api_key:
        raise ValueError("❌ Missing ODDS_API_KEY in .env")

    cache_path = Path("data/live/latest_odds.json")

    if cache_path.exists():
        with open(cache_path, "r") as f:
            cached = json.load(f)
            timestamp = datetime.fromisoformat(cached.get("timestamp", datetime.min.isoformat()))
            if datetime.now() - timestamp < timedelta(hours=12):
                print("🛡️ Using fresh cached odds.")
                return cached.get("data", {})

    try:
        print("📡 Validating available sports...")
        response = retry_request(
            "https://api.the-odds-api.com/v4/sports",
            params={"api_key": odds_api_key}
        )
        available_sports = {sport["key"] for sport in response.json()}

        valid_mapping = {
            code: key for code, key in SPORTS_MAPPING.items()
            if key in available_sports
        }

        print(f"✅ Found {len(valid_mapping)} valid leagues out of {len(SPORTS_MAPPING)}.")

        all_odds = {}
        failed_leagues = []

        for league_code, sport_key in valid_mapping.items():
            try:
                print(f"Fetching odds for: {league_code} ({sport_key})")
                odds_response = retry_request(
                    f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
                    params={
                        "api_key": odds_api_key,
                        "regions": "eu",
                        "markets": "h2h",
                        "oddsFormat": "decimal"
                    }
                )
                if odds_response.status_code == 200:
                    all_odds[league_code] = odds_response.json()
                else:
                    print(f"⚠️ No odds for {league_code} (status: {odds_response.status_code})")
                    failed_leagues.append(league_code)

                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Failed: {league_code} — {e}")
                failed_leagues.append(league_code)

        with open(cache_path, "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "data": all_odds}, f, indent=2)
        print(f"✅ Saved odds. Failed leagues: {failed_leagues if failed_leagues else 'None'}")
        return all_odds

    except Exception as e:
        print(f"❌ Failed to fetch sports or odds: {e}")
        return {}


def fetch_fixtures():
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        raise ValueError("❌ Missing API_FOOTBALL_KEY in .env")

    active_leagues = fetch_active_leagues()

    if not active_leagues:
        print("⚠️ No active leagues found.")
        return []    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    tomorrow = (now_utc + timedelta(days=1)).date()
    
    print(f"📅 Date Range for Fixtures: {today} to {tomorrow}")
    
    # Clear any old fixture caches
    clear_fixture_cache()

    all_fixtures = []

    for league_id in active_leagues:
        try:
            print(f"📅 Fetching fixtures for league ID {league_id}...")
            
            # Automatically detect the latest active season for the league
            season_response = retry_request(
                "https://v3.football.api-sports.io/leagues",
                headers={"x-apisports-key": api_key},
                params={"id": league_id}
            )
            season_data = season_response.json().get("response", [])
            if not season_data:
                print(f"⚠️ No season data found for league {league_id}.")
                continue
            
            # Get the latest active season for the league
            latest_season = max(season["seasons"][-1]["year"] for season in season_data if season["seasons"])
            print(f"🔍 Detected latest season for league {league_id}: {latest_season}")            # Fetch fixtures only for today and tomorrow in the latest season
            response = retry_request(
                "https://v3.football.api-sports.io/fixtures",
                headers={"x-apisports-key": api_key},
                params={
                    "league": league_id,
                    "season": latest_season,
                    "from": today.isoformat(),
                    "to": tomorrow.isoformat()
                }
            )
            response_data = response.json()
            
            # Save to both cache locations
            update_both_caches(f"fixtures_{league_id}.json", response_data)
            
            fixtures_for_league = response_data.get("response", [])
            if fixtures_for_league:
                print(f"✅ Retrieved {len(fixtures_for_league)} fixtures for league {league_id}.")
                all_fixtures.extend(fixtures_for_league)
            else:
                print(f"⚠️ No fixtures found for league {league_id} in this range.")

            time.sleep(1)  # To avoid API rate limits
        except Exception as e:
            print(f"⚠️ Failed to fetch fixtures for {league_id}: {e}")

    if all_fixtures:
        print(f"✅ Total Retrieved {len(all_fixtures)} fixtures.")
    else:
        print("❌ No fixtures found for today or tomorrow.")

    return all_fixtures



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch football data selectively.")
    parser.add_argument("--odds", action="store_true", help="Fetch betting odds")
    parser.add_argument("--fixtures", action="store_true", help="Fetch fixtures")
    parser.add_argument("--leagues", action="store_true", help="Fetch active leagues list (refreshes cache)")

    args = parser.parse_args()

    if args.leagues:
        fetch_active_leagues()
    if args.odds:
        fetch_odds()
    if args.fixtures:
        fetch_fixtures()
