import discord
from discord import app_commands
from discord.ext import commands

from typing import Dict

from utils.config import get_config

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Whitelist(bot))

class Whitelist(commands.Cog):

    group = app_commands.Group(name="whitelist", description="Whitelist to the server", guild_ids=[622199790398341150])
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = get_config("whitelist")
        self.pending = {type_:[] for type_ in self.config["types"]}
        self.accepted = {type_:[] for type_ in self.config["types"]}
        # TODO: Use a DB instead ?

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.logger.info("Cog whitelist ready!")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member) -> None:
        if not user.bot and reaction.message.channel.id == self.config["validation chan"]:
            url = reaction.message.embeds[0].author.icon_url
            i = url.find("avatars/")
            id_ = int(url[i:].split("/")[1])
            user = await self.bot.fetch_user(id_)
            
            for type_ in self.config["types"]:
                for app in self.pending[type_]:
                    if app.id == id_:
                        if reaction.emoji == self.config["accept"]:
                            await user.send("Your request to join the survival has been accepted!")
                            self.pending[type_].remove(app)
                            self.accepted[type_].append(app)
                            return
                        if reaction.emoji == self.config["reject"]:
                            await user.send(f"Your request to join the survival has been denied. You may send a new one if you want. Here is your original:\n`"+app.raw_command+"`")
                            self.pending[type_].remove(app)
                            return
            await reaction.remove(user)
    



    @group.command(name="apply", description="Form to apply for our server")
    @app_commands.describe(username="Your in game name (IGN)", type_="What are you applying for?", reason="A good reason for us to trust you")
    @app_commands.rename(type_="type")
    async def apply(self, interaction: discord.Interaction, username: str, type_: str, reason: str) -> None:
        # TODO: Convert to a proper form
        await interaction.response.defer(ephemeral=True)
        if interaction.channel.type != discord.DMChannel and interaction.channel_id != self.config["request chan"]:
            await interaction.delete_original_message()
            return

        if type_ not in self.config["types"]:
            await interaction.edit_original_message(content=f"Invalid type \"{type_}\". Options are:\n" + ", ".join(self.config["types"]))

        id_ = interaction.user.id
        for app in self.pending[type_]:
            if app.id == id_:
                await interaction.edit_original_message(content="Your request is already being reviewed. Please wait for it to be reviewed. This make take some time.")
                return
        for app in self.accepted[type_]:
            if app.id == id_:
                await interaction.edit_original_message(content="You are already whitelisted and can join right away.")
                return
        
        chan = self.bot.get_channel(self.config["validation chan"])
        if chan is not None:
            try:
                application = Application(interaction, id_, username, type_, reason)
                embed = application.to_embed(self.bot, self.config["types"])
                message = await chan.send(embed=embed)
                await message.add_reaction(self.config["accept"])
                await message.add_reaction(self.config["reject"])
                self.pending[type_].append(application)
                await interaction.edit_original_message(content="Your application has been sent! Please wait for a response.")
                return
            except Exception as e:
                await interaction.edit_original_message(content="An error occured: " + str(e))
                raise e
        await interaction.edit_original_message(content="An error occured: Validation channel not found.")
    
    @group.command(name="list", description="List all applications")
    async def list(self, interaction: discord.Interaction) -> None:
        author = interaction.user
        if author.id != 283358054827819008: # TODO: Generalize
            await interaction.response.send_message("You are not allowed to do that.", ephemeral=True)
            return
        
        for type_ in self.config["types"]:
            await author.send(
                f"`{type_}`:\nPending: " + str(
                    [app.to_dict() for app in self.pending[type_]]
                ) + "\nAccepted: " + str(
                    [app.to_dict() for app in self.accepted[type_]]
                )
            )

    # TODO: Type autocomplete



class Application:

    def __init__(self, interaction: discord.Interaction, id_: int, username: str, type_: str, reason: str) -> None:
        self.interaction = interaction
        self.id = id_
        self.username = username
        self.type = type_
        self.reason = reason

    def to_dict(self) -> Dict[str, str]:
        return {
            "username": self.username,
            "type": self.type,
            "reason": self.reason
        }

    def to_embed(self, bot: commands.Bot, types: Dict[str, int]) -> discord.Embed:
        emoji = str(bot.get_emoji(types[self.type]))
        author = self.interaction.user
        
        embed = discord.Embed(
            title=emoji + " " + self.username,
            description=self.reason
        )
        embed.set_author(
            name=author.name,
            icon_url=author.avatar.url
        )

        return embed

    @property
    def raw_command(self) -> str:
        return f"/whitelist username:{self.username} type:{self.type} reason:{self.reason} "
