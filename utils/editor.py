import json
from discord.ext import commands
from discord_slash import SlashContext
from utils.emojis import Emojis
from utils.components import Component

__editors = {}

class Editor:

    emojis = None
    AIR = "g0"

    def __init__(self, ctx : SlashContext):
        if Editor.emojis == None:
            Editor.reset_emojis(ctx.bot)

        self.ctx = ctx
        self.x = 0
        self.y = 0
        self.selected = "g1" #Editor.AIR
        self.grid = {(0, 0): self.emojis.get(self.selected)}
    
    @staticmethod
    def reset_emojis(bot : commands.Bot):
        with open("settings.json") as f:
            guild_ids = json.load(f)["emojis guilds ids"]
        
        L = []
        for guild_id in guild_ids:
            L += bot.get_guild(guild_id).emojis
        
        Editor.emojis = Emojis(L)


    
    def get(self, radius=2):
        grid = []
        for y in range(self.y - radius, self.y + radius + 1):
            row = []
            for x in range(self.x - radius, self.x + radius + 1):
                
                if (x, y) in self.grid:
                    emoji = self.grid[(x, y)]
                else:
                    emoji = Editor.emojis.get(Editor.AIR)
                row.append(emoji)
            grid.append(row)
        
        content = "\n".join(
            "".join(
                str(emoji)
            for emoji in row)
        for row in grid)

        components = None #Component.generate()

        return content, components
