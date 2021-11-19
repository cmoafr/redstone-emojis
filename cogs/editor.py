from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from utils.editor import Editor

def setup(bot : commands.Bot):
    bot.add_cog(EditorCog(bot))

class EditorCog(commands.Cog):

    def __init__(self, bot : commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog editor ready!")

    @commands.Cog.listener()
    async def on_message(self, message : str):
        pass
    
    @cog_ext.cog_slash(
        name="editor",
        description="Visual editor to create circuits\nNote: you can reply to a message with this command to edit it",
        guild_ids=[460515591900495873]
    )
    async def editor(self, ctx : SlashContext):
        await ctx.defer()
        editor = Editor(ctx)
        content, components = editor.get()
        await ctx.send(content=content, components=components)