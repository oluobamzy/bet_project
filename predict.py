# predict.py

import pickle
import numpy as np
from fetch_data import fetch_fixture_inputs
import pandas as pd
import os
import joblib
# Auto-detect the model file
MODELS_FOLDER = "models"

model_files = [f for f in os.listdir(MODELS_FOLDER) if f.endswith(".pkl")]

if not model_files:
    raise FileNotFoundError("❌ No model file (.pkl) found in models/ folder!")

# You could pick the first one or apply sorting if you have many
MODEL_PATH = os.path.join(MODELS_FOLDER, model_files[0])

# Now load the model
try:
    with open(MODEL_PATH, "rb") as f:
        model = joblib.load(f)
except Exception as e:
    raise FileNotFoundError(f"❌ Failed to load model: {e}")

# --- Predict upcoming fixtures
def predict_bet(league: str = "EPL") -> str:
    """Make predictions for upcoming fixtures in the given league."""
    fixtures = fetch_fixture_inputs(league)

    if not fixtures:
        return "❌ No fixtures found."

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

# --- Optionally, manual prediction for a custom match
def predict_bet_tomorrow(league_name="EPL"):
    inputs = fetch_fixture_inputs(league_name=league_name, for_tomorrow=True)
    if not inputs:
        return "No fixtures for tomorrow!"

    predictions = []
    for fixture in inputs:
        features = np.array(fixture['features']).reshape(1, -1)
        pred = model.predict(features)
        pred_label = pred[0]

        outcome = "Home Win" if pred_label == 0 else "Draw" if pred_label == 1 else "Away Win"
        predictions.append(f"{fixture['home']} vs {fixture['away']}: {outcome}")

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
