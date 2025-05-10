import os
import asyncio
import discord
import json
import logging
import pandas as pd
from discord.ext import commands
from dotenv import load_dotenv
from discord import app_commands
from predict import predict_bet, predict_bet_tomorrow, format_predictions_for_discord
from utils.prediction_tracker import PredictionTracker
from utils.explainer import PredictionExplainer
from utils.model_monitor import trigger_retraining
import schedule
from datetime import datetime, time
from pathlib import Path
import io

# --- Set up logging
LOG_PATH = Path("logs")
LOG_PATH.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH / "bot.log"),
        logging.StreamHandler()
    ]
)

# --- Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logging.error("❌ Discord token not found in .env file")
    raise ValueError("Discord token not found in .env file")

# --- Initialize prediction services
prediction_tracker = PredictionTracker()
prediction_explainer = PredictionExplainer()

# --- Supported leagues
SUPPORTED_LEAGUES = {
    "EPL": "English Premier League",
    "LaLiga": "Spanish La Liga",
    "SerieA": "Italian Serie A",
    "Bundesliga": "German Bundesliga",
    "Ligue1": "French Ligue 1",
    "PrimeiraLiga": "Portuguese Primeira Liga",
    "Eredivisie": "Dutch Eredivisie",
    "ProLeague": "Belgian Pro League",
    "SPL": "Scottish Premiership",
    "SuperLig": "Turkish Süper Lig",
    "BundesligaAT": "Austrian Bundesliga",
    "SuperLeagueCH": "Swiss Super League",
    "Superliga": "Danish Superliga",
    "Eliteserien": "Norwegian Eliteserien",
    "Allsvenskan": "Swedish Allsvenskan",
    "UPL": "Ukrainian Premier League",
    "SuperLeagueGR": "Greek Super League",
    "FortunaLiga": "Czech Fortuna Liga",
    "HNL": "Croatian Prva HNL",
    "SuperLigaRS": "Serbian SuperLiga",
    "Ekstraklasa": "Polish Ekstraklasa",
    "NBI": "Hungarian NB I",
    "Liga1": "Romanian Liga I",
    "FirstDivisionCY": "Cyprus First Division",
    "PremierLeagueIL": "Israeli Premier League"
}

# --- Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load subscribed users from JSON file
SUBSCRIPTION_FILE = Path("data/subscriptions.json")
CHANNELS_FILE = Path("data/channels.json")

try:
    if SUBSCRIPTION_FILE.exists():
        with open(SUBSCRIPTION_FILE, "r") as f:
            data = json.load(f)
            subscribed_users = data.get("subscribed_users", [])
    else:
        # Create directory if it doesn't exist
        SUBSCRIPTION_FILE.parent.mkdir(exist_ok=True)
        subscribed_users = []
        with open(SUBSCRIPTION_FILE, "w") as f:
            json.dump({"subscribed_users": subscribed_users}, f)
except Exception as e:
    logging.error(f"❌ Error loading subscriptions: {e}")
    subscribed_users = []

# Load channel configuration
try:
    if CHANNELS_FILE.exists():
        with open(CHANNELS_FILE, "r") as f:
            channels_data = json.load(f)
            guild_channels = channels_data.get("subscription_channels", {})
    else:
        guild_channels = {}
        with open(CHANNELS_FILE, "w") as f:
            json.dump({"subscription_channels": guild_channels}, f)
except Exception as e:
    logging.error(f"❌ Error loading channel configuration: {e}")
    guild_channels = {}

# Function to save subscribed users
def save_subscribed_users():
    try:
        with open(SUBSCRIPTION_FILE, "w") as f:
            json.dump({"subscribed_users": subscribed_users}, f)
    except Exception as e:
        logging.error(f"❌ Error saving subscriptions: {e}")
        
# Function to save channel configuration
def save_guild_channels():
    try:
        with open(CHANNELS_FILE, "w") as f:
            json.dump({"subscription_channels": guild_channels}, f)
    except Exception as e:
        logging.error(f"❌ Error saving channel configuration: {e}")

# --- Background task: Auto-scheduling predictions
async def send_daily_predictions():
    await bot.wait_until_ready()
    while not bot.is_closed():
        schedule.run_pending()
        await asyncio.sleep(60)

