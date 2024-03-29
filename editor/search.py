import discord

from random import choice

from editor.base import BaseView
from editor.selector import SelectorView

class Search(discord.ui.Modal):

    def __init__(self, view: BaseView) -> None:
        self.view = view
        super().__init__(title="Search")

        self.block.placeholder = choice(list(self.view.blocks))
        self.error = None


    block = discord.ui.TextInput(label="Block name")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not self.view.is_allowed(interaction):
            return

        block = self.block.value

        # The block exists, change and return to main menu
        if block is None or block in self.view.blocks:
            self.view.block = block or self.view.block
            self.view.update_buttons()
            await self.view.send(interaction)
            return

        # The block does not exists, try to find the closest matches
        await interaction.response.edit_message(
            content=f"Here are the closest matches to `{block}`.\nPlease select the correct one.",
            view=SelectorView(self.view, block),
            attachments=[]
        )
