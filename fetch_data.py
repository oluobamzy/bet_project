import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from cron.fetch_latest_data import fetch_fixtures, fetch_odds


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


def fetch_fixture_inputs(league_name: str = "EPL", for_tomorrow: bool = False) -> List[Dict]:
    fixtures = fetch_fixtures()
    inputs = []
    now = pd.Timestamp.now()

    # Determine tomorrow's date for filtering
    tomorrow = now + timedelta(days=1)
    tomorrow_date = tomorrow.date()

    for fx in fixtures:
        try:
            home = fx['teams']['home']['name']
            away = fx['teams']['away']['name']
            match_datetime = pd.to_datetime(fx['fixture']['date'])
            match_date = match_datetime.date()

            # Unified date filtering logic
            target_date = tomorrow_date if for_tomorrow else now.date()
            if match_date != target_date:
                continue

            # Compute relevant stats
            home_form = get_form(home, match_datetime)
            away_form = get_form(away, match_datetime)
            h2h = get_h2h_rate(home, away, match_datetime)
            odds = get_live_odds(home, away) or {}

            # Construct features
            features = [
                odds.get("home_odds", 2.0),
                odds.get("away_odds", 2.0),
                odds.get("draw_odds", 3.0),
                home_form or 0.5,
                away_form or 0.5,
                h2h or 0.5
            ]

            inputs.append({
                "home": home,
                "away": away,
                "date": str(match_date),
                "features": features
            })
        except Exception as e:
            print(f"⚠️ Skipped fixture {fx.get('fixture', {}).get('id')}: {e}")

    return inputs

