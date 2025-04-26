# utils/train_model.py
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import logging
from pathlib import Path
from config import CONFIG  # Your config file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def train_model():
    """Train and save the prediction model"""
    try:
        logging.info("🚀 Starting model training...")
        
        # 1. Load processed data
        data_path = Path("data/processed/clean_matches.csv")
        df = pd.read_csv(data_path)
        
        # 2. Feature Engineering
        features = [
            'home_odds', 'away_odds', 'draw_odds',
            'home_form', 'away_form', 'h2h_win_rate'
        ]
        target = 'FTR'  # Column with H/D/A outcomes
        
        X = df[features]
        y = df[target].map({'H': 0, 'D': 1, 'A': 2})  # Encode outcomes

        # 3. Train/Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 4. Train XGBoost Model
        model = XGBClassifier(
            objective='multi:softprob',
            num_class=3,
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            early_stopping_rounds=10
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=True
        )

        # 5. Evaluate
        preds = model.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        logging.info(f"✅ Model trained with accuracy: {accuracy:.2%}")

        # 6. Save Model
        model_dir = Path("models")
        model_dir.mkdir(exist_ok=True)
        joblib.dump(model, model_dir / "xgboost_model.pkl")
        logging.info(f"💾 Model saved to {model_dir/'xgboost_model.pkl'}")

    except Exception as e:
        logging.error(f"❌ Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    train_model()