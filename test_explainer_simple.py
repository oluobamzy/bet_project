from utils.explainer import PredictionExplainer

try:
    # Create explainer
    explainer = PredictionExplainer()
    print('SUCCESS: PredictionExplainer was successfully initialized')
    
    # Create a dummy fixture - we don't need the model to work
    fixture = {
        "home": "Test Team A",
        "away": "Test Team B",
        "features": [1.0, 2.0, 3.0, 0.5, 0.5, 0.5],
        "date": "2023-05-10"
    }
    
    # Try to use the explain_match_prediction method
    print('Testing explain_match_prediction method...')
    result = explainer.explain_match_prediction(
        home_team="Test Team A",
        away_team="Test Team B",
        features=[1.0, 2.0, 3.0, 0.5, 0.5, 0.5],
        league_name=""
    )
    
    print(f"Result type: {type(result)}")
    if isinstance(result, dict) and "error" in result:
        print(f"Expected error (no model): {result['error']}")
    else:
        print("No error in result (unexpected)")
        
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
