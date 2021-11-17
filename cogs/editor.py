import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option, SlashCommandOptionType as OptionType
import sqlite3 as sql

def setup(bot):
    bot.add_cog(Editor(bot))

class Editor(commands.Cog):

    AIR = "g0"

    def __init__(self, bot):
        self.bot = bot

        db = sql.connect("data.db")
        cur = db.cursor()
        self.emojis = cur.execute("SELECT * FROM emojis").fetchall()
        self.menus = cur.execute("SELECT * FROM menus").fetchall()
        db.close()

        db = sql.connect("editor.db")
        cur = db.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grid
            (msgId INT,
            x INT,
            y INT,
            emoji STRING)
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS editors
            (msgId INT,
            x INT,
            y INT)
        """)
        db.commit()
        db.close()


    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog editor ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        pass
    
    @cog_ext.cog_slash(
        name="editor",
        description="Visual editor to create circuits\nNote: you can reply to a message with this command to edit it",
        guild_ids=[666735437188038706]
    )
    async def editor(self, ctx):
        await ctx.defer()
        await self.new(ctx)
    


    async def new(self, ctx):
        db = sql.connect("db/editor.db")
        cur = db.cursor()
        cur.execute("INSERT INTO grid VALUES(?, 0, 0, ?)", (ctx.message.id, self.AIR))
        db.commit()
        db.close()

        grid = {(0, 0): self.AIR}

    async def edit(self, ctx):
        pass

    def __fetch(self, msg_id, x, y, radius=2):
        # Warning: Untested
        db = sql.connect("db/editor.db")
        cur = db.cursor()
        cur.execute("""
        SELECT * FROM grid
        WHERE msgId = ?
        AND x BETWEEN ? AND ?
        AND y BETWEEN ? AND ?
        """, (msg_id, x-radius, x+radius, y-radius, y+radius))
        raw = cur.fetchall()
        db.close()

        data = {(d[1], d[2]): d[3] for d in raw}

        grid = [[
            data[(X, Y)] if (X, Y) in data else self.AIR
            for X in range(x-radius, x+radius+1)] for Y in range(y-radius, y+radius+1)]

        return grid
    
    def __edit(self, msg_id, emoji, x, y, radius=2):
        # Warning: Untested
        db = sql.connect("db/editor.db")
        cur = db.cursor()
        cur.execute("""
        IF EXIST(SELECT * FROM grid WHERE msgId = :msgId AND x = :x AND Y = :y)
            UPDATE grid SET emoji = :emoji WHERE msgId = :msgId AND x = :x AND Y = :y
        ELSE
            INSERT INTO grid VALUES(:msgId, :x, :y, :emoji)
        """, {
            "msgId": msg_id,
            "x": x,
            "y": y,
            "emoji": emoji
        })
        db.commit()
        db.close()
