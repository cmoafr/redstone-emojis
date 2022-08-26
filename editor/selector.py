import discord

from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional

from editor.base import BaseView

def get_scores(options: Iterable[str], selected: str, exact_matches_increment: float = 1) -> Dict[str, float]:
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

def get_best_matches(options: Iterable[str], text: str, count: Optional[int] = None) -> List[str]:
    options = list(options)
    scores = get_scores(options, text, 0.5)
    options.sort(key=scores.get, reverse=True)
    if count is None:
        return options
    return options[:count]



class SelectorDropdown(discord.ui.Select):
    def __init__(self, main_view: BaseView, options: Iterable[discord.SelectOption], search_block: str, selected: Optional[str] = None) -> None:
        super().__init__(options=options, min_values=1, max_values=1)
        self.main_view = main_view
        self.search_block = search_block
        self.selected = selected

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.view.is_allowed(interaction):
            await interaction.response.defer()
            return
        
        selected = self.values[0]

        view = SelectorView(self.main_view, self.search_block, selected)
        view.confirm.disabled = False
        
        await interaction.response.edit_message(
            content=f"Here are the closest matches to `{self.search_block}`.\nPlease confirm you select `{selected}`.",
            view=view,
            attachments=[]
        )



class SelectorView(BaseView):
    def __init__(self, main_view: BaseView, search_block: str, selected: Optional[str] = None) -> None:
        super().__init__(main_view.bot, main_view.shareability, main_view.user_id)
        self.main_view = main_view
        self.search_block = search_block

        options = [
            discord.SelectOption(label=option, value=option)
            for option in get_best_matches(self.main_view.blocks, search_block, 25)
        ]

        self.dropdown = SelectorDropdown(self.main_view, options, self.search_block, selected)
        self.add_item(self.dropdown)

    @discord.ui.button(label="Search again", style=discord.ButtonStyle.blurple, row=1)
    async def search(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self.main_view.is_allowed(interaction):
            return
        
        # Local import to prevent circular import
        # TODO: Refacto this
        from editor.search import Search

        await interaction.response.send_modal(Search(self.main_view))
        
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, row=1, disabled=True)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self.main_view.is_allowed(interaction):
            return
        
        if self.dropdown.selected:
            self.main_view.block = self.dropdown.selected
            self.main_view.update_buttons()
            await self.main_view.send(interaction)
