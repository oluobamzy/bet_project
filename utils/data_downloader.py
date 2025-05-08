import urllib.request
import os
import logging
from typing import List

# Confirmed league codes from football-data.co.uk
LEAGUE_CODE_MAP = {
    "EPL": "E0",             # English Premier League
    "LaLiga": "SP1",         # Spanish La Liga
    "SerieA": "I1",          # Italian Serie A
    "Bundesliga": "D1",      # German Bundesliga
    "Ligue1": "F1",          # French Ligue 1
    "PrimeiraLiga": "P1",    # Portuguese Primeira Liga
    "Eredivisie": "N1",      # Dutch Eredivisie
    "ProLeague": "B1",       # Belgian Pro League
    "SPL": "SC0",            # Scottish Premiership
    "SuperLig": "T1",        # Turkish Süper Lig
    "BundesligaAT": "A1",    # Austrian Bundesliga
    "SuperLeagueCH": "SW1",  # Swiss Super League
    "Superliga": "DK1",      # Danish Superliga
    "Eliteserien": "NW1",    # Norwegian Eliteserien
    "Allsvenskan": "S1",     # Swedish Allsvenskan
    "UPL": "UKR1",           # Ukrainian Premier League
    "SuperLeagueGR": "G1",   # Greek Super League
    "FortunaLiga": "CZ1",    # Czech Fortuna Liga
    "HNL": "HR1",            # Croatian Prva HNL
    "SuperLigaRS": "SRB1",   # Serbian SuperLiga
    "Ekstraklasa": "PL1",    # Polish Ekstraklasa
    "NBI": "HU1",            # Hungarian NB I
    "Liga1": "RO1",          # Romanian Liga I
    "FirstDivisionCY": "CY1",# Cyprus First Division
    "PremierLeagueIL": "ISR1"# Israeli Premier League
}

def download_all_supported_data(seasons: List[str]) -> None:
    """Download match data for all supported leagues across given seasons."""
    os.makedirs("cron/data/historical", exist_ok=True)

    for season in seasons:
        logging.info(f"📅 Downloading season {season}")
        for league_name, league_code in LEAGUE_CODE_MAP.items():
            try:
                url = f"https://www.football-data.co.uk/mmz4281/{season}/{league_code}.csv"
                file_path = f"cron/data/historical/{league_name}_{season}.csv"
                urllib.request.urlretrieve(url, file_path)
                logging.info(f"✅ Downloaded {league_name} ({league_code}) for {season}")
            except Exception as e:
                logging.error(f"❌ Failed {league_name} ({league_code}) for {season}: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    seasons = ["2223", "2324"]  # Add more seasons as needed
    download_all_supported_data(seasons)
