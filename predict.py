# predict.py

import os
import numpy as np
import pandas as pd
import joblib
from fetch_data import fetch_fixture_inputs

# Auto-detect the model file
MODELS_FOLDER = "models"
model_files = [f for f in os.listdir(MODELS_FOLDER) if f.endswith(".pkl")]

if not model_files:
    raise FileNotFoundError("❌ No model file (.pkl) found in models/ folder!")

MODEL_PATH = os.path.join(MODELS_FOLDER, model_files[0])

# Load the model
try:
    with open(MODEL_PATH, "rb") as f:
        model = joblib.load(f)
except Exception as e:
    raise FileNotFoundError(f"❌ Failed to load model: {e}")

# --- Predict upcoming fixtures
def predict_bet(league: str = "EPL") -> str:
    """Predict matches scheduled for TODAY for a given league."""
    fixtures = fetch_fixture_inputs(league_name=league, for_tomorrow=False)

    if not fixtures:
        return "❌ No fixtures found for today."

    results = []
    for fixture in fixtures:
        home = fixture["home"]
        away = fixture["away"]
        features = fixture["features"]

        try:
            input_array = np.array(features).reshape(1, -1)
            pred = model.predict(input_array)[0]
            outcome = ["🏠 Home Win", "🤝 Draw", "🚀 Away Win"][pred]
            results.append(f"**{home} vs {away}: {outcome}**")
        except Exception as e:
            results.append(f"**{home} vs {away}: ❌ Prediction Error ({e})**")

    return "\n".join(results)

def predict_bet_tomorrow(league_name="EPL") -> str:
    """Predict matches scheduled for TOMORROW for a given league."""
    fixtures = fetch_fixture_inputs(league_name=league_name, for_tomorrow=True)

    if not fixtures:
        return "❌ No fixtures found for tomorrow."

    predictions = []
    for fixture in fixtures:
        home = fixture["home"]
        away = fixture["away"]
        features = fixture["features"]

        try:
            input_array = np.array(features).reshape(1, -1)
            pred = model.predict(input_array)[0]
            outcome = ["🏠 Home Win", "🤝 Draw", "🚀 Away Win"][pred]
            predictions.append(f"**{home} vs {away}: {outcome}**")
        except Exception as e:
            predictions.append(f"**{home} vs {away}: ❌ Prediction Error ({e})**")

    return "\n".join(predictions)

def predict_single_match(home_team: str, away_team: str, model_input: list) -> str:
    """Predict a single match given pre-built model input."""
    try:
        input_array = np.array(model_input).reshape(1, -1)
        pred = model.predict(input_array)[0]
        outcome = ["🏠 Home Win", "🤝 Draw", "🚀 Away Win"][pred]
        return f"**{home_team} vs {away_team}: {outcome}**"
    except Exception as e:
        return f"❌ Error predicting {home_team} vs {away_team}: {e}"

# --- Example usage for CLI testing
if __name__ == "__main__":
    print(predict_bet())
