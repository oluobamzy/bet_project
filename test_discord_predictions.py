# test_discord_predictions.py
#
# This script tests the Discord formatting for predictions
# to verify that the bot will display predictions correctly

from predict import predict_bet, predict_bet_tomorrow, format_predictions_for_discord

# Test today's predictions
print("\n--- TODAY'S EPL PREDICTIONS ---")
today_predictions = predict_bet("EPL")
if isinstance(today_predictions, str):
    print("Error:", today_predictions)
else:
    print(f"Found {len(today_predictions)} predictions for today")
    formatted_today = format_predictions_for_discord(today_predictions, is_tomorrow=False)
    print("\nFormatted message for Discord:")
    print("-" * 50)
    print(formatted_today)
    print("-" * 50)

# Test tomorrow's predictions
print("\n--- TOMORROW'S EPL PREDICTIONS ---")
tomorrow_predictions = predict_bet_tomorrow("EPL")
if isinstance(tomorrow_predictions, str):
    print("Error:", tomorrow_predictions)
else:
    print(f"Found {len(tomorrow_predictions)} predictions for tomorrow")
    formatted_tomorrow = format_predictions_for_discord(tomorrow_predictions, is_tomorrow=True)
    print("\nFormatted message for Discord:")
    print("-" * 50)
    print(formatted_tomorrow)
    print("-" * 50)
