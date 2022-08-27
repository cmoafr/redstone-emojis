import discord
from discord.ext import commands

from logging import Logger
import os

from utils.config import get_config
from utils.logging import get_logger

class Bot(commands.Bot):

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        def no_prefix(bot: commands.Bot, message: discord.Message) -> str:
            return "<" if message.content.startswith(">") else ">"
        super().__init__(
            command_prefix=no_prefix,
            intents=discord.Intents.all()
        )

        if not os.path.exists("config/bot.json"):
            raise FileNotFoundError(
                "The bot has no config file. "
                "Please copy the default template and change the token."
            )
        self.config = get_config()

    async def on_ready(self) -> None:
        self.logger.info(f"Logged in as {self.user}")

    async def setup_hook(self) -> None:
        """
        Initializes the cogs and synchronizes the commands.
        """

        # Load the cogs
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")

        # Synchronize the commands.
        async def sync() -> None:
            self.logger.debug("Synchronizing commands...")
            await self.wait_until_ready()
            for guild in self.guilds:
                try:
                    await self.tree.sync(guild=guild)
                except discord.Forbidden:
                    self.logger.warning(
                        f"Bot is missing permissions to sync commands in {guild.name}"
                    )
            await self.tree.sync()
            self.logger.debug("Commands synchronized.")
        self.loop.create_task(sync())

def run() -> None:
    logger = get_logger("bot")

    logger.info("Initializing bot...")
    bot = Bot(logger)

    try:
        logger.info("Starting bot...")
        bot.run(bot.config["token"])
    except Exception as e:
        logger.exception(e)
    finally:
        logger.info("Goodbye!")

if __name__ == "__main__":
    run()
