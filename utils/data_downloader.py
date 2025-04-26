import urllib.request
import os
from typing import List
import logging

def download_historical_data(leagues: List[str], season: str) -> None:
    """Modular downloader that can be called from anywhere"""
    base_url = f"https://www.football-data.co.uk/mmz4281/{season}"
    os.makedirs("data/historical", exist_ok=True)

    for league in leagues:
        try:
            urllib.request.urlretrieve(
                f"{base_url}/{league}.csv",
                f"data/historical/{league}_{season}.csv"
            )
            logging.info(f"Downloaded {league}_{season}.csv")
        except Exception as e:
            logging.error(f"Failed {league}: {str(e)}")

# Example standalone usage
if __name__ == "__main__":
    download_historical_data(leagues=["E0", "E1"], season="2324")