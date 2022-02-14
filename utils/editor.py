from functools import lru_cache
from io import BytesIO
import json
import sqlite3
from PIL import Image
import discord
from discord_slash import SlashContext
import requests
from utils.emojis import Emojis
from utils.components import Component


class Editor:
    
    __editors = []
    emojis = None
    data_emojis = None
    data_menus = None
    AIR = "g0"
    _BASE_COMPONENTS = [
        [   Component("Air",        Component.RED,      "CB_Editor_Remove"  ),
            Component(None,         Component.BLUE,     "CB_Editor_Up",     "\u2b06"),
            Component("Place",      Component.GREEN,    "CB_Editor_Place"   )
        ], [Component(None,         Component.BLUE,     "CB_Editor_Left",   "\u2b05"),
            Component(callback="CB_Editor_None"),
            Component(None,         Component.BLUE,     "CB_Editor_Right",  "\u27a1")
        ], [Component(callback="CB_Editor_None2"),
            Component(None,         Component.BLUE,     "CB_Editor_Down",   "\u2b07"),
            Component("Finish",     Component.GREEN,    "CB_Editor_Finish"  )]
    ]
    
    def __init__(self, ctx: SlashContext):
        if Editor.emojis == None:
            Editor.reset_emojis(ctx.bot)
        if Editor.data_menus == None or Editor.data_emojis == None:
            Editor.reset_data(ctx.bot)
        
        self.ctx = ctx
        self.grid = {}
        self.x = 0
        self.y = 0
        self.selected = Editor.emojis.get("g1")
        #self.place()
        self.menu_stack = [[item[3] for item in Editor.data_emojis if item[0] == self.selected.id][0]]
        while self.menu_stack[0] != None:
            self.menu_stack.insert(0, [item[2] for item in Editor.data_menus if item[0] == self.menu_stack[-1]][0])
        Editor.__editors.append(self)



    @staticmethod
    def reset_emojis(bot):
        with open("settings.json") as f:
            guild_ids = json.load(f)["emojis guilds ids"]
        
        L = []
        for guild_id in guild_ids:
            L += bot.get_guild(guild_id).emojis
        
        Editor.emojis = Emojis(L)
    
    @staticmethod
    def reset_data(bot):
        database = sqlite3.connect("data.db")
        cursor = database.cursor()
        cursor.execute("SELECT * FROM menus")
        Editor.data_menus = cursor.fetchall()
        cursor.execute("SELECT * FROM emojis")
        Editor.data_emojis = cursor.fetchall()
        database.close()



    def place(self, emoji=None, x=None, y=None):
        if x == None: x = self.x
        if y == None: y = self.y
        if emoji == None: emoji = self.selected
        emoji = Editor.emojis.get(emoji)
        if (x, y) in self.grid: del self.grid[(x, y)]
        if not Editor.emojis.equal(emoji, Editor.AIR):
            self.grid[(x, y)] = emoji
    
    async def update(self, btn_ctx):
        content, components = self.get()
        await btn_ctx.edit_origin(content=content, components=components)
    
    def get(self, radius=3):
        # Content
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
        
        # Sub menus options
        options = []
        menu_list = [
            item for item in Editor.data_menus
            if item[2] == self.menu_stack[-1]
        ]
        if self.menu_stack[-1] != None:
            options = [Component(
                text="< Back",
                callback="Menu ",
                emoji=Editor.emojis.get("\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}")
            )]

        menu_list.sort(key=lambda item: item[3])
        for name, icon, parent, order in menu_list:
            options.append(Component(
                text="> " + name[:23],
                callback="Menu " + name,
                emoji=Editor.emojis.get(icon)
            ))
        
        # Menu options
        emoji_list = [
            item for item in Editor.data_emojis
            if item[3] == self.menu_stack[-1]
        ]
        emoji_list.sort(key=lambda item: item[1])
        for id, name, icon, menu in emoji_list:
            options.append(Component(
                text=name[:25],
                callback="Emoji " + icon,
                emoji=Editor.emojis.get(icon),
                default=Editor.emojis.equal(icon, self.selected)
            ))

        # Generate
        base_components = Editor._BASE_COMPONENTS
        base_components[1][1].emoji = self.selected
        components = Component.generate(
            [
                Component(
                    options=options,
                    callback="CB_Editor_Select"
                )
            ] + base_components
        )
        
        return content, components
    
    def generate(self, export_size=64):
        if len(self.grid) == 0:
            return None
        x_min = y_min = float("inf")
        x_max = y_max = -float("inf")
        for x, y in self.grid:
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)
        
        @lru_cache
        def get_image(emoji):
            r = requests.get(str(emoji.url), stream=True)
            return Image.open(r.raw).resize((export_size, export_size), resample=0).convert("RGBA")

        air = Editor.emojis.get(Editor.AIR)
        grid = [
            [
                self.grid[(x, y)] if (x, y) in self.grid else air
                for x in range(x_min, x_max+1)
            ]
            for y in range(y_min, y_max+1)
        ]

        w, h = export_size*len(grid[0]), export_size*len(grid)
        img = Image.new("RGBA", (w, h), color=(54, 57, 63, 0)) # Default color: Discord BG but transparent
        for i, line in enumerate(grid):
            for j, emoji in enumerate(line):
                e = get_image(emoji)
                img.paste(e, (export_size*j, export_size*i), e)
        return img



    @staticmethod
    def getEditor(btn_ctx):
        for editor in Editor.__editors:
            message = editor.ctx.message
            if message != None and message.id == btn_ctx.origin_message_id:
                return editor
        return None
    
    @staticmethod
    async def CB_Editor_Up(btn_ctx):
        self = Editor.getEditor(btn_ctx)
        if self != None:
            self.y -= 1
            await self.update(btn_ctx)
    
    @staticmethod
    async def CB_Editor_Down(btn_ctx):
        self = Editor.getEditor(btn_ctx)
        if self != None:
            self.y += 1
            await self.update(btn_ctx)
    
    @staticmethod
    async def CB_Editor_Left(btn_ctx):
        self = Editor.getEditor(btn_ctx)
        if self != None:
            self.x -= 1
            await self.update(btn_ctx)
    
    @staticmethod
    async def CB_Editor_Right(btn_ctx):
        self = Editor.getEditor(btn_ctx)
        if self != None:
            self.x += 1
            await self.update(btn_ctx)
    
    @staticmethod
    async def CB_Editor_Place(btn_ctx):
        self = Editor.getEditor(btn_ctx)
        if self != None:
            self.place()
            await self.update(btn_ctx)
    
    @staticmethod
    async def CB_Editor_Remove(btn_ctx):
        self = Editor.getEditor(btn_ctx)
        if self != None:
            self.place(Editor.AIR)
            await self.update(btn_ctx)
    
    @staticmethod
    async def CB_Editor_Finish(btn_ctx):
        self = Editor.getEditor(btn_ctx)
        if self != None:
            img = self.generate()
            if img == None:
                await btn_ctx.origin_message.delete()
            elif type(img) == str:
                await btn_ctx.edit_origin(content=img, components=None)
            else:
                with BytesIO() as img_bin:
                    img.save(img_bin, "PNG")
                    img_bin.seek(0)
                    file = discord.File(img_bin, "export.png")
                await btn_ctx.edit_origin(file=file, content=None, components=None)
    
    @staticmethod
    async def CB_Editor_Select(btn_ctx):
        self = Editor.getEditor(btn_ctx)
        if self != None:
            value = btn_ctx.values[0]
            i = value.find(" ")
            type, value = value[:i], value[i+1:]
            if type == "Menu":
                if value:
                    self.menu_stack.append(value)
                else:
                    self.menu_stack.pop()
            elif type == "Emoji":
                self.selected = Editor.emojis.get(value)
            await self.update(btn_ctx)
