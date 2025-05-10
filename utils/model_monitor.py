import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from sklearn.metrics import accuracy_score
import subprocess
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

MIN_ACCURACY_THRESHOLD = 0.60

def evaluate_model_performance():
    """
    Evaluate model performance on recent data to detect accuracy drift.
    Returns True if model needs retraining, False otherwise.
    """
    try:
        logging.info("🔍 Evaluating model performance on recent data...")
        
        # Load model
        model_path = Path("models/xgboost_model.pkl")
        if not model_path.exists():
            logging.error("❌ Model file not found!")
            return True  # Need to train if model doesn't exist
            
        model = joblib.load(model_path)
        
        # Load recent clean match data
        data_path = Path("utils/cron/data/processed/clean_matches.csv")
        df = pd.read_csv(data_path)
        
        # Get the most recent 20% of matches for evaluation
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False)
        recent_matches = df.head(int(len(df) * 0.2))
        
        if recent_matches.empty:
            logging.warning("⚠️ No recent matches found for evaluation")
            return False
            
        # Get feature list
        feature_list_path = Path("models/feature_list.pkl")
        if feature_list_path.exists():
            feature_data = joblib.load(feature_list_path)
            features = feature_data.get("features")
        else:
            features = [
                'home_odds', 'away_odds', 'draw_odds',
                'home_form', 'away_form', 'h2h_win_rate'
            ]
            
        # Prepare features and target
        X_recent = recent_matches[features]
        y_recent = recent_matches['FTR'].map({'H': 0, 'D': 1, 'A': 2})
        
        # Evaluate
        preds = model.predict(X_recent)
        accuracy = accuracy_score(y_recent, preds)
        
        logging.info(f"📊 Current model accuracy on recent data: {accuracy:.2%}")
        logging.info(f"📊 Minimum accuracy threshold: {MIN_ACCURACY_THRESHOLD:.2%}")
        
        # Check if accuracy falls below threshold
        if accuracy < MIN_ACCURACY_THRESHOLD:
            logging.warning(f"⚠️ Model accuracy ({accuracy:.2%}) has fallen below threshold ({MIN_ACCURACY_THRESHOLD:.2%})")
            return True
        else:
            logging.info(f"✅ Model accuracy ({accuracy:.2%}) is above threshold ({MIN_ACCURACY_THRESHOLD:.2%})")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error evaluating model performance: {e}")
        return False  # Default to not retraining on error
        
def trigger_retraining():
    """
    Trigger model retraining if needed.
    """
    try:
        if evaluate_model_performance():
            logging.info("🔄 Triggering model retraining...")
            
            # Get the path to the Python interpreter that's currently running
            python_executable = sys.executable
            
            # Run the train_model.py script as a subprocess
            subprocess.run([python_executable, "train_model.py"], check=True)
            logging.info("✅ Model retraining completed successfully")
            return True
        else:
            logging.info("✅ Model performance is satisfactory, no retraining needed")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error during retraining: {e}")
        return False
        
if __name__ == "__main__":
    trigger_retraining()
