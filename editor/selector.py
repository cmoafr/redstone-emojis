import discord

from editor.base import BaseView

def get_scores(options, selected):
    """
    Calculates the scores for each option using the longest common subsequence algorithm.
    """
    def lcs(a, b):
        c = [[0 for _ in range(len(b) + 1)] for _ in range(len(a) + 1)]
        for i in range(len(a) + 1):
            c[i][0] = 0
        for j in range(len(b) + 1):
            c[0][j] = 0
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                if a[i - 1] == b[j - 1]:
                    c[i][j] = c[i - 1][j - 1] + 1
                else:
                    c[i][j] = max(c[i - 1][j], c[i][j - 1])
        return c[-1][-1]

    return {option: lcs(option.lower(), selected.lower()) for option in options}



class SelectorDropdown(discord.ui.Select):
    def __init__(self, main_view, options, search_block, selected=None):
        super().__init__(options=options, min_values=1, max_values=1)
        self.main_view = main_view
        self.search_block = search_block
        self.selected = selected

    async def callback(self, interaction):
        selected = self.values[0]

        view = SelectorView(self.main_view, self.search_block, selected)
        view.confirm.disabled = False
        
        await interaction.response.edit_message(
            content=f"Here are the closest matches to `{self.search_block}`.\nPlease confirm you select `{selected}`.",
            view=view,
            attachments=[]
        )



class SelectorView(BaseView):
    def __init__(self, main_view, search_block, selected=None):
        super().__init__(main_view.bot)
        self.main_view = main_view
        self.search_block = search_block

        scores = get_scores(self.main_view.blocks, search_block)
        options = [
            discord.SelectOption(
                label=option,
                value=option,
                emoji=self.bot.get_emoji(self.main_view.blocks[option])
            )
            for option in sorted(scores, key=scores.get)[:25]
        ]
        #print(sorted(scores, key=scores.get)[:25])

        self.dropdown = SelectorDropdown(self.main_view, options, self.search_block, selected)
        self.add_item(self.dropdown)

    @discord.ui.button(label='Search again', style=discord.ButtonStyle.blurple, row=1)
    async def search(self, interaction, button):
        # Local import to prevent circular import
        # TODO: Refacto this
        from editor.search import Search

        await interaction.response.send_modal(Search(self))
        
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, row=1, disabled=True)
    async def confirm(self, interaction, button):
        if self.dropdown.selected:
            self.main_view.block = self.dropdown.selected
            await self.main_view.send(interaction)
