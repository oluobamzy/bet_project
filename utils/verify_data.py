# utils/verify_data.py
# is util working
import pandas as pd
import logging
import os
from typing import List, Set
from datetime import datetime
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def validate_dates(df: pd.DataFrame, league: str) -> None:
    """Validate date formats in the DataFrame"""
    try:
        dates = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        if dates.isnull().any():
            logging.warning(f"⚠️ {league}: Invalid date formats detected")
    except Exception as e:
        logging.error(f"❌ {league}: Date validation failed - {str(e)}")
        raise

def validate_scores(df: pd.DataFrame, league: str) -> None:
    """Validate score columns in the DataFrame"""
    if df[['FTHG', 'FTAG']].isnull().any().any():
        logging.warning(f"⚠️ {league}: Contains null/missing scores")

def verify_historical_data(
    leagues: List[str] = CONFIG["leagues"],
    season: str = CONFIG["season"],
    required_cols: Set[str] = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
) -> bool:
    """
    Validates downloaded CSV files against requirements
    
    Args:
        leagues: League codes to verify
        season: Season code in YY-YY format
        required_cols: Mandatory columns to check
        
    Returns:
        bool: True if all files are valid
    """
    all_valid = True
    data_dir = os.path.join("data", "historical")

    for league in leagues:
        file_path = os.path.join(data_dir, f"{league}_{season}.csv")
        try:
            # Check file exists
            if not os.path.exists(file_path):
                logging.error(f"❌ File not found: {file_path}")
                all_valid = False
                continue

            # Load and validate data
            df = pd.read_csv(file_path)
            
            # Column check
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                logging.error(f"❌ {league}: Missing columns {missing_cols}")
                all_valid = False
            else:
                logging.info(f"✅ {league}: Valid structure at {file_path}")

            # Run data quality checks
            validate_dates(df, league)
            validate_scores(df, league)
                
        except Exception as e:
            logging.error(f"❌ {league}: Verification failed - {str(e)}")
            all_valid = False
            
    return all_valid

if __name__ == "__main__":
    try:
        success = verify_historical_data()
        if not success:
            raise ValueError("Data validation failed. Check logs for details.")
        logging.info("🎉 All data validated successfully")
    except Exception as e:
        logging.critical(f"🔴 Critical failure: {str(e)}")
        exit(1)

        