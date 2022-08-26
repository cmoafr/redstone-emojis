import discord
from discord import app_commands
from discord.ext import commands

from editor.main import MainView
from utils.shareability import Shareability

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Editor(bot))

class Editor(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.logger.info("Cog editor ready!")

    @app_commands.command(name="editor", description="Visual editor to create circuits")
    @app_commands.describe(
        shareability="Shareability with others.\n"
        "Value 'Public' will allow anyone to interact with you session and is highly discouraged."
    )
    @app_commands.choices(
        shareability=[
            app_commands.Choice(name=s.value, value=s.value)
            for s in Shareability.__members__.values()
        ]
    )
    async def editor(
            self,
            interaction: discord.Interaction,
            shareability: str = Shareability.PRIVATE.value
        ) -> None:
        view = MainView(self.bot, Shareability(shareability), interaction.user.id)
        await view.send(interaction)
