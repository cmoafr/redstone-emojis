import discord
from discord.ext import commands

from random import random
import re

from utils.config import get_config

ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, users=True, roles=False)

async def setup(bot):
    await bot.add_cog(Autoreply(bot))

class Autoreply(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.groups = get_config("autoreply")

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Cog autoreply ready!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author_id = message.author.id
        if author_id != self.bot.user.id:

            for name, group in self.groups.items():
                match = re.search(group["pattern"].format(
                    message=message,
                    bot=self.bot
                ), message.content, re.IGNORECASE)

                if match is None or random() > group["probability"]:
                    # Negated to reduce indentation
                    continue
                
                response = group["response"].format(
                    message=message,
                    bot=self.bot,
                    match=match,
                    group=match.group(),
                    groups=match.groups(),
                    namedgroups=match.groupdict()
                )

                await message.channel.send(response, allowed_mentions=ALLOWED_MENTIONS)
                self.bot.logger.debug(response)

                if not ALLOWED_MENTIONS.everyone and message.mention_everyone:
                    try:
                        await message.author.edit(
                            nick="Dummy who tried to ping everyone",
                            reason="Tried to ping everyone"
                        )
                    except discord.Forbidden:
                        pass

                if "break" in group and group["break"]:
                    return
