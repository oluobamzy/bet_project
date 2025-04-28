# utils/fetch_data.py

import requests
import os
from dotenv import load_dotenv
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

load_dotenv()

CACHE_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours

def is_cache_valid(filepath: str) -> bool:
    """Check if a cache file is still valid (not too old)."""
    if not os.path.exists(filepath):
        return False
    file_mtime = os.path.getmtime(filepath)
    return (time.time() - file_mtime) < CACHE_EXPIRY_SECONDS

def fetch_odds(sport: str = "soccer_epl") -> List[Dict]:
    """Fetches live odds with error handling and caching"""
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport}/odds",
            params={
                "api_key": os.getenv("ODDS_API_KEY"),
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            },
            timeout=10
        )
        response.raise_for_status()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "data": response.json()
        }
        os.makedirs("data/live", exist_ok=True)
        with open("data/live/latest_odds.json", "w") as f:
            json.dump(data, f)
            
        print("✅ Live odds fetched successfully.")
        return data["data"]

    except requests.exceptions.RequestException as e:
        print(f"⚠️ API Error fetching odds: {e}")

        # Fallback to cache
        cache_path = "data/live/latest_odds.json"
        if is_cache_valid(cache_path):
            try:
                with open(cache_path, "r") as f:
                    print("♻️ Using cached odds data.")
                    return json.load(f)["data"]
            except (FileNotFoundError, json.JSONDecodeError) as cache_error:
                print(f"⚠️ Cache read error: {cache_error}")

        print("❌ No valid odds data available.")
        return []

def get_fixtures(league_id: int = 39) -> List[Dict]:
    """Fetch fixtures with caching"""
    try:
        response = requests.get(
            "https://api-football-v1.p.rapidapi.com/v3/fixtures",
            headers={
                "x-rapidapi-key": os.getenv("API_FOOTBALL_KEY"),
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
            },
            params={"league": league_id, "season": datetime.now().year},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        os.makedirs("cache", exist_ok=True)
        with open("cache/fixtures.json", "w") as f:
            json.dump(data, f)

        print("✅ Fixtures fetched successfully.")
        return data.get("response", [])

    except requests.exceptions.RequestException as e:
        print(f"⚠️ API Error fetching fixtures: {e}")

        # Fallback to cache
        cache_path = "cache/fixtures.json"
        if is_cache_valid(cache_path):
            try:
                with open(cache_path, "r") as f:
                    print("♻️ Using cached fixtures data.")
                    return json.load(f).get("response", [])
            except (FileNotFoundError, json.JSONDecodeError) as cache_error:
                print(f"⚠️ Cache read error: {cache_error}")

        print("❌ No valid fixtures data available.")
        return []
