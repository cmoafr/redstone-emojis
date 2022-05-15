from discord import app_commands
from discord.ext import commands

from editor.main import MainView

async def setup(bot):
    await bot.add_cog(Editor(bot))

class Editor(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Cog editor ready!")

    @app_commands.command(name="editor", description="Visual editor to create circuits")
    async def editor(self, interaction):
        view = MainView(self.bot)
        await view.send(interaction)
