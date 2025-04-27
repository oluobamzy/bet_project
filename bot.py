import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import schedule
from discord import app_commands
from predict import predict_bet, predict_bet_tomorrow

# --- Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ Discord token not found in .env file")

# --- Supported leagues
SUPPORTED_LEAGUES = {
    # Top 5 major leagues
    "EPL": "English Premier League",
    "LaLiga": "Spanish La Liga",
    "SerieA": "Italian Serie A",
    "Bundesliga": "German Bundesliga",
    "Ligue1": "French Ligue 1",

    # Other top-tier European leagues (A-Z)
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
intents.guilds = True  # Needed to access guild info for slash commands

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Autocomplete function for leagues
async def autocomplete_leagues(interaction: discord.Interaction, current: str):
    current = current.lower()
    return [
        app_commands.Choice(name=name, value=key)
        for key, name in SUPPORTED_LEAGUES.items()
        if current in key.lower() or current in name.lower()
    ][:25]  # Discord allows max 25 choices

# --- Background task
async def send_daily_predictions():
    await bot.wait_until_ready()
    while not bot.is_closed():
        schedule.run_pending()
        await asyncio.sleep(60)

def daily_job():
    try:
        prediction = predict_bet_tomorrow()
        if not prediction:
            print("⚠️ No prediction to send.")
            return
    except Exception as e:
        print(f"❌ Error fetching tomorrow's prediction: {e}")
        return

    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    asyncio.create_task(channel.send(
                        f"📅 **Tomorrow's Predictions:**\n{prediction}",
                        delete_after=3600  # Auto-delete after 1 hour to keep channels clean
                    ))
                    print(f"✅ Sent prediction to {guild.name} in #{channel.name}")
                    break  # Send to only one channel per guild
                except Exception as e:
                    print(f"⚠️ Failed to send in {channel.name}: {e}")

# --- Schedule the daily job
schedule.every().day.at("10:00").do(daily_job)

# --- Events
@bot.event
async def on_ready():
    print(f"✅ Bot is now online as {bot.user}")
    asyncio.create_task(send_daily_predictions())
    try:
        synced = await bot.tree.sync()
        print(f"🔗 Synced {len(synced)} application commands globally.")
    except Exception as e:
        print(f"❌ Failed syncing commands: {e}")

# --- Slash Commands
@bot.tree.command(name="bet", description="Get match predictions for a specific league.")
@app_commands.describe(league="Choose a league")
@app_commands.autocomplete(league=autocomplete_leagues)
async def bet_command(interaction: discord.Interaction, league: str = "EPL"):
    """Get match predictions for a given league."""
    league = league.strip()

    if league not in SUPPORTED_LEAGUES:
        await interaction.response.send_message(f"⚠️ Unknown league `{league}`. Use `/leagues` to view supported leagues.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    try:
        prediction = predict_bet(league)
        if not prediction.strip():
            await interaction.followup.send("❌ No predictions generated.", ephemeral=True)
        else:
            await interaction.followup.send(
                f"🔮 **Predictions for {SUPPORTED_LEAGUES[league]}:**\n{prediction}"
            )
    except Exception as e:
        await interaction.followup.send(f"❌ Prediction failed: {e}", ephemeral=True)

@bot.tree.command(name="leagues", description="Show all available leagues.")
async def leagues_command(interaction: discord.Interaction):
    """List all supported leagues."""
    message = "**🏆 Available Leagues:**\n" + "\n".join(
        f"- `{key}`: {name}" for key, name in SUPPORTED_LEAGUES.items()
    )
    await interaction.response.send_message(message, ephemeral=True)

@bot.tree.command(name="help", description="View all available commands.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Help - Available Commands",
        description="Here’s what I can do for you!",
        color=discord.Color.blue()
    )
    embed.add_field(name="`/bet [league]`", value="Get match predictions for a specific league (default: EPL)", inline=False)
    embed.add_field(name="`/leagues`", value="List all supported leagues.", inline=False)
    embed.add_field(name="`/help`", value="Show this help message.", inline=False)

    # Send directly without deferring (since it is quick)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="subscribe", description="Subscribe to daily predictions.")
async def subscribe(interaction: discord.Interaction):
    """Subscribe to daily predictions."""
    user_id = interaction.user.id
    # In a real deployment, you would save this info in a database or file
    # Here, we're simulating it with a list.
    if user_id not in subscribed_users:
        subscribed_users.append(user_id)
        await interaction.response.send_message("✅ You have subscribed to daily predictions!", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ You're already subscribed.", ephemeral=True)

@bot.tree.command(name="unsubscribe", description="Unsubscribe from daily predictions.")
async def unsubscribe(interaction: discord.Interaction):
    """Unsubscribe from daily predictions."""
    user_id = interaction.user.id
    # In a real deployment, you would save this info in a database or file
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        await interaction.response.send_message("✅ You have unsubscribed from daily predictions.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ You are not subscribed.", ephemeral=True)

# --- Run
if __name__ == "__main__":
    # A placeholder for subscribed users, ideally this would be in a database or a persistent file
    subscribed_users = []

    bot.run(TOKEN)
