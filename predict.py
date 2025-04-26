# predict.py

import pickle
import numpy as np
from fetch_data import fetch_fixture_inputs
import pandas as pd

# --- Load trained model
MODEL_PATH = "models/model.pkl"

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
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
