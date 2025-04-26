# fetch_data.py

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from utils.api_fetcher import get_fixtures, fetch_odds

# --- Load historical match data
DATA_PATH = Path("data/processed/clean_matches.csv")

try:
    df_matches = pd.read_csv(DATA_PATH, parse_dates=["date"])
except Exception as e:
    raise FileNotFoundError(f"❌ Failed to load match data: {e}")

# --- Helper Functions

def get_form(team_name: str, match_date: pd.Timestamp, window: int = 5) -> float:
    """Calculate win rate form for a team over last `window` matches before `match_date`."""
    recent_matches = df_matches[
        ((df_matches["home_team"] == team_name) | (df_matches["away_team"] == team_name)) &
        (df_matches["date"] < match_date)
    ].sort_values("date", ascending=False).head(window)

    if recent_matches.empty:
        return 0.5  # fallback neutral value

    wins = 0
    for _, row in recent_matches.iterrows():
        if row["home_team"] == team_name and row["FTR"] == "H":
            wins += 1
        elif row["away_team"] == team_name and row["FTR"] == "A":
            wins += 1

    return wins / len(recent_matches)


def get_h2h_rate(home_team: str, away_team: str, match_date: pd.Timestamp, window: int = 5) -> float:
    """Calculate head-to-head win rate of `home_team` against `away_team`."""
    h2h_matches = df_matches[
        (df_matches["h2h_key"] == str(frozenset([home_team, away_team]))) &
        (df_matches["date"] < match_date)
    ].sort_values("date", ascending=False).head(window)

    if h2h_matches.empty:
        return 0.5  # fallback neutral value

    home_wins = 0
    for _, row in h2h_matches.iterrows():
        if row["home_team"] == home_team and row["FTR"] == "H":
            home_wins += 1
        elif row["away_team"] == home_team and row["FTR"] == "A":
            home_wins += 1

    return home_wins / len(h2h_matches)


def get_historical_odds(home_team: str, away_team: str, match_date: pd.Timestamp) -> Optional[Dict[str, float]]:
    """Get historical odds from dataset."""
    match = df_matches[
        (df_matches["home_team"] == home_team) &
        (df_matches["away_team"] == away_team) &
        (df_matches["date"] == match_date)
    ]

    if match.empty:
        return None

    row = match.iloc[0]
    return {
        "home_odds": row.get("home_odds", 2.0),
        "draw_odds": row.get("draw_odds", 3.0),
        "away_odds": row.get("away_odds", 2.0),
    }


def get_live_odds(home_team: str, away_team: str) -> Dict[str, float]:
    """Fetch live odds if available."""
    odds_data = fetch_odds()
    match = next(
        (event for event in odds_data if home_team in event.get('home_team', '') and away_team in event.get('away_team', '')),
        None
    )
    if match and match.get("bookmakers"):
        h2h = match["bookmakers"][0]["markets"][0]["outcomes"]
        home_odds = next((o["price"] for o in h2h if o["name"] == home_team), 2.5)
        draw_odds = next((o["price"] for o in h2h if o["name"].lower() == "draw"), 3.2)
        away_odds = next((o["price"] for o in h2h if o["name"] == away_team), 2.8)
    else:
        home_odds, draw_odds, away_odds = 2.5, 3.2, 2.8  # fallback defaults

    return {
        "home_odds": home_odds,
        "draw_odds": draw_odds,
        "away_odds": away_odds,
    }


# --- MAIN function to build input features
def fetch_fixture_inputs(league_name: str = "EPL") -> List[Dict]:
    """Build model-ready inputs for upcoming fixtures."""
    fixtures = get_fixtures()
    inputs = []

    for fx in fixtures:
        try:
            home = fx["teams"]["home"]["name"]
            away = fx["teams"]["away"]["name"]
            match_date_str = fx["fixture"]["date"]
            match_date = pd.to_datetime(match_date_str)

            # Features
            home_form = get_form(home, match_date)
            away_form = get_form(away, match_date)
            h2h_rate = get_h2h_rate(home, away, match_date)

            # Prefer live odds if possible
            odds = get_live_odds(home, away)

            features = [
                odds["home_odds"],
                odds["away_odds"],
                odds["draw_odds"],
                home_form,
                away_form,
                h2h_rate,
            ]

            inputs.append({
                "home": home,
                "away": away,
                "date": match_date_str,
                "features": features
            })
        except Exception as e:
            print(f"⚠️ Skipped fixture {fx.get('fixture', {}).get('id', 'unknown')}: {e}")

    return inputs
