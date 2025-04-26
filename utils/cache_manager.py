# utils/cache_manager.py
import time

class APIManager:
    def __init__(self, calls_per_minute: int):
        self.last_call: float = 0
        self.delay: float = 60 / calls_per_minute
        
    def throttle(self) -> None:
        """Enforce rate limiting by sleeping if needed"""
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_call = time.time()


# utils/api_fetcher.py
import requests
import os
import json
from datetime import datetime
from typing import Dict, List
from .cache_manager import APIManager  # Relative import

# Initialize rate limiter instance
odds_api_manager = APIManager(calls_per_minute=10)  # OddsAPI free tier limit

def fetch_odds(sport: str = "soccer_epl") -> List[Dict]:
    """Fetch live odds with rate limiting and caching"""
    try:
        # Enforce rate limit
        odds_api_manager.throttle()
        
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
        
        # Cache response
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
        # Fallback to cache
        try:
            with open("data/live/latest_odds.json", "r") as f:
                return json.load(f)["data"]
        except (FileNotFoundError, json.JSONDecodeError):
            return []