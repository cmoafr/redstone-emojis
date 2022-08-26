import discord

from io import BytesIO

from editor.base import BaseView
from utils.shareability import Shareability

COPYKEYS = ("shareability", "user_id", "blocks", "block", "x", "y", "grid")

class SecondaryView(BaseView):
    def __init__(self, main_view: BaseView) -> None:
        super().__init__(main_view.bot, main_view.shareability, main_view.user_id)
        for k in COPYKEYS:
            setattr(self, k, getattr(main_view, k))
        self.main_view = main_view
        self.update_buttons()

    def update_buttons(self) -> None:
        self.delete.disabled = self.shareability == Shareability.PRIVATE
        #self.generate_preview.disabled = not self.grid
        self.done.disabled = not self.grid

    @discord.ui.button(emoji="\u23eb", style=discord.ButtonStyle.blurple, row=0, disabled=True)
    async def layer_above(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ) -> None:
        if self.is_allowed(interaction):
            pass # TODO
        await self.send(interaction)

    @discord.ui.button(emoji="\u2699", style=discord.ButtonStyle.gray, row=0, disabled=True)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.is_allowed(interaction):
            pass # TODO
        await self.send(interaction)

    @discord.ui.button(emoji="\U0001f5c2", style=discord.ButtonStyle.gray, row=0)
    async def menu(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.is_allowed(interaction):
            await self.main_view.send(interaction)
        else:
            await self.send(interaction)

    @discord.ui.button(emoji="\u23ec", style=discord.ButtonStyle.blurple, row=1, disabled=True)
    async def layer_below(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ) -> None:
        if self.is_allowed(interaction):
            pass # TODO 
        await self.send(interaction)

    @discord.ui.button(label="Help", style=discord.ButtonStyle.gray, row=1)
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            content=self.bot.config["editor help"],
            ephemeral=True
        )

    @discord.ui.button(label="Schem", style=discord.ButtonStyle.green, row=1, disabled=True)
    async def generate_schem(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ) -> None:
        if self.is_allowed(interaction):
            pass # TODO
        await self.send(interaction)

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, row=2)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.is_allowed(interaction) and self.shareability != Shareability.PRIVATE:
            await interaction.message.delete()
        else:
            # Cannot delete ephemeral messages
            await self.send(interaction)

    @discord.ui.button(
        emoji="\U0001f441",
        style=discord.ButtonStyle.blurple,
        row=2,
        disabled=True
    )
    async def generate_preview(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ) -> None:
        if self.is_allowed(interaction):
            pass # TODO
        await self.send(interaction)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.green, row=2)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self.is_allowed(interaction):
            await self.send(interaction)
            return
        
        if not self.grid:
            # Would generate an empty image, cancel
            await self.send(interaction)
            return

        image = self.get_image(
            render_distance=float("inf"), # Get the full image
            border_size=0,
            invert_size=0,
            expand_cursor=False
        )
        with BytesIO() as image_bin:
            image.save(image_bin, "PNG")
            image_bin.seek(0)
            file = discord.File(image_bin, filename="circuit.png")

        await interaction.response.edit_message(content=None, view=None, attachments=[file])
