import discord

from difflib import SequenceMatcher

from editor.base import BaseView

def get_scores(options, selected, exact_matches_increment=1):
    """
    Calculates the scores for each option using the builtin SequenceMatcher.
    """
    sm = SequenceMatcher(lambda c: not c.isalnum(), selected.lower())
    scores = {}

    for option in options:
        sm.set_seq2(option.lower())
        score = sm.ratio()
        exact = option.lower().split(" ")
        for word in selected.lower().split(" "):
            if word in exact:
                score += exact_matches_increment # The more exact words in common, the higher it should be
        scores[option] = score

    return scores

def get_best_matches(options, text, count=None):
    options = list(options)
    scores = get_scores(options, text, 0.5)
    options.sort(key=scores.get, reverse=True)
    return options[:count]



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

        options = [
            discord.SelectOption(
                label=option,
                value=option,
                emoji=self.bot.get_emoji(self.main_view.blocks[option])
            )
            for option in get_best_matches(self.main_view.blocks, search_block, 25)
        ]

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