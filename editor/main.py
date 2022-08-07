import discord

from editor.base import BaseView, NONE
from editor.search import Search
from editor.secondary import SecondaryView

class MainView(BaseView):
    def __init__(self, *args):
        super().__init__(*args)
        self.update_buttons()

    def update_buttons(self):
        self.place.emoji = self.bot.get_emoji(self.blocks[self.block])

    @discord.ui.button(label='Air', style=discord.ButtonStyle.blurple, row=0)
    async def air(self, interaction, button):
        if self.is_allowed(interaction) and (self.x, self.y) in self.grid:
            del self.grid[(self.x, self.y)]
        await self.send(interaction)

    @discord.ui.button(emoji='\u2b06', style=discord.ButtonStyle.blurple, row=0)
    async def up(self, interaction, button):
        if self.is_allowed(interaction):
            self.y -= 1
        await self.send(interaction)

    @discord.ui.button(label='Favs', style=discord.ButtonStyle.gray, row=0, disabled=True)
    async def favorites(self, interaction, button):
        if self.is_allowed(interaction):
            pass # TODO
        await self.send(interaction)

    @discord.ui.button(emoji='\U0001f5c2', style=discord.ButtonStyle.gray, row=0)
    async def menu(self, interaction, button):
        if self.is_allowed(interaction):
            secondary_view = SecondaryView(self)
            await secondary_view.send(interaction)
        else:
            await self.send(interaction)

    @discord.ui.button(emoji='\u2b05', style=discord.ButtonStyle.blurple, row=1)
    async def left(self, interaction, button):
        if self.is_allowed(interaction):
            self.x -= 1
        await self.send(interaction)

    @discord.ui.button(emoji='\u2611', style=discord.ButtonStyle.blurple, row=1) # Emoji is temporary
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

    @discord.ui.button(label='Undo', style=discord.ButtonStyle.red, row=1, disabled=True)
    async def undo(self, interaction, button):
        if self.is_allowed(interaction):
            pass # TODO
        await self.send(interaction)

    @discord.ui.button(emoji='\U0001f50e', style=discord.ButtonStyle.gray, row=2)
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

    @discord.ui.button(label='Last', style=discord.ButtonStyle.gray, row=2, disabled=True)
    async def lastest_blocks(self, interaction, button):
        if self.is_allowed(interaction):
            pass # TODO
        await self.send(interaction)

    @discord.ui.button(label='Redo', style=discord.ButtonStyle.green, row=2, disabled=True)
    async def redo(self, interaction, button):
        if self.is_allowed(interaction):
            pass # TODO
        await self.send(interaction)
