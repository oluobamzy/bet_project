import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from utils.cron.fetch_latest_data import retry_request, fetch_active_leagues

def debug_epl_fixtures():
    """Fetch EPL fixtures directly and save them for debugging."""
    
    print("🔍 Debugging EPL fixtures fetch...")
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        print("❌ Missing API_FOOTBALL_KEY in .env")
        return
        
    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    tomorrow = (now_utc + timedelta(days=1)).date()
    
    print(f"📅 Date Range: {today} to {tomorrow}")
    
    league_id = 39  # EPL
    try:
        # Check if EPL is in active leagues
        active_leagues = fetch_active_leagues()
        if league_id in active_leagues:
            print("✅ EPL is in active leagues list")
        else:
            print("⚠️ EPL is NOT in active leagues list!")
            
        # Manually fetch season info for EPL
        print("📡 Fetching season info for EPL...")
        season_response = retry_request(
            "https://v3.football.api-sports.io/leagues",
            headers={"x-apisports-key": api_key},
            params={"id": league_id}
        )
        season_data = season_response.json()
        
        # Save the response for inspection
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        with open(debug_dir / "epl_seasons.json", "w") as f:
            json.dump(season_data, f, indent=2)
            
        # Extract latest season
        if not season_data.get("response"):
            print("❌ No season data returned for EPL!")
            return
            
        latest_season = max(
            season["seasons"][-1]["year"] 
            for season in season_data["response"] 
            if season["seasons"]
        )
        print(f"📊 Latest EPL season: {latest_season}")
        
        # Fetch fixtures for EPL
        print("📡 Fetching EPL fixtures...")
        fixture_response = retry_request(
            "https://v3.football.api-sports.io/fixtures",
            headers={"x-apisports-key": api_key},
            params={
                "league": league_id,
                "season": latest_season,
                "from": today.isoformat(),
                "to": tomorrow.isoformat()
            }
        )
        fixture_data = fixture_response.json()
        
        # Save the fixtures for inspection
        with open(debug_dir / "epl_fixtures.json", "w") as f:
            json.dump(fixture_data, f, indent=2)
            
        # Also save to regular cache locations
        with open(f"cache/fixtures_{league_id}.json", "w") as f:
            json.dump(fixture_data, f, indent=2)
            
        with open(f"utils/cron/cache/fixtures_{league_id}.json", "w") as f:
            json.dump(fixture_data, f, indent=2)
        
        # Report on fixtures
        fixtures = fixture_data.get("response", [])
        print(f"✅ Found {len(fixtures)} EPL fixtures")
        if fixtures:
            for fixture in fixtures:
                match_time = datetime.fromtimestamp(fixture["fixture"]["timestamp"], tz=timezone.utc)
                print(f"  ⚽ {match_time.strftime('%Y-%m-%d %H:%M')} UTC: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
        else:
            print("❌ No fixtures found for EPL in this date range!")
            
    except Exception as e:
        print(f"❌ Error while debugging EPL fixtures: {e}")

if __name__ == "__main__":
    debug_epl_fixtures()
