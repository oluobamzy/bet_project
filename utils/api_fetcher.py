import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, List, Optional

load_dotenv()

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
            }
        )
        response.raise_for_status()
        
        # Save to cache
        data = {
            "timestamp": datetime.now().isoformat(),
            "data": response.json()
        }
        os.makedirs("data/live", exist_ok=True)
        with open("data/live/latest_odds.json", "w") as f:
            json.dump(data, f)
            
        return data["data"]
    except requests.exceptions.RequestException as e:
        print(f"⚠️ API Error: {e}")
        # Fallback to cached data if available
        try:
            with open("data/live/latest_odds.json", "r") as f:
                return json.load(f)["data"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ Cache Error: {e}")
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
            params={"league": league_id, "season": datetime.now().year}
        )
        response.raise_for_status()
        
        # Cache response
        os.makedirs("cache", exist_ok=True)
        with open("cache/fixtures.json", "w") as f:
            json.dump(response.json(), f)
        return response.json().get("response", [])
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Fixtures API Error: {e}")
        try:
            with open("cache/fixtures.json", "r") as f:
                return json.load(f).get("response", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ Fixtures Cache Error: {e}")
            return []