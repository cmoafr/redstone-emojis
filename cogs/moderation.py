import discord
from discord.ext import commands
import re

def setup(bot):
    bot.add_cog(Moderation(bot))

class Moderation(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot



    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog moderation ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if (not message.author.bot):
            content = message.content
            lower = content.lower()
            chan = message.channel

            # Check if spam (WARNING: Untested!!!)
            last_messages = await message.author.history(limit=5).flatten()
            if len(set(msg.content for msg in last_messages)) == 1: # If the last 5 messages are the same
                main_chan = next((chan for chan in message.guild.channels if chan.name == "general"), guild.channels[0]) # Finding main channel or defaulting to first one
                try:
                    await message.author.kick(reason="Spam")
                    await main_chan.send(f"{message.author.mention} has been kicked for spam.")
                except discord.Forbidden:
                    pass
                return
