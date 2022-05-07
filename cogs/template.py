from discord.ext import commands

async def setup(bot):
    await bot.add_cog(Template(bot))

class Template(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        pass
        #self.bot.logger.info("Cog template ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        pass