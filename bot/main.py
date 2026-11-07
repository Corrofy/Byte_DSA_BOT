import asyncio
import logging
import discord
from discord.ext import commands
from bot.config import settings
from bot.db.session import init_db

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("dsa_daily")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "bot.cogs.setup",
    "bot.cogs.daily",
    "bot.cogs.linking",
    "bot.cogs.verification",
    "bot.cogs.stats",
    "bot.cogs.leaderboard",
    "bot.cogs.admin",
    "bot.cogs.help",
    "bot.cogs.dev",
    "bot.cogs.scope",
]


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    if settings.DEV_MODE:
        logger.info("🧪 DEV_MODE is ENABLED! /test commands (/test problem now, /test solve, /test status) are active.")

    try:
        if settings.DEV_MODE and settings.DEV_GUILD_ID:
            guild_obj = discord.Object(id=settings.DEV_GUILD_ID)
            bot.tree.copy_global_to(guild=guild_obj)
            synced = await bot.tree.sync(guild=guild_obj)
            logger.info(f"Fast-synced {len(synced)} slash commands directly to dev guild {settings.DEV_GUILD_ID}.")
        else:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} application slash commands globally.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")


async def main():
    await init_db()
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

        if not settings.DISCORD_TOKEN:
            logger.warning("DISCORD_TOKEN is not set. Bot will not connect until token is provided in .env.")
            return

        await bot.start(settings.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
