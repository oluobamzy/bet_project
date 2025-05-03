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
            "https://api-football-v1.p.rapidapi.com/v3/leagues",
            headers={
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
            }
        )
        leagues = response.json().get("response", [])
        active_leagues = set()

        for league_info in leagues:
            for season in league_info.get("seasons", []):
                if season.get("year") == datetime.now().year and season.get("coverage", {}).get("fixtures", {}).get("events", False):
                    active_leagues.add(league_info["league"]["id"])

        print(f"✅ Found {len(active_leagues)} active leagues.")
        cache_active_leagues(active_leagues, cache_path=cache_path)
        return active_leagues

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
        return []

    for league_id in active_leagues:
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
            with open(f"cache/fixtures_{league_id}.json", "w") as f:
                json.dump(response.json(), f, indent=2)
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Failed to fetch fixtures for {league_id}: {e}")

    # ✅ Return all fixtures from saved files
    all_fixtures = []
    for league_id in active_leagues:
        cache_path = f"cache/fixtures_{league_id}.json"
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                league_data = json.load(f)
                all_fixtures.extend(league_data.get("response", []))

    return all_fixtures


if __name__ == "__main__":
    fetch_odds()
    fetch_fixtures()