def daily_job():
    """Send tomorrow's predictions to all configured guild channels and subscribed users."""
    predictions = predict_bet_tomorrow()
    
    # Handle both possible return types from predict_bet_tomorrow
    if isinstance(predictions, str):
        if not predictions.strip():
            logging.warning("⚠️ No prediction to send.")
            return
        prediction = predictions
    else:
        if not predictions:
            logging.warning("⚠️ No prediction to send.")
            return
        # Format the predictions for Discord
        prediction = format_predictions_for_discord(predictions, is_tomorrow=True)

    # Send to configured guild channels
    for guild in bot.guilds:
        guild_id = str(guild.id)
        sent = False
        
        # Try configured channel first
        if guild_id in guild_channels:
            try:
                channel_id = int(guild_channels[guild_id])
                channel = guild.get_channel(channel_id)
                # Make sure the channel is a TextChannel that can send messages
                if isinstance(channel, discord.TextChannel) and channel.permissions_for(guild.me).send_messages:
                    asyncio.create_task(channel.send(
                        f"📅 **Tomorrow's Predictions:**\n{prediction}"
                    ))
                    logging.info(f"✅ Sent prediction to {guild.name} in #{channel.name}")
                    sent = True
            except Exception as e:
                logging.error(f"❌ Error sending to configured channel in {guild.name}: {e}")
        
        # Fallback to first available text channel
        if not sent:
            for channel in guild.text_channels:  # This already filters to TextChannel objects only
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        asyncio.create_task(channel.send(
                            f"📅 **Tomorrow's Predictions:**\n{prediction}"
                        ))
                        logging.info(f"✅ Sent prediction to {guild.name} in #{channel.name} (fallback)")
                        break
                    except Exception as e:
                        logging.error(f"❌ Error sending to fallback channel in {guild.name}: {e}")
                
    # Send to subscribed users via DM
    for user_id in subscribed_users:
        try:
            user = bot.get_user(user_id)
            if user:
                asyncio.create_task(user.send(f"📅 **Tomorrow's Predictions:**\n{prediction}"))
                logging.info(f"✅ Sent prediction to user {user.name}")
        except Exception as e:
            logging.error(f"❌ Failed to send prediction to user {user_id}: {e}")

# --- Schedule the daily job (10:00 AM server time)
schedule.every().day.at("10:00").do(daily_job)

# --- Autocomplete function for leagues
async def autocomplete_leagues(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=name, value=key)
        for key, name in SUPPORTED_LEAGUES.items()
        if current.lower() in key.lower() or current.lower() in name.lower()
    ][:25]

# --- Events
@bot.event
async def on_ready():
    logging.info(f"✅ Bot is now online as {bot.user}")
    asyncio.create_task(send_daily_predictions())
    try:
        synced = await bot.tree.sync()
        logging.info(f"🔗 Synced {len(synced)} application commands globally.")
    except Exception as e:
        logging.error(f"❌ Failed syncing commands: {e}")

# --- Slash Commands
@bot.tree.command(name="bet", description="Get match predictions for a specific league.")
@app_commands.describe(league="Choose a league")
@app_commands.autocomplete(league=autocomplete_leagues)
async def bet_command(interaction: discord.Interaction, league: str = "EPL"):
    league = league.strip()
    if league not in SUPPORTED_LEAGUES:
        await interaction.response.send_message(f"⚠️ Unknown league `{league}`.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        predictions = predict_bet(league)
        if isinstance(predictions, str):
            # It's an error message
            await interaction.followup.send(predictions)
            return
            
        # Format the predictions for Discord
        formatted_message = format_predictions_for_discord(predictions, is_tomorrow=False)
        await interaction.followup.send(formatted_message)
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        await interaction.followup.send(f"❌ Prediction failed: {e}", ephemeral=True)

@bot.tree.command(name="bet_today", description="Get today's match predictions for a specific league.")
@app_commands.describe(league="Choose a league")
@app_commands.autocomplete(league=autocomplete_leagues)
async def bet_today_command(interaction: discord.Interaction, league: str = "EPL"):
    league = league.strip()
    if league not in SUPPORTED_LEAGUES:
        await interaction.response.send_message(f"⚠️ Unknown league `{league}`.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        predictions = predict_bet(league)
        if isinstance(predictions, str):
            # It's an error message
            await interaction.followup.send(predictions)
            return
            
        # Format the predictions for Discord
        formatted_message = format_predictions_for_discord(predictions, is_tomorrow=False)
        await interaction.followup.send(formatted_message)
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        await interaction.followup.send(f"❌ Prediction failed: {e}", ephemeral=True)
        
@bot.tree.command(name="bet_tomorrow", description="Get tomorrow's match predictions for a specific league.")
@app_commands.describe(league="Choose a league")
@app_commands.autocomplete(league=autocomplete_leagues)
async def bet_tomorrow_command(interaction: discord.Interaction, league: str = "EPL"):
    league = league.strip()
    if league not in SUPPORTED_LEAGUES:
        await interaction.response.send_message(f"⚠️ Unknown league `{league}`.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        predictions = predict_bet_tomorrow(league)
        if isinstance(predictions, str):
            # It's an error message
            await interaction.followup.send(predictions)
            return
            
        # Format the predictions for Discord
        formatted_message = format_predictions_for_discord(predictions, is_tomorrow=True)
        await interaction.followup.send(formatted_message)
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        await interaction.followup.send(f"❌ Prediction failed: {e}", ephemeral=True)

@bot.tree.command(name="leagues", description="Show all available leagues.")
async def leagues_command(interaction: discord.Interaction):
    message = "**🏆 Available Leagues:**\n" + "\n".join(
        f"- `{key}`: {name}" for key, name in SUPPORTED_LEAGUES.items()
    )
    await interaction.response.send_message(message, ephemeral=True)

@bot.tree.command(name="subscribe", description="Subscribe to daily prediction updates.")
async def subscribe_command(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in subscribed_users:
        await interaction.response.send_message("✅ You're already subscribed to daily predictions!", ephemeral=True)
    else:
        subscribed_users.append(user_id)
        save_subscribed_users()
        await interaction.response.send_message("🔔 You've been subscribed to daily predictions! You'll receive updates every morning.", ephemeral=True)

@bot.tree.command(name="unsubscribe", description="Unsubscribe from daily prediction updates.")
async def unsubscribe_command(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        save_subscribed_users()
        await interaction.response.send_message("🔕 You've been unsubscribed from daily predictions.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ You're not currently subscribed to daily predictions.", ephemeral=True)

@bot.tree.command(name="set_channel", description="Set the channel for daily predictions (admin only).")
@app_commands.describe(channel="Select a text channel for daily predictions")
async def set_channel_command(interaction: discord.Interaction, channel: discord.TextChannel):
    # Check if this is a guild command
    if not interaction.guild:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return
        
    # Get the member object to check permissions correctly
    member = interaction.guild.get_member(interaction.user.id)
    if not member or not member.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    guild_channels[guild_id] = str(channel.id)
    save_guild_channels()
    
    await interaction.response.send_message(
        f"✅ Daily predictions will now be sent to {channel.mention}.", 
        ephemeral=True
    )

@bot.tree.command(name="help", description="View all available commands.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Help - Available Commands",
        description="Here's what I can do for you!",
        color=discord.Color.blue()
    )
    embed.add_field(name="`/bet [league]`", value="Get match predictions for a specific league.", inline=False)
    embed.add_field(name="`/bet_today [league]`", value="Get today's match predictions for a specific league.", inline=False)
    embed.add_field(name="`/bet_tomorrow [league]`", value="Get tomorrow's match predictions for a specific league.", inline=False)
    embed.add_field(name="`/subscribe`", value="Subscribe to daily prediction updates.", inline=False)
    embed.add_field(name="`/unsubscribe`", value="Unsubscribe from daily prediction updates.", inline=False)
    embed.add_field(name="`/leagues`", value="List all supported leagues.", inline=False)
    embed.add_field(name="`/set_channel`", value="Set the channel for daily predictions (admin only).", inline=False)
    embed.add_field(name="`/help`", value="Show this help message.", inline=False)
    
    # Add bot info
    embed.set_footer(text="⚽ Football Prediction Bot | Powered by XGBoost")
    embed.set_author(name="Football Predictions", icon_url="https://cdn-icons-png.flaticon.com/512/53/53283.png")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="explain", description="Get detailed explanation for a prediction.")
@app_commands.describe(
    league="Choose a league",
    home_team="Home team name",
    away_team="Away team name"
)
@app_commands.autocomplete(league=autocomplete_leagues)
async def explain_command(interaction: discord.Interaction, league: str, home_team: str, away_team: str):
    league = league.strip()
    if league not in SUPPORTED_LEAGUES:
        await interaction.response.send_message(f"⚠️ Unknown league `{league}`.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        # Get fixture data for the teams
        from fetch_data import fetch_fixture_inputs
        fixtures = fetch_fixture_inputs(league_name=league)
        
        fixture = None
        for f in fixtures:
            if home_team.lower() in f["home"].lower() and away_team.lower() in f["away"].lower():
                fixture = f
                break
                
        if not fixture:
            await interaction.followup.send(f"❌ Could not find match: {home_team} vs {away_team} in {league}", ephemeral=True)
            return
            
        # Generate explanation
        explanation = prediction_explainer.explain_prediction(fixture, league)
        
        # Create embed response
        embed = discord.Embed(
            title=f"Prediction Explanation: {fixture['home']} vs {fixture['away']}",
            description=f"Prediction: **{explanation['prediction']}** with {explanation['confidence']:.1f}% confidence",
            color=0x3498db
        )
        
        # Add feature importance fields
        for feature, importance in sorted(explanation["feature_importance"].items(), key=lambda x: abs(x[1]), reverse=True):
            impact = "+" if importance > 0 else "-"
            embed.add_field(
                name=f"{feature} ({impact})",
                value=f"Impact: {abs(importance):.4f}",
                inline=True
            )
        
        # Create image attachment if available
        if "visualization_base64" in explanation:
            import base64
            img_data = base64.b64decode(explanation["visualization_base64"])
            file = discord.File(io.BytesIO(img_data), filename="explanation.png")
            embed.set_image(url="attachment://explanation.png")
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logging.error(f"Explanation error: {e}")
        await interaction.followup.send(f"❌ Explanation failed: {e}", ephemeral=True)

@bot.tree.command(name="accuracy", description="Show prediction accuracy statistics.")
@app_commands.describe(days="Number of days to analyze (default: 30)")
async def accuracy_command(interaction: discord.Interaction, days: int = 30):
    await interaction.response.defer(thinking=True)
    try:
        report = prediction_tracker.generate_accuracy_report(days=days)
        
        if not report:
            await interaction.followup.send("⚠️ No prediction data available for the requested period.", ephemeral=True)
            return
            
        # Create embed for report
        overall = report["overall_accuracy"] * 100
        color = 0x2ecc71 if overall >= 60 else 0xe74c3c  # Green if above threshold, red if below
        
        embed = discord.Embed(
            title="Prediction Accuracy Report",
            description=f"Analysis of predictions over the last {days} days",
            color=color
        )
        
        embed.add_field(
            name="Overall Accuracy",
            value=f"**{overall:.1f}%** ({report['completed_matches']} matches)",
            inline=False
        )
        
        # Add accuracy by confidence level
        confidence_text = ""
        for level, acc in report["accuracy_by_confidence"].items():
            if not pd.isna(acc):  # Filter out NaN values
                confidence_text += f"- {level}: **{acc*100:.1f}%**\n"
        
        if confidence_text:
            embed.add_field(
                name="By Confidence Level",
                value=confidence_text,
                inline=True
            )
            
        # Add accuracy by league
        league_text = ""
        for league, acc in report["accuracy_by_league"].items():
            if not pd.isna(acc) and league in SUPPORTED_LEAGUES:
                league_text += f"- {league}: **{acc*100:.1f}%**\n"
        
        if league_text:
            embed.add_field(
                name="By League",
                value=league_text,
                inline=True
            )
            
        # Add chart if available
        chart_path = Path(f"data/accuracy_reports/accuracy_chart_{datetime.now().strftime('%Y%m%d')}.png")
        if chart_path.exists():
            with open(chart_path, "rb") as f:
                chart_file = discord.File(f, filename="accuracy.png")
            embed.set_image(url="attachment://accuracy.png")
            await interaction.followup.send(embed=embed, file=chart_file)
        else:
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logging.error(f"Accuracy report error: {e}")
        await interaction.followup.send(f"❌ Failed to generate accuracy report: {e}", ephemeral=True)

@bot.tree.command(name="retrain", description="Retrain the prediction model (admin only).")
@app_commands.describe(force="Force retraining even if not needed")
async def retrain_command(interaction: discord.Interaction, force: bool = False):
    # Check if this is a guild command
    if not interaction.guild:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return
        
    # Get the member object to check permissions correctly
    member = interaction.guild.get_member(interaction.user.id)
    if not member or not member.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        if force:
            from train_model import train_all_models
            await interaction.followup.send("🔄 Forcing model retraining. This may take some time...")
            
            # Run in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, train_all_models)
            
            await interaction.followup.send("✅ Model retraining complete!")
        else:
            await interaction.followup.send("🔍 Checking if model retraining is needed...")
            
            # Run in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            needed = await loop.run_in_executor(None, trigger_retraining)
            
            if needed:
                await interaction.followup.send("✅ Model retraining completed successfully!")
            else:
                await interaction.followup.send("✅ Current model is performing well, no retraining needed.")
                
    except Exception as e:
        logging.error(f"Retraining error: {e}")
        await interaction.followup.send(f"❌ Retraining failed: {e}", ephemeral=True)

# --- Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
