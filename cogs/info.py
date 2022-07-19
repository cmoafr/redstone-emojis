from discord import app_commands, Embed
from discord.ext import commands

from utils.config import get_config

async def setup(bot):
    await bot.add_cog(Info(bot))

class Info(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = int(bot.config["embed color"][-6:], 16)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Cog info ready!")

    @app_commands.command(name="github", description="Get the link to the GitHub repository")
    async def template(self, interaction):
        """
        Send an embed with the link to the GitHub repository
        """
        embed = Embed(
            title="cmoafr/redstone-emojis",
            url="https://github.com/cmoafr/redstone-emojis",
            description="Here you go :)",
            color=self.embed_color
        )
        embed.set_author(
            name="GitHub",
            url="https://github.com",
            icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/app-icons/710126213695537203/1a83adcc9083303c060b2596fd5f669f.png")
        embed.set_footer(
            text="Made with ❤️ by cmoa",
            icon_url="https://avatars.githubusercontent.com/u/43421239"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="discord", description="Get the link to the Discord server")
    async def discord(self, interaction):
        """
        Send an embed with the link to the Discord server
        """
        embed = Embed(
            title="Discord links",
            color=self.embed_color
        )
        embed.set_author(
            name="Discord",
            url="https://discord.com",
            icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/4/4f/Discord_Logo_sans_texte.svg/1818px-Discord_Logo_sans_texte.svg.png"
            # Don't ask why there is no official png logo
        )
        for name, link in get_config("info")["discord"].items():
            embed.add_field(name=name, value=link, inline=False)
        embed.set_footer(
            text="Made with ❤️ by cmoa",
            icon_url="https://avatars.githubusercontent.com/u/43421239"
        )
        await interaction.response.send_message(embed=embed)
