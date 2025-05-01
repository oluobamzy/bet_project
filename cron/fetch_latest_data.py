# fetch_latest_data.py
# -*- coding: utf-8 -*-

import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path
import time

load_dotenv()

# Create necessary folders
Path("data/live").mkdir(parents=True, exist_ok=True)
Path("cache").mkdir(parents=True, exist_ok=True)

# Mapping of your SUPPORTED_LEAGUES keys to The Odds API sports keys
SPORTS_MAPPING = {
    "EPL": "soccer_epl",
    "LaLiga": "soccer_spain_la_liga",
    "SerieA": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue1": "soccer_france_ligue_one",
    "PrimeiraLiga": "soccer_portugal_primeira_liga",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "ProLeague": "soccer_belgium_first_division_a",
    "SPL": "soccer_scotland_premiership",
    "SuperLig": "soccer_turkey_super_lig",
    "BundesligaAT": "soccer_austria_bundesliga",
    "SuperLeagueCH": "soccer_switzerland_superleague",
    "Superliga": "soccer_denmark_superliga",
    "Eliteserien": "soccer_norway_eliteserien",
    "Allsvenskan": "soccer_sweden_allsvenskan",
    "UPL": "soccer_ukraine_premier_league",
    "SuperLeagueGR": "soccer_greece_super_league",
    "FortunaLiga": "soccer_czech_republic_first_league",
    "HNL": "soccer_croatia_1_hnl",
    "SuperLigaRS": "soccer_serbia_super_liga",
    "Ekstraklasa": "soccer_poland_ekstraklasa",
    "NBI": "soccer_hungary_nb_i",
    "Liga1": "soccer_romania_liga_1",
    "FirstDivisionCY": "soccer_cyprus_1st_division",
    "PremierLeagueIL": "soccer_israel_ligat_haal",
}

def retry_request(url, headers=None, params=None, retries=3, delay=2):
    """Retry logic for flaky APIs"""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise Exception(f"❌ All {retries} attempts failed for {url}")

def fetch_active_leagues() -> set:
    """Fetch currently active league IDs from API-Football."""
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        raise ValueError("❌ Missing API_FOOTBALL_KEY in .env")

    try:
        print("Fetching active leagues...")
        response = retry_request(
            "https://api-football-v1.p.rapidapi.com/v3/leagues",
            headers={
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
            }
        )
        leagues = response.json().get("response", [])
        active_leagues = set()

        for league_info in leagues:
            season_info = league_info.get("seasons", [])
            for season in season_info:
                if season.get("year") == datetime.now().year and season.get("coverage", {}).get("fixtures", {}).get("events", False):
                    active_leagues.add(league_info["league"]["id"])

        print(f"✅ Found {len(active_leagues)} active leagues.")
        return active_leagues

    except Exception as e:
        print(f"⚠️ Error fetching active leagues: {e}")
        return set()

def fetch_odds() -> None:
    """Fetch and save odds for all supported leagues."""
    odds_api_key = os.getenv("ODDS_API_KEY")
    if not odds_api_key:
        raise ValueError("❌ Missing ODDS_API_KEY in .env")

    cache_path = Path("data/live/latest_odds.json")
    fresh = False

    # Check if cache exists and is fresh
    if cache_path.exists():
        with open(cache_path, "r") as f:
            cached = json.load(f)
            timestamp = datetime.fromisoformat(cached.get("timestamp", datetime.min.isoformat()))
            if datetime.now() - timestamp < timedelta(hours=12):
                print("🛡️ Using fresh cached odds.")
                fresh = True
            else:
                print("🔄 Cached odds expired (>12h), fetching new odds...")
    else:
        print("🔎 No cached odds found, fetching new odds...")

    if fresh:
        return

    all_odds = {}

    for league_code, sport_key in SPORTS_MAPPING.items():
        try:
            print(f"Fetching odds for: {league_code} ({sport_key})")
            response = retry_request(
                f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
                params={
                    "api_key": odds_api_key,
                    "regions": "eu",
                    "markets": "h2h",
                    "oddsFormat": "decimal"
                }
            )
            if response.status_code == 200:
                all_odds[league_code] = response.json()
            elif response.status_code == 404:
                print(f"⚠️ No odds available for {league_code} (skipping)")
            else:
                print(f"⚠️ Failed to fetch odds for {league_code}: {response.status_code} {response.text}")

            time.sleep(1)  # avoid rate limits

        except Exception as e:
            print(f"⚠️ Error fetching {league_code}: {e}")

    if all_odds:
        timestamp = datetime.now().isoformat()
        with open("data/live/latest_odds.json", "w") as f:
            json.dump({"timestamp": timestamp, "data": all_odds}, f, indent=2)
        print("✅ All odds saved to data/live/latest_odds.json")
    else:
        print("⚠️ No odds data fetched. (Check API keys?)")

def fetch_fixtures(league_id: int = 39) -> None:
    """Fetch and save fixtures only for active leagues."""
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        raise ValueError("❌ Missing API_FOOTBALL_KEY in .env")

    active_leagues = fetch_active_leagues()
    if league_id not in active_leagues:
        print(f"⚠️ League ID {league_id} is not active currently. Skipping fixtures fetch.")
        return

    try:
        print(f"Fetching fixtures for league ID {league_id}...")
        response = retry_request(
            "https://api-football-v1.p.rapidapi.com/v3/fixtures",
            headers={
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
            },
            params={"league": league_id, "season": datetime.now().year}
        )
        with open("cache/fixtures.json", "w") as f:
            json.dump(response.json(), f, indent=2)
        print("✅ Fixtures saved to cache/fixtures.json")

    except Exception as e:
        print(f"⚠️ Error fetching fixtures: {e}")
        if Path("cache/fixtures.json").exists():
            print("ℹ️ Using cached fixtures.")

if __name__ == "__main__":
    fetch_odds()
    fetch_fixtures()
