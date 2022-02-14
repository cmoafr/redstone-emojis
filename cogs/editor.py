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
    
    @cog_ext.cog_component()
    async def CB_Editor_Up(self, btn_ctx):
        await Editor.CB_Editor_Up(btn_ctx)
    
    @cog_ext.cog_component()
    async def CB_Editor_Down(self, btn_ctx):
        await Editor.CB_Editor_Down(btn_ctx)

    @cog_ext.cog_component()
    async def CB_Editor_Left(self, btn_ctx):
        await Editor.CB_Editor_Left(btn_ctx)
    
    @cog_ext.cog_component()
    async def CB_Editor_Right(self, btn_ctx):
        await Editor.CB_Editor_Right(btn_ctx)
    
    @cog_ext.cog_component()
    async def CB_Editor_Place(self, btn_ctx):
        await Editor.CB_Editor_Place(btn_ctx)
    
    @cog_ext.cog_component()
    async def CB_Editor_Remove(self, btn_ctx):
        await Editor.CB_Editor_Remove(btn_ctx)
    
    @cog_ext.cog_component()
    async def CB_Editor_Finish(self, btn_ctx):
        await Editor.CB_Editor_Finish(btn_ctx)
    
    @cog_ext.cog_component()
    async def CB_Editor_Select(self, btn_ctx):
        await Editor.CB_Editor_Select(btn_ctx)
    
    @cog_ext.cog_component()
    async def CB_Editor_None(self, btn_ctx):
        editor = Editor.getEditor(btn_ctx)
        if editor != None: await btn_ctx.edit_origin()
    
    @cog_ext.cog_component()
    async def CB_Editor_None2(self, btn_ctx):
        editor = Editor.getEditor(btn_ctx)
        if editor != None: await btn_ctx.edit_origin()
