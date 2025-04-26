# test_pipeline.py
import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Tuple, Optional, Any, Dict
from dotenv import load_dotenv
import discord
from discord import Message, TextChannel, Guild
from discord.ext import commands
from discord.state import ConnectionState
TextChannelPayload = dict  # or just don't type it at all if it's temporary for tests


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class TestBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        logging.info(f"✅ Bot is online as {self.user}")

class TestMessage(Message):
    def __init__(self, *, state: ConnectionState, channel: TextChannelPayload, content: str):
        data: Dict[str, Any] = {
            'id': 123456789,
            'channel_id': channel.id, # type: ignore
            'author': {
                'id': 987654321,
                'username': 'TestUser',
                'discriminator': '0001',
                'bot': False
            },
            'content': content,
            'timestamp': discord.utils.utcnow().isoformat(),
            'type': 0
        }
        super().__init__(state=state, channel=channel, data=data) # type: ignore

async def test_bot_commands(bot: commands.Bot) -> Tuple[bool, str]:
    try:
        @bot.command()
        async def test(ctx: commands.Context):
            await ctx.send("Test response")
            return True

        # Create proper test channel
        guild_data: Dict[str, Any] = {
            'id': 123,
            'name': 'Test Guild',
            'icon': None,
            'features': []
        }
        guild = Guild(data=guild_data, state=bot._connection) # type: ignore
        
        channel_data: TextChannelPayload = {
            'id': 456,
            'type': 0,
            'guild_id': guild.id,
            'name': 'test-channel',
            'position': 0,
            'permission_overwrites': [],
            'nsfw': False,
            'topic': None, # type: ignore
            'last_message_id': None,
            'rate_limit_per_user': 0,
            'parent_id': None
        }
        
        
        # Create test message and context
        message = TestMessage(state=bot._connection, channel=channel_data, content="!test")
        ctx = await bot.get_context(message)
        
        cmd = bot.get_command("test")
        if cmd is None:
            return False, "❌ Command not found"
            
        await cmd.invoke(ctx)
        return True, "✅ Bot commands working"
    except Exception as e:
        return False, f"❌ Command test failed: {str(e)}"

async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logging.critical("❌ Missing DISCORD_TOKEN in .env file")
        return

    bot = TestBot()
    try:
        async with bot:
            await bot.start(token)
            success, message = await test_bot_commands(bot)
            logging.info(message)
    except Exception as e:
        logging.critical(f"🔴 Critical error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Tests stopped by user")