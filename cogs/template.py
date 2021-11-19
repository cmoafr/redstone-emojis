import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option, SlashCommandOptionType as OptionType

def setup(bot):
    bot.add_cog(Template(bot))

class Template(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



    @commands.Cog.listener()
    async def on_ready(self):
        pass #print("Cog NAME HERE ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    """
    @cog_ext.cog_slash(
        name="command",
        description="Command description",
        options=[create_option(name="option",
                description="Option description",
                option_type=OptionType.STRING,
                required=True)]
    )
    async def command(self, ctx, calculation):
        pass
    """