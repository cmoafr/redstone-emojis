import discord
from discord.ext import commands

from datetime import datetime, timedelta
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
        author = message.author
        for name, group in self.groups.items():

            m = re.search(group["pattern"].format(
                message=message,
                bot=self.bot
            ), message.content, re.IGNORECASE)

            if m is None:
                continue

            conditions = True
            for condition, value in group.get("conditions", {}).items():
                try:
                    match condition:
                        case "bot":
                            conditions &= author.bot == value
                        case "self":
                            conditions &= author.id == self.bot.user.id
                        case "in guild":
                            conditions &= message.guild.id in value
                        case "not in guild":
                            conditions &= message.guild.id not in value
                        case "in channel":
                            conditions &= message.channel.id in value
                        case "not in channel":
                            conditions &= message.channel.id not in value
                        case "in users":
                            conditions &= author.id in value
                        case "not in users":
                            conditions &= author.id not in value
                        case "admin permissions":
                            conditions &= author.guild_permissions.administrator == value
                        case "member for":
                            conditions &= author.joined_at >= datetime.now() + timedelta(seconds=value)
                        case "probability":
                            conditions &= random() <= value
                    print(condition, conditions)
                except Exception as e:
                    pass
            
            if not conditions:
                continue
            
            response = group["response"].format(
                message=message,
                bot=self.bot,
                match=m,
                group=m.group(),
                groups=m.groups(),
                namedgroups=m.groupdict()
            )

            await message.reply(response, allowed_mentions=ALLOWED_MENTIONS)

            if not ALLOWED_MENTIONS.everyone and (message.mention_everyone or "@everyone" in message.content):
                try:
                    await message.author.edit(
                        nick="Dummy who tried to ping everyone",
                        reason="Tried to ping everyone"
                    )
                except discord.Forbidden:
                    pass

            if group.get("break", False):
                return
