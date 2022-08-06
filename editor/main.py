import discord

from io import BytesIO

from editor.base import BaseView, NONE
from editor.search import Search

class MainView(BaseView):
    def __init__(self, *args):
        super().__init__(*args)
        self.update_buttons()

    def update_buttons(self):
        self.done.disabled = not self.grid

    @discord.ui.button(label='Undo', style=discord.ButtonStyle.red, row=0, disabled=True)
    async def undo(self, interaction, button):
        if self.is_allowed(interaction):
            pass # TODO
        self.update_buttons()
        await self.send(interaction)

    @discord.ui.button(emoji="\u2b06", style=discord.ButtonStyle.blurple, row=0)
    async def up(self, interaction, button):
        if self.is_allowed(interaction):
            self.y -= 1
        await self.send(interaction)

    @discord.ui.button(label='Redo', style=discord.ButtonStyle.green, row=0, disabled=True)
    async def redo(self, interaction, button):
        if self.is_allowed(interaction):
            pass # TODO
        self.update_buttons()
        await self.send(interaction)

    @discord.ui.button(emoji='\u2b05', style=discord.ButtonStyle.blurple, row=1)
    async def left(self, interaction, button):
        if self.is_allowed(interaction):
            self.x -= 1
        await self.send(interaction)

    @discord.ui.button(label='Place', style=discord.ButtonStyle.blurple, row=1)
    async def place(self, interaction, button):
        if self.is_allowed(interaction):
            if self.block == NONE:
                del self.grid[(self.x, self.y)]
            else:
                self.grid[(self.x, self.y)] = self.blocks[self.block]
            self.update_buttons()
        await self.send(interaction)

    @discord.ui.button(emoji='\u27a1', style=discord.ButtonStyle.blurple, row=1)
    async def right(self, interaction, button):
        if self.is_allowed(interaction):
            self.x += 1
        await self.send(interaction)

    @discord.ui.button(label='Pick', style=discord.ButtonStyle.blurple, row=2)
    async def search(self, interaction, button):
        if self.is_allowed(interaction):
            await interaction.response.send_modal(Search(self))
        else:
            await self.send(interaction)

    @discord.ui.button(emoji='\u2b07', style=discord.ButtonStyle.blurple, row=2)
    async def down(self, interaction, button):
        if self.is_allowed(interaction):
            self.y += 1
        await self.send(interaction)

    @discord.ui.button(label='Done', style=discord.ButtonStyle.green, row=2, disabled=True)
    async def done(self, interaction, button):
        if not self.is_allowed(interaction):
            await self.send(interaction)
            return
        
        if not self.grid:
            # Would generate an empty image, cancel
            await interaction.response.defer()
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
