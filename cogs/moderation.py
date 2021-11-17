import discord
from discord.ext import commands
import re

def setup(bot):
    bot.add_cog(Moderation(bot))

class Moderation(commands.Cog):

    KEEP_MSG_DELAY = 120 # Forget messages after 2 minutes
    NB_SPAM_MSG = 5 # Number of messages before boing kicked for spam
    
    def __init__(self, bot):
        self.bot = bot
        self.last_messages = [] # Keeps the last messages from oldest to newest



    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog moderation ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if (not message.author.bot and isinstance(message.channel, discord.TextChannel)):
            content = message.content
            lower = content.lower()
            chan = message.channel

            # Check if spam (WARNING: Untested!!!)
            self.last_messages.append(message)
            from_author = [msg for msg in self.last_messages if msg.author.id == message.author.id]
            if len(from_author) >= self.NB_SPAM_MSG:
                last_from_author = from_author[-self.NB_SPAM_MSG:]
                if len(set([msg.content for msg in last_from_author])) == 1: # If the last 5 messages are the same
                    main_chan = next((chan for chan in message.guild.text_channels if chan.name == "general"), message.guild.text_channels[0]) # Finding main channel or defaulting to first one
                    try:
                        await message.author.kick(reason="Spam")
                        await main_chan.send(f"{message.author.mention} have been kicked for spam.")
                        for msg in last_from_author:
                            await msg.delete()
                    except discord.Forbidden as e:
                        print(e)
                    return

            # Clean up message history
            now = message.created_at.timestamp()
            for i, msg in enumerate(self.last_messages):
                if now - msg.created_at.timestamp() < self.KEEP_MSG_DELAY:
                    break
            self.last_messages = self.last_messages[i:]