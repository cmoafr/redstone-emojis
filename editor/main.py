import discord

from editor.base import BaseView

class MainView(BaseView):
    def __init__(self, bot):
        super().__init__(bot)

    @discord.ui.button(label='Undo', style=discord.ButtonStyle.red, row=0, disabled=True)
    async def undo(self, interaction, button):
        # TODO
        await self.send(interaction)

    @discord.ui.button(emoji="\u2b06", style=discord.ButtonStyle.blurple, row=0)
    async def up(self, interaction, button):
        self.y -= 1
        await self.send(interaction)

    @discord.ui.button(label='Redo', style=discord.ButtonStyle.green, row=0, disabled=True)
    async def redo(self, interaction, button):
        # TODO
        await self.send(interaction)

    @discord.ui.button(emoji='\u2b05', style=discord.ButtonStyle.blurple, row=1)
    async def left(self, interaction, button):
        self.x -= 1
        await self.send(interaction)

    @discord.ui.button(label='Place', style=discord.ButtonStyle.blurple, row=1)
    async def place(self, interaction, button):
        self.grid[(self.x, self.y)] = self.block
        await self.send(interaction)

    @discord.ui.button(emoji='\u27a1', style=discord.ButtonStyle.blurple, row=1)
    async def right(self, interaction, button):
        self.x += 1
        await self.send(interaction)

    @discord.ui.button(label='Block', style=discord.ButtonStyle.blurple, row=2, disabled=True)
    async def search(self, interaction, button):
        # TODO
        await self.send(interaction)

    @discord.ui.button(emoji='\u2b07', style=discord.ButtonStyle.blurple, row=2)
    async def down(self, interaction, button):
        self.y += 1
        await self.send(interaction)

    @discord.ui.button(label='Done', style=discord.ButtonStyle.green, row=2, disabled=True)
    async def done(self, interaction, button):
        # TODO
        await self.send(interaction)
