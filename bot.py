import discord
from discord.ext import commands

import os

from utils.config import get_config
from utils.logging import get_logger

class Bot(commands.Bot):

    def __init__(self) -> None:
        no_prefix = lambda bot, message: '<' if message.content.startswith('>') else '>'
        super().__init__(
            command_prefix=no_prefix,
            intents=discord.Intents.all()
        )

        self.config = {}

    async def on_ready(self) -> None:
        self.logger.info(f"Logged in as {self.user}")

    async def setup_hook(self) -> None:
        """
        Initializes the cogs and synchronizes the commands.
        """

        # Load the cogs
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                self.load_extension(f"cogs.{filename[:-3]}")

        # Synchronize the commands.
        async def sync():
            self.logger.debug("Synchronizing commands...")
            await self.wait_until_ready()
            await self.tree.sync()
            self.logger.debug("Commands synchronized.")
        self.loop.create_task(sync())

def run() -> None:
    logger = get_logger("bot")

    logger.info("Initializing bot...")
    bot = Bot()
    bot.config = get_config()
    bot.logger = logger

    try:
        logger.info("Starting bot...")
        bot.run(bot.config["token"])
    finally:
        logger.info("Goodbye!")

if __name__ == "__main__":
    run()
