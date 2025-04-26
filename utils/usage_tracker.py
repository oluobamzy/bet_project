# utils/usage_tracker.py
import json

def track_usage(api_name):
    try:
        with open("data/api_usage.json", "r") as f:
            usage = json.load(f)
    except:
        usage = {}
    
    usage[api_name] = usage.get(api_name, 0) + 1
    
    with open("data/api_usage.json", "w") as f:
        json.dump(usage, f)

# Usage:
track_usage("odds_api")