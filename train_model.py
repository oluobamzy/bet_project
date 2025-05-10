# train_model.py
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, classification_report
from sklearn.utils.class_weight import compute_class_weight
import joblib
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Set a minimum required accuracy threshold
MIN_ACCURACY_THRESHOLD = 0.60

# Leagues with sufficient data for specific models
MAJOR_LEAGUES = ["EPL", "LaLiga", "SerieA", "Bundesliga", "Ligue1"]

def train_model(league_name=None):
    """
    Train and save the prediction model.
    If league_name is provided, train a league-specific model.
    If league_name is None, train a general model with all data.
    """
    try:
        if league_name:
            logging.info(f"🚀 Starting model training for {league_name}...")
        else:
            logging.info("🚀 Starting general model training...")

        # Load data
        data_path = Path("utils/cron/data/processed/clean_matches.csv")
        df = pd.read_csv(data_path)
        
        # Filter by league if specified
        if league_name:
            if 'league' not in df.columns:
                logging.warning(f"⚠️ No 'league' column in data, cannot filter for {league_name}")
                return False
                
            df = df[df['league'] == league_name]
            if len(df) < 300:  # Need sufficient data for training
                logging.warning(f"⚠️ Insufficient data for {league_name}: {len(df)} matches only")
                return False
                
            logging.info(f"📊 Using {len(df)} matches for {league_name} model")

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

        # Evaluate with multiple metrics
        preds = model.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        
        # Enhanced evaluation metrics
        precision = precision_score(y_test, preds, average='weighted')
        recall = recall_score(y_test, preds, average='weighted')
        conf_matrix = confusion_matrix(y_test, preds)
        
        # Log detailed evaluation
        logging.info(f"🎯 Model Evaluation Results:")
        logging.info(f"✅ Accuracy: {accuracy:.2%}")
        logging.info(f"📊 Precision: {precision:.2%}")
        logging.info(f"📈 Recall: {recall:.2%}")
        logging.info(f"📉 Confusion Matrix:\n{conf_matrix}")
        logging.info(f"📋 Detailed Classification Report:\n{classification_report(y_test, preds)}")
        
        # Check if accuracy meets threshold requirement
        if accuracy < MIN_ACCURACY_THRESHOLD:
            logging.warning(f"⚠️ Model accuracy ({accuracy:.2%}) is below minimum threshold ({MIN_ACCURACY_THRESHOLD:.2%})")
            logging.warning("⚠️ Consider retraining with different parameters or more data")
            return False
        else:
            logging.info(f"✅ Model meets accuracy threshold: {accuracy:.2%} >= {MIN_ACCURACY_THRESHOLD:.2%}")
            
            # Save model if it meets accuracy requirements
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)
            
            # Save as league-specific model if applicable
            if league_name:
                model_filename = f"xgboost_model_{league_name}.pkl"
                feature_filename = f"feature_list_{league_name}.pkl"
            else:
                model_filename = "xgboost_model.pkl"
                feature_filename = "feature_list.pkl"
                
            joblib.dump(model, model_dir / model_filename)
            
            # Save feature list for consistency checks
            feature_list = {
                "features": features,
                "classes": ["Home Win", "Draw", "Away Win"]
            }
            joblib.dump(feature_list, model_dir / feature_filename)
            
            logging.info(f"💾 Model saved to {model_dir/model_filename}")
            logging.info(f"💾 Feature list saved to {model_dir/feature_filename}")
            return True

    except Exception as e:
        logging.error(f"❌ Training failed: {str(e)}")
        raise
        
def train_all_models():
    """Train both general model and league-specific models."""
    # Train general model first
    general_success = train_model()
    
    # Train league-specific models if possible
    league_results = {}
    for league in MAJOR_LEAGUES:
        try:
            logging.info(f"🏆 Training model for {league}...")
            success = train_model(league)
            league_results[league] = success
        except Exception as e:
            logging.error(f"❌ Failed training for {league}: {str(e)}")
            league_results[league] = False
    
    # Summary
    logging.info("📋 Training Summary:")
    logging.info(f"General model: {'✅ Success' if general_success else '❌ Failed'}")
    for league, success in league_results.items():
        logging.info(f"{league}: {'✅ Success' if success else '❌ Failed'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train football prediction models")
    parser.add_argument("--league", type=str, help="Train model for specific league only")
    parser.add_argument("--all", action="store_true", help="Train models for all major leagues")
    
    args = parser.parse_args()
    
    if args.all:
        train_all_models()
    elif args.league:
        train_model(args.league)
    else:
        train_model()  # Default: train general model
