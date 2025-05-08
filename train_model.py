# train_model.py
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.utils.class_weight import compute_class_weight
import joblib
from utils.data_cleaner import process_historical
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def train_model():
    """Train and save the prediction model"""
    try:
        logging.info("🚀 Starting model training...")

        # Load data
        data_path = Path("utils/cron/data/processed/clean_matches.csv")
        df = pd.read_csv(data_path)

        # Define features and target
        features = [
            'home_odds', 'away_odds', 'draw_odds',
            'home_form', 'away_form', 'h2h_win_rate'
        ]
        target = 'FTR'

        expected_cols = set(features + [target])
        if not expected_cols.issubset(df.columns):
            missing = expected_cols - set(df.columns)
            raise ValueError(f"Missing columns in data: {missing}")

        X = df[features]
        y = df[target].map({'H': 0, 'D': 1, 'A': 2})

        # Compute class weights
        classes = np.unique(y)
        weights = compute_class_weight(class_weight="balanced", classes=classes, y=y)
        class_weights = {cls: w for cls, w in zip(classes, weights)}
        logging.info(f"⚖️ Class weights applied: {class_weights}")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train model
        model = XGBClassifier(
            objective='multi:softprob',
            num_class=3,
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            early_stopping_rounds=10,
            scale_pos_weight=1  # Not used for multi-class, safe default
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            sample_weight=[class_weights[cls] for cls in y_train],
            verbose=True
        )

        # Evaluate
        preds = model.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        logging.info(f"✅ Model trained with accuracy: {accuracy:.2%}")

        # Save model
        model_dir = Path("models")
        model_dir.mkdir(exist_ok=True)
        joblib.dump(model, model_dir / "xgboost_model.pkl")
        logging.info(f"💾 Model saved to {model_dir/'xgboost_model.pkl'}")

    except Exception as e:
        logging.error(f"❌ Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    train_model()
