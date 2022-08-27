import logging
import discord
from discord.ext import commands

from typing import Any

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Error(bot))

class Error(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        bot.tree.error(coro = self.__dispatch_to_app_command_handler)
        discord.ui.View.on_error = self.on_view_error
        discord.ui.Modal.on_error = self.on_modal_error

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.logger.info("Cog error ready!")

    async def __dispatch_to_app_command_handler(
            self,
            interaction: discord.Interaction,
            error: discord.app_commands.AppCommandError
        ):
        self.bot.dispatch("app_command_error", interaction, error)



    async def debug(self, interaction: discord.Interaction, type_: str):
        if isinstance(interaction.channel, (discord.DMChannel, discord.PartialMessageable)):
            channel = "DMS"
        else:
            channel = f"#{interaction.channel.name} [{interaction.guild.name}]"
        
        self.bot.logger.debug(
            f"Error by @{interaction.user.name}#{interaction.user.discriminator} "
            f"on {type_} "
            f"in {channel}"
        )

    async def error(self, error: Exception, *args):
        self.bot.logger.exception(error, exc_info=error)

    async def respond(self, interaction: discord.Interaction):
        ids = self.bot.config.get("admin ids", [])
        mentions = [self.bot.get_user(id_).mention for id_ in ids]
        if len(ids) == 0:
            contact = "the bot's owner"
        elif len(ids) == 1:
            contact = mentions[0]
        else:
            contact = ", ".join(mentions[:-1]) + " or " + mentions[-1]

        await interaction.response.send_message(
            "An error occured while doing this interaction.\n"
            f"Please contact {contact}.",
            ephemeral=True
        )



    @commands.Cog.listener()
    async def on_app_command_error(
            self,
            interaction: discord.Interaction,
            error: discord.app_commands.AppCommandError
        ):
        await self.debug(interaction, f"command {interaction.command.name}")
        await self.error(error)
        await self.respond(interaction)

    async def on_view_error(
            self,
            interaction: discord.Interaction,
            error: Exception,
            item: Any
        ):
        await self.debug(interaction, "view")
        await self.error(error, item)
        await self.respond(interaction)

    async def on_modal_error(
            self,
            interaction: discord.Interaction,
            error: Exception
        ):
        await self.debug(interaction, "modal")
        await self.error(error)
        await self.respond(interaction)
