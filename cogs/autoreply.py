import discord
from discord.ext import commands
import re

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
            im = re.search(r"""
                           (.*?[\s])?          # Some text
                           (im|i\ am|i\'m)[\s] # The "i'm" and a whitespace
                           (?P<name>.+)       # The name
                           """, lower, re.VERBOSE)
            if im:
                name = im.group("name").strip()
                await chan.send("Hi " + name + ", I'm " + self.bot.user.mention)