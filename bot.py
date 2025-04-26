# bot.py

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from predict import predict_bet

# --- Load environment variables
load_dotenv()

# --- Get token
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ Discord token not found in .env file")

# --- Set up Discord client
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- List of supported leagues
SUPPORTED_LEAGUES = {
    "EPL": "English Premier League",
    "LaLiga": "Spanish La Liga",
    "SerieA": "Italian Serie A",
    "Bundesliga": "German Bundesliga",
    "Ligue1": "French Ligue 1"
    # You can expand this as you add more leagues support
}

# --- Events
@bot.event
async def on_ready():
    print(f"✅ Bot is now online as {bot.user}")

# --- Commands
@bot.command(name="bet")
async def bet(ctx, league: str = "EPL"):
    """Predict match outcomes for a given league."""
    league = league.strip()
    msg = await ctx.send(f"🔄 Fetching predictions for **{league}**...", delete_after=5)

    if league not in SUPPORTED_LEAGUES:
        await ctx.send(f"⚠️ Unknown league `{league}`. Use `!leagues` to see available leagues.", delete_after=8)
        return

    try:
        prediction = predict_bet(league)
        if not prediction or prediction.strip() == "":
            await ctx.send("❌ No prediction results were generated.", delete_after=8)
        else:
            await ctx.send(f"🔮 Predictions for {SUPPORTED_LEAGUES[league]}:\n{prediction}")
    except Exception as e:
        await ctx.send(f"❌ Prediction failed: {e}", delete_after=10)

@bot.command(name="leagues")
async def leagues(ctx):
    """Show available leagues you can predict for."""
    message = "**🏆 Available Leagues:**\n" + "\n".join(
        f"- `{key}`: {name}" for key, name in SUPPORTED_LEAGUES.items()
    )
    await ctx.send(message, delete_after=15)


# --- Run
if __name__ == "__main__":
    bot.run(TOKEN)
