import discord
from discord.ext import commands

def setup(bot):
    bot.add_cog(Autoreply(bot))

class Autoreply(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot



    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog autoreply ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if (not message.author.bot):
            content = message.content
            lower = content.lower()
            chan = message.channel

            # Hi X I'm dad
            if " i'm " in lower:
                i = lower.index(" i'm ") + 4 # TODO: Include ponctuation and such
                name = content[i:].strip()
                await chan.send("Hi " + name + " I'm " + self.bot.user.mention)