
# ⚽ Football Prediction Bot

A Discord bot that provides daily football match predictions using an XGBoost machine learning model. This bot supports multiple football leagues and can deliver predictions for both today's and tomorrow's matches.

## 🚀 Features

- ✅ Provides match predictions using an XGBoost model.
- 📅 Supports predictions for today's and tomorrow's matches.
- 🌍 Supports multiple leagues (EPL, LaLiga, Serie A, Bundesliga, Ligue 1, and more).
- ⏰ Automated daily prediction messages in subscribed channels.
- 📩 Users can manually request predictions for any supported league.
- 🔔 Subscription system for daily predictions.
- 🌐 Slash commands for a seamless user experience.

## 📌 Supported Leagues
- English Premier League (EPL)
- Spanish La Liga (LaLiga)
- Italian Serie A (SerieA)
- German Bundesliga (Bundesliga)
- French Ligue 1 (Ligue1)
- ... and many more.

## 📌 Project Structure
```
.
├── bot.py               # Main bot file (Discord interactions)
├── predict.py           # Prediction logic using XGBoost model
├── fetch_data.py        # Fetching fixtures and features for prediction
├── models/              # Folder containing the trained XGBoost model
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation (this file)
```

## 📖 How It Works
1. The bot fetches football fixtures from the API.
2. The features of these fixtures are prepared for the model.
3. The XGBoost model makes predictions on the fixture outcomes (Home Win, Draw, Away Win).
4. Predictions are sent to the Discord server via the bot.

## 📋 User Stories
- **As a user**, I want to request predictions for a specific league, so I can know the outcomes of matches.
- **As a user**, I want to receive daily predictions automatically, so I stay updated without requesting manually.
- **As an admin**, I want to control the list of supported leagues, so I can ensure accurate predictions.
- **As a user**, I want to subscribe or unsubscribe from daily predictions.

## 🚀 Setup Guide

### Prerequisites
- Python 3.8 or above.
- A trained XGBoost model saved as `.pkl` in the `models/` directory.
- A Discord bot token (You can create one at [Discord Developer Portal](https://discord.com/developers/applications)).

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/football-prediction-bot.git
cd football-prediction-bot

# Install dependencies
pip install -r requirements.txt

# Create a .env file with your Discord bot token
echo "DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN" > .env

# Ensure you have your trained XGBoost model in the models/ directory

# Run the bot
python bot.py
```

## 🔧 Usage
- Use `/bet [league]` to get predictions for today's matches in the specified league.
- Use `/bet_tomorrow [league]` to get predictions for tomorrow's matches.
- Use `/leagues` to see all supported leagues.
- Use `/subscribe` to subscribe to daily predictions.
- Use `/unsubscribe` to unsubscribe.

## 🛠️ Known Issues
- The bot currently does not generate predictions because the XGBoost model is not properly integrated. Ensure your model file is compatible.
- Model feature generation (fetch_data.py) must match the model's expected input format.

## 📌 Roadmap
- [ ] Properly integrate the XGBoost model with accurate feature preparation.
- [ ] Add more leagues based on user requests.
- [ ] Allow server admins to customize subscribed channels.
- [ ] Implement a persistent database for subscribed users.

## 👨‍💻 Contributing
Contributions are welcome! Please create an issue before submitting a pull request.

## 📜 License
This project is licensed under the MIT License.

## 📞 Support
For help, please create an issue on the GitHub repository.
