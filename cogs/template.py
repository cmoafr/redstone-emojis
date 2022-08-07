import discord
from discord import app_commands
from discord.ext import commands

async def setup(bot: commands.Bot) -> None:
    # Do not register this cog as it is just for showcase.
    # Remove the `pass #` on the following line to make it work.
    pass #await bot.add_cog(Template(bot))

class Template(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.logger.info("Cog template ready!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await message.channel.send("Message received!")

    @app_commands.command(name="template", description="This is a template command")
    @app_commands.describe(value="Description of the parameter")
    @app_commands.rename(value="custom_display_name")
    async def template(self, interaction: discord.Interaction, value: str = "Default value") -> None:
        await interaction.response.send_message(value)

# Examples of commands:
# https://github.com/Rapptz/discord.py/blob/master/examples/app_commands/basic.py