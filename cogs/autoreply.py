import discord
from discord import app_commands
from discord.ext import commands

from datetime import datetime, timedelta
from random import random
import re
from typing import Any, List

from utils.config import get_config, update_config_file

ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, users=True, roles=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Autoreply(bot))

class Autoreply(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.groups = get_config("autoreply")
        self.optouts = get_config("optout")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.logger.info("Cog autoreply ready!")

    async def condition(self, condition: str, value: Any, message: discord.Message):
        author = message.author
        match condition:
            case "bot":
                return author.bot == value
            case "self":
                return author.id == self.bot.user.id
            case "in guild":
                return message.guild.id in value
            case "not in guild":
                return message.guild.id not in value
            case "in channel":
                return message.channel.id in value
            case "not in channel":
                return message.channel.id not in value
            case "in users":
                return author.id in value
            case "not in users":
                return author.id not in value
            case "admin permissions":
                return author.guild_permissions.administrator == value
            case "member for":
                return author.joined_at >= datetime.now() + timedelta(seconds=value)
            case "probability":
                return random() <= value

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        author = message.author
        for name, group in self.groups.items():

            if name in self.optouts and author.id in self.optouts.get(name, []):
                continue

            m = re.search(group["pattern"].format(
                message=message,
                bot=self.bot
            ), message.content, re.IGNORECASE)

            if m is None:
                continue

            conditions = True
            for condition, value in group.get("conditions", {}).items():
                try:
                    conditions &= await self.condition(condition, value, message)
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

            if not ALLOWED_MENTIONS.everyone \
                and (message.mention_everyone or "@everyone" in message.content):
                try:
                    await message.author.edit(
                        nick="Dummy who tried to ping everyone",
                        reason="Tried to ping everyone"
                    )
                except discord.Forbidden:
                    pass

            if group.get("break", False):
                return

    @app_commands.command(name="optout", description="Opt out of autoreplies")
    @app_commands.describe(name="Which autoreply to optout from.")
    async def optout(self, interaction: discord.Interaction, name: str) -> None:
        if name not in self.groups:
            await interaction.response.send_message(f"\"{name}\" does not exist.", ephemeral=True)
            return
        if not self.groups[name].get("optout", False):
            await interaction.response.send_message(
                f"You cannot opt out from \"{name}\".",
                ephemeral=True
            )
            return
        if interaction.user.id in self.optouts.get(name, []):
            await interaction.response.send_message(
                f"You are already opted out from \"{name}\".",
                ephemeral=True
            )
            return

        if not name in self.optouts:
            self.optouts[name] = []
        self.optouts[name].append(interaction.user.id)
        update_config_file("optout", self.optouts) # TODO: Move to DB instead ?
        await interaction.response.send_message(
            f"You have successfully been optout from \"{name}\".",
            ephemeral=True
        )

    @optout.autocomplete("name")
    async def optout_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str
        ) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=name, value=name)
            for name in self.groups
            if "optout" in self.groups[name]
        ]
