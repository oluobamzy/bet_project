# utils/data_cleaner.py
import pandas as pd
import os
import numpy as np
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def calculate_h2h(df: pd.DataFrame) -> Dict[frozenset, float]:
    """Calculate head-to-head win rates for all team pairs."""
    h2h = {}
    team_pairs = {
        frozenset([home, away]) 
        for home, away in zip(df['home_team'], df['away_team'])
    }

    for pair in team_pairs:
        home, away = tuple(pair)
        matches = df[
            ((df['home_team'] == home) & (df['away_team'] == away)) |
            ((df['home_team'] == away) & (df['away_team'] == home))
        ]
        
        if len(matches) > 0:
            home_matches = matches[matches['home_team'] == home]
            win_rate = (home_matches['home_goals'] > home_matches['away_goals']).mean()
            h2h[pair] = 0.5 if np.isnan(win_rate) else win_rate
        else:
            h2h[pair] = 0.5
            
    return h2h

def process_historical() -> None:
    """Process all historical match data into cleaned training data."""
    try:
        start_time = datetime.now()
        dfs = []
        data_dir = Path("data/historical")
        processed_dir = Path("data/processed")
        
        # 1. Verify and load data
        if not data_dir.exists():
            raise FileNotFoundError(f"Directory not found: {data_dir}")
            
        csv_files = list(data_dir.glob("*.csv"))
        if not csv_files:
            raise ValueError(f"No CSV files found in {data_dir}")

        for file in csv_files:
            try:
                df = pd.read_csv(file)
                
                # Standardize columns
                column_map = {
                    "FTHG": "home_goals", "FTAG": "away_goals",
                    "HS": "home_shots", "AS": "away_shots",
                    "B365H": "home_odds", "B365D": "draw_odds", "B365A": "away_odds",
                    "Date": "date", "HomeTeam": "home_team", "AwayTeam": "away_team"
                }
                df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
                dfs.append(df)
                
            except Exception as e:
                logging.warning(f"⚠️ Error processing {file.name}: {str(e)}")
                continue

        if not dfs:
            raise ValueError("No valid data found after processing files")

        # 2. Combine and clean
        combined = pd.concat(dfs, ignore_index=True)
        combined['date'] = pd.to_datetime(combined['date'], dayfirst=True, errors='coerce')
        combined = combined.dropna(subset=['date'])

        # 3. Feature engineering
        logging.info("Calculating features...")
        for team_type in ['home', 'away']:
            combined = combined.sort_values([f'{team_type}_team', 'date'])
            combined[f'{team_type}_form'] = (
                combined.groupby(f'{team_type}_team')[f'{team_type}_goals']
                .rolling(5, min_periods=1).mean()
                .reset_index(level=0, drop=True)
            )

        h2h_rates = calculate_h2h(combined)
        combined['h2h_key'] = [
            frozenset([h, a]) for h, a in zip(combined['home_team'], combined['away_team'])
        ]
        combined['h2h_win_rate'] = combined['h2h_key'].map(h2h_rates)

        # 4. Save processed data
        processed_dir.mkdir(parents=True, exist_ok=True)
        combined.to_csv(processed_dir/"clean_matches.csv", index=False)
        
        duration = (datetime.now() - start_time).total_seconds()
        logging.info(f"✅ Processed {len(combined)} matches in {duration:.2f}s")

    except Exception as e:
        logging.error(f"❌ Processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    process_historical()