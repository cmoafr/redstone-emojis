import asyncio
import discord
import json
import logging
import os
import re
import requests
import signal
import sqlite3
from asyncpraw import Reddit
from asyncprawcore.exceptions import NotFound as PrawNotFound, RequestException
from datetime import datetime
from discord.client import _cleanup_loop
from discord.ext.commands import Bot
from discord_slash import SlashCommand, SlashContext, SlashCommandOptionType, ButtonStyle
from discord_slash.utils import manage_commands, manage_components
from functools import lru_cache
from io import BytesIO
from PIL import Image



EMPTY = "\u200b"
EMBED_COLOR = 0xFF0000
BACK_EMOJI = '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}' # /!\ Must be Unicode no shortcode

no_prefix = lambda bot, message: '<' if message.content.startswith('>') else '>'

emoji_full_pattern = re.compile("<a?:[a-zA-Z0-9_]{2,32}:[0-9]+>")
emoji_pattern = re.compile(":[a-zA-Z0-9_]{2,32}:")

AIR = "g0"
BLOCK = "g1"
MARKER_HORIZ = "fb"
MARKER_VERTI = "fc"
export_size = 64





bot = Bot(command_prefix=no_prefix)
slash = SlashCommand(bot, sync_commands=True)

if not os.path.isdir("logs"):
    os.mkdir("logs")
i = 1
while True:
    logFilename = datetime.date(datetime.now()).strftime(f"logs/%Y-%m-%d_{i}.log")
    if not os.path.isfile(logFilename):
        break
    i += 1

database = sqlite3.connect("data.db")
cursor = database.cursor()




def Logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s",
        "%H:%M:%S"
    )
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    fileHandler = logging.FileHandler(logFilename)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    return logger

log = Logger("main")





class Option:

    def __init__(self, name, description, type_, required, choices=[], usage=None):
        self.option = manage_commands.create_option(name, description, type_, required, choices)
        self.name = name
        self.description = description
        self.type = self.option["type"]
        self.required = required
        self.choices = self.option["choices"]
        if usage:
            self.usage = usage
        else:
            usage = self.name
            if self.choices:
                usage = "|".join(choice["name"] for choice in self.choices)
            # TODO: Handle subcommands and groups
            if self.required:
                self.usage = "<" + usage + ">"
            else:
                self.usage = "[" + usage + "]"



class Command:

    def __init__(self, func, name=None, description=None, usage=None, hidden=False, options=[], **kwargs):
        self.func = func
        self.name = (name or func.__name__).lower()
        description = func.__doc__ or "\n" + (description or "")
        self.hidden = hidden
        self.options = options
        self.kwargs = kwargs
        
        if description[0] == '\n':
            self.description = description.strip() or EMPTY
            self.usage = usage or self.get_default_usage()
        else:
            split = description.split('\n')
            self.description = '\n'.join(split[1:]).strip() or EMPTY
            self.usage = usage or split[0]

    def register(self, slash):
        self.cmdobj = slash.add_slash_command(self.func, self.name, self.description, **self.kwargs)
        return self.cmdobj

    def help(self):
        return self.usage

    def get_default_usage(self):
        usage = "/" + self.name + " "
        for option in self.options:
            usage += option.usage + " "
        return usage.strip()



class Commands:
    
    def __init__(self, slash):
        self.slash = slash
        self.list = []

    def register(self, **kwargs):
        def wrapper(func):
            nonlocal kwargs
            cmd = Command(func, **kwargs)
            self.list.append(cmd)
            obj = cmd.register(slash)
            return obj
        return wrapper



class LayersEmbed:

    interactions = []

    def __init__(self, ctx, layers=None, name=None):
        self.ctx = ctx
        self.layers = layers or format_msg(self.ctx.message.content, split=False).split("\n\n")
        for layer in self.layers:
            if len(layer) >= 4096:
                self.layers = ["Message is too long and could not be sent."]
                break
        self.name = name
        self.current = 0
        self.interactions.append(self)

    def get_data(self, layer):
        if layer < 0 or layer >= len(self.layers):
            return None, None
        
        embed = discord.Embed(
            title=self.name,
            description=self.layers[layer],
            color=EMBED_COLOR
        )
        buttons = []
        components = None

        if len(self.layers) > 1:
            buttons = [manage_components.create_button(
                style=ButtonStyle.gray,
                label="Layer " + str(layer+1) + "/" + str(len(self.layers)),
                custom_id="__layersCB_none"
            )]
            if layer != 0:
                buttons.insert(0, manage_components.create_button(
                    style=ButtonStyle.blue,
                    label="<-",
                    custom_id="__layersCB_prev"
                ))
            if layer != len(self.layers)-1:
                buttons.append(manage_components.create_button(
                    style=ButtonStyle.blue,
                    label="->",
                    custom_id="__layersCB_next"
                ))
            components = [manage_components.create_actionrow(*buttons)]

        return embed, components

    async def send(self, layer=0):
        self.current = layer
        embed, components = self.get_data(layer)
        await self.ctx.send(embed=embed, components=components)

    async def edit(self, button_ctx, layer=0):
        self.current = layer
        embed, components = self.get_data(layer)
        await button_ctx.edit_origin(embed=embed, components=components)



    def find(id_):
        for lm in LayersEmbed.interactions:
            message = lm.ctx.message
            if message != None:
                if message.id == id_:
                    return lm
        return None

    @slash.component_callback()
    async def __layersCB_prev(button_ctx):
        id_ = button_ctx.origin_message_id
        if id_==None: return
        origin = LayersEmbed.find(id_)
        if origin:
            await origin.edit(button_ctx, origin.current-1)

    @slash.component_callback()
    async def __layersCB_next(button_ctx):
        id_ = button_ctx.origin_message_id
        if id_==None: return
        origin = LayersEmbed.find(id_)
        if origin:
            await origin.edit(button_ctx, origin.current+1)

    @slash.component_callback()
    async def __layersCB_none(button_ctx):
        id_ = button_ctx.origin_message_id
        if id_==None: return
        origin = LayersEmbed.find(id_)
        if origin:
            await origin.edit(button_ctx, origin.current)



class Editor:

    list = []

    def __init__(self, ctx, width, height):
        if int(width) != width or width <= 0 or int(height) != height or height <= 0:
            self.send = lambda: False
            ctx.send("Invalid size.")
        self.ctx = ctx
        self.width = width
        self.height = height
        self.reset_message()
        self.list.append(self)

    def reset_message(self):
        self.x = 0
        self.y = 0
        self.selected = BLOCK
        cursor.execute("SELECT menu FROM emojis WHERE icon=?", [self.selected])
        self.menu = [cursor.fetchone()[0]]
        while self.menu[0] != None:
            cursor.execute("SELECT parent FROM menus WHERE name=?", [self.menu[0]])
            self.menu.insert(0, cursor.fetchone()[0])
        self.grid = [[AIR for j in range(self.width)] for i in range(self.height)]
        self.undos = []
        self.buttons = [
            [(4, "Undo", "__editorCB_undo"),    (1, "˄", "__editorCB_up"),      (1, "Air", "__editorCB_air")         ],
            [(1, "˂", "__editorCB_left"),       (1, AIR, "__editorCB_place"),   (1, "˃", "__editorCB_right")        ],
            [(3, "Echo", "__editorCB_echo"),    (1, "˅", "__editorCB_down"),    (3, "PNG", "__editorCB_export")  ]
        ]
        if self.width * self.height > 2000/24.5:
            self.buttons[2][0] = (2, "", "__editorCB_none")

    def get_data(self):

        sx = max(min(self.x-3, self.width-7), 0)
        sy = max(min(self.y-3, self.height-7), 0)    
        ex, ey = min(sx+7, self.width), min(sy+7, self.height)
        border_horiz = [AIR] + [MARKER_VERTI if j == self.x else AIR for j in range(sx, ex)] + [AIR]
        grid = [border_horiz]
        for i in range(sy, ey):
            border_vert = MARKER_HORIZ if i == self.y else AIR
            line = [border_vert]
            for j in range(sx, ex):
                line.append(self.grid[i][j])
            line += [border_vert]
            grid.append(line)
        grid += [border_horiz]

        message = "\n".join("".join(str(emojis_dict[name]) for name in line) for line in grid)


        self.buttons[1][1] = (1, self.selected, "__editorCB_place")

        options = []
        if self.menu[-1] == None:
            cursor.execute("SELECT * FROM menus WHERE parent IS NULL")
        else:
            options = [manage_components.create_select_option(
                label="< Back",
                value="Menu ",
                emoji=BACK_EMOJI
            )]
            cursor.execute("SELECT * FROM menus WHERE parent=?", [self.menu[-1]])
        menu_list = cursor.fetchall()
        menu_list.sort(key=lambda item: item[3])
        for name, icon, parent, order in menu_list:
            options.append(manage_components.create_select_option(
                label="> "+name[:23],
                value="Menu "+name,
                emoji=emojis_dict[icon]
            ))

        if self.menu[-1] == None:
            cursor.execute("SELECT * FROM emojis WHERE menu IS NULL")
        else:
            cursor.execute("SELECT * FROM emojis WHERE menu=?", [self.menu[-1]])
        emojis_list = cursor.fetchall()
        emojis_list.sort(key=lambda item: item[1])
        for name, icon, menu in emojis_list:
            options.append(manage_components.create_select_option(
                label=name[:25],
                value="Emoji "+icon,
                emoji=emojis_dict[icon],
                default=icon==self.selected
            ))
        
        buttons = [[manage_components.create_select(
            options=options,
            custom_id="__editorCB_select"
        )]]
        
        for raw_line in self.buttons:
            line = []
            for raw in raw_line:
                name = raw[1] or EMPTY
                kwargs = {"style": raw[0], "custom_id": raw[2]}
                if name in emojis_dict:
                    kwargs["emoji"] = emojis_dict[name]
                else:
                    kwargs["label"] = name
                line.append(manage_components.create_button(**kwargs))
            buttons.append(line)
        components = [manage_components.create_actionrow(*row) for row in buttons]

        return message, components

    async def update(self, btn_ctx):
        message, components = self.get_data()
        await btn_ctx.edit_origin(content=message, components=components)

    async def send(self):
        message, components = self.get_data()
        await self.ctx.send(message, components=components)

    def find(btn_ctx):
        id_ = btn_ctx.origin_message_id
        for editor in Editor.list:
            message = editor.ctx.message
            if message != None and message.id == id_:
                return editor
        log.exception(LookupError("Editor interaction with id "+str(id_)+" not found"))

    @slash.component_callback()
    async def __editorCB_none(btn_ctx):
        self = Editor.find(btn_ctx)
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_select(btn_ctx):
        self = Editor.find(btn_ctx)
        value = btn_ctx.values[0]
        i = value.find(" ")
        type, value = value[:i], value[i+1:]
        if type == "Menu":
            if value:
                self.menu.append(value)
            else:
                self.menu.pop()
        elif type == "Emoji":
            self.selected = value
        else:
            pass # Should never happen
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_up(btn_ctx):
        self = Editor.find(btn_ctx)
        if self.y > 0:
            self.y -= 1
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_down(btn_ctx):
        self = Editor.find(btn_ctx)
        if self.y < self.height-1:
            self.y += 1
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_left(btn_ctx):
        self = Editor.find(btn_ctx)
        if self.x > 0:
            self.x -= 1
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_right(btn_ctx):
        self = Editor.find(btn_ctx)
        if self.x < self.width-1:
            self.x += 1
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_place(btn_ctx):
        self = Editor.find(btn_ctx)
        old = self.grid[self.y][self.x]
        if old != self.selected:
            self.undos.append((self.x, self.y, old, self.selected))
            self.grid[self.y][self.x] = self.selected
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_air(btn_ctx):
        self = Editor.find(btn_ctx)
        self.grid[self.y][self.x] = AIR
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_undo(btn_ctx):
        self = Editor.find(btn_ctx)
        if self.undos:
            x, y, old, new = self.undos.pop()
            self.grid[y][x] = old
        await self.update(btn_ctx)

    @slash.component_callback()
    async def __editorCB_echo(btn_ctx):
        await btn_ctx.edit_origin(content="Your circuit has been echoed back below.", components=None)
        self = Editor.find(btn_ctx)
        message = "\n".join(":"+"::".join(line)+":" for line in self.grid)
        await echo.invoke(self.ctx, message)

    @slash.component_callback()
    async def __editorCB_export(btn_ctx):
        await btn_ctx.edit_origin(content="Your circuit has been exported to an image below.", components=None)
        self = Editor.find(btn_ctx)
        message = "\n".join(":"+"::".join(line)+":" for line in self.grid)
        await export.invoke(self.ctx, message)





def format_msg(message, max_length=2000, split=True):

    if type(message) == list:
        for i, x in enumerate(message):
            if type(x) == list:
                message[i] = "\n".join(x)
        message = "\n\n".join(message)

    message = message.replace("\\n", "\n").strip()
    splited = []
    start = 0
    i = 0
    while i < len(message):
        c = message[i]

        # TODO: Change for 3.10 switch statements
        if c == "\\":
            i += 2
            continue

        if c == "\n":
            if message[i+1] == "\n":
                splited.append(message[start:i])
                start = i = i + 2
                continue

        if c == "`":
            n = 1
            if message[i:i+3] == "```":
                n = 3
                i += 2
            j = i + 1
            while j < len(message):
                if message[j:j+n] == "`"*n:
                    i = j + n-1
                    break
                if n == 1 and message[j-1] == "\n":
                    message = message[:j-1] + "\\n" + message[j:]
                j += 1

        if c == "<":
            search = emoji_full_pattern.search(message, i)
            if search and search.start() == i:
                i = search.end()
                continue

        if c == ":":
            search = emoji_pattern.search(message, i)
            if search and search.start() == i:
                e = search.end()
                name = message[i+1:e-1]
                if name in emojis_dict:
                    emoji = emojis_dict[name]
                    full = str(emoji)
                else:
                    full = ":"+name+":"
                message = message[:i] + full + message[e:]
                i += len(full)
                continue
            
        i += 1
    splited.append(message[start:].strip())

    if not split:
        return "\n\n".join(splited)

    splited = [x.strip() for x in splited]
    if max_length != None and max(len(x) for x in splited) > max_length:
        return ["Message is too long and could not be send."]
    
    return splited # TODO: Join messages if possible





default_settings = '''{
    "token": "INSERT YOUR TOKEN HERE"
    "emojis guilds ids": [],
    "discord links": {
        "Bot": "https://discord.gg/e5Jag3kuxq"
    }
}'''



commands = Commands(slash)

try:
    with open("settings.json") as f:
        settings = json.load(f)
except FileNotFoundError:
    with open("settings.json", "w") as f:
        f.write(default_settings)
    log.exception(FileNotFoundError("Settings file not found. Please put your Discord bot token in the newly created file."))
    exit()

try:
    with open("presets.json") as f:
        presets = json.load(f)
except FileNotFoundError:
    presets = {"and":[[":hd::g1::j1::g0::g0::g0::g0:",":g0::g0::fk::eb::g1::j6::hx:",":hd::g1::j1::g0::g0::g0::g0:"]]}

try:
    if "reddit" in settings:
        reddit = Reddit(client_id=settings["reddit"]["id"],
                             client_secret=settings["reddit"]["secret"],
                             user_agent=settings["reddit"]["user agent"])
        del settings["reddit"]["secret"]
        subreddits = {connection["subreddit"]: connection["discord"] for connection in settings["reddit"]["connections"]}
except Exception as e:
    log.exception(e) # TODO ?





@bot.event
async def on_ready():
    global emojis, emojis_dict
    try:
        commands_list = await manage_commands.get_all_commands(bot.user.id, settings["token"])
        del settings["token"]
    except KeyError:
        pass # Bot reconnected, no need to reaquire the list.

    emojis = []
    for guild_id in settings["emojis guilds ids"]:
        emojis += bot.get_guild(guild_id).emojis
    emojis.sort(key=lambda e: e.name)
    emojis_dict = {e.name:e for e in emojis}

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="with redstone! Use /help"
        )
    )

    log.info("Connected on {} guilds with {} ({}) commands.".format(len(bot.guilds), len(commands.list), len(commands_list)))





# Commands

@commands.register()
async def help(ctx):
    """
    Shows the list of all commands
    """
    ordered = sorted(commands.list, key=lambda cmd: cmd.name)
    embed = discord.Embed(
        title="Commands:",
        color=EMBED_COLOR
    )
    for cmd in ordered:
        if not (cmd.hidden and not ctx.author.top_role.permissions.administrator):
            embed.add_field(
                name=cmd.usage or "Error",
                value=cmd.description or EMPTY,
                inline=False
            )
    await ctx.send(embed=embed)



@commands.register(options=[Option(
    name="message",
    description="Message to be formated and echoed back",
    type_=SlashCommandOptionType.STRING,
    required=True
)])
async def echo(ctx, message):
    """
    Send back the message with the correct format
    """
    split = format_msg(message)
    for msg in split:
        await ctx.send(msg)



@commands.register(options=[Option(
    name="width",
    description="Width of the grid",
    type_=SlashCommandOptionType.INTEGER,
    required=True
), Option(
    name="height",
    description="Height of the grid",
    type_=SlashCommandOptionType.INTEGER,
    required=True
)])
async def editor(ctx, width, height):
    """
    Visual editor to create emoji circuits
    """
    await ctx.defer()
    try:
        await Editor(ctx, int(width), int(height)).send()
    except Exception as e:
        #await ctx.send("An error occured. More details about errors will be added later.")
        log.exception(e)



@commands.register()
async def emojis(ctx):
    """
    Shows all emojis.\nWarning: Will spam. Use in appropriate channel
    """
    if len(emojis) == 0:
        await ctx.send("Error: No emojis found.")
        return
    message = ""
    for i, emoji in enumerate(emojis):
        if i%60 == 0 and message:
            await ctx.send(message)
            if i == 60:
                ctx = ctx.channel
            message = ""
        message += "<:{}:{}>".format(emoji.name, emoji.id)
    await ctx.send(message)



@commands.register(options=[Option(
    name="circuit",
    description="Circuit to export. Multiple layers and text are not supported yet.",
    type_=SlashCommandOptionType.STRING,
    required=True
)])
async def export(ctx, circuit):
    """
    Exports a circuit to a PNG file.
    """
    try:
        await ctx.defer()
    except:
        pass
    try:
        if circuit == "_":
            for msg in (await ctx.channel.history(limit=50).flatten())[1:]:
                if msg.author.id == bot.user.id and msg.content:
                    message = msg.content
                    break
        elif circuit.startswith("https://discord.com/channels/"):
            message = None
            guildId, chanId, msgId = circuit.split("/")[4:7]
            try:
                chan = await bot.fetch_channel(chanId)
                message = (await ctx.channel.fetch_message(msgId)).content
            except Exception as e:
                await ctx.send("Could not access this message. Either I am not on this server or I do not have access to this channel.")
                return
        else:
            msgId = int(circuit)
            message = (await ctx.channel.fetch_message(msgId)).content
    except Exception as e:
        message = format_msg(circuit, max_length=None)[0]

    @lru_cache
    def get_image(emoji):
        r = requests.get(str(emoji.url), stream=True)
        return Image.open(r.raw).resize((export_size, export_size), resample=0).convert("RGBA")

    grid = []
    line = []
    while message:
        search = re.search(emoji_full_pattern, message)
        if search == None:
            break
        s, e = search.span()
        if s != 0:
            text = message[:s]
            if "\n" in text:
                grid.append(line)
                line = []
        e_name = message[s+2:message.find(":",s+2)]
        if e_name in emojis_dict:
            emoji = emojis_dict[e_name]
            if str(emoji) == message[s:e]:
                line.append(emoji)
        message = message[e:]
    if line:
        grid.append(line)

    m = max(len(line) for line in grid) if len(grid) else 0
    if len(grid) == 0 or m == 0:
        await ctx.send("No circuit found. I'm not just gonna export plain text you know...")
        return
    for i in range(len(grid)):
        while len(grid[i]) < m:
            grid[i].append(emojis_dict[AIR])

    w, h = export_size*len(grid[0]), export_size*len(grid)
    img = Image.new("RGBA", (w, h), color=(54, 57, 63, 0))
    for i, line in enumerate(grid):
        for j, emoji in enumerate(line):
            e = get_image(emoji)
            img.paste(e, (export_size*j, export_size*i), e)

    with BytesIO() as img_bin:
        img.save(img_bin, "PNG")
        img_bin.seek(0)
        file = discord.File(img_bin, "export.png")
        await ctx.send(file=file)



@commands.register()
async def github(ctx):
    """
    Link to the Github of this bot
    """
    embed = discord.Embed(
        title="cmoafr/redstone-emojis",
        url="https://github.com/cmoafr/redstone-emojis",
        description="Here you go :)",
        color=EMBED_COLOR
    )
    embed.set_author(
        name="GitHub",
        url="https://github.com",
        icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
    )
    embed.set_thumbnail(url="https://avatars.githubusercontent.com/u/43421239")
    await ctx.send(embed=embed)



@commands.register(options=[Option(
    name="preset",
    description="Name of the preset you want",
    type_=SlashCommandOptionType.STRING,
    required=True,
    choices=[name for name in presets]
)])
async def preset(ctx, name=None):
    """
    A few preselected systems ready to go!
    """
    if name:
        if name in presets:
            layers = format_msg(presets[name], split=False).split("\n\n")
            await LayersEmbed(ctx, layers, name=name).send()
        else:
            await ctx.send("Unkown preset. Correct values:\n" + ", ".join(presets.keys()))
    else:
        pass # TBD



@commands.register(options=[Option(
    name="server",
    description="Server you want the link of (Optional)",
    type_=SlashCommandOptionType.STRING,
    required=False,
    choices=[name.lower() for name in settings["discord links"]]
)])
async def servers(ctx, server=None):
    """
    Links to other helpful Discord servers
    """
    links = settings["discord links"]
    links = {k.lower():v for k,v in links.items()}
    if server:
        if server in links:
            await ctx.send(links[server])
        else:
            await ctx.send("Unkown server. Correct values:\n" + ", ".join(servers.keys()))
    else:
        embed = discord.Embed(color=EMBED_COLOR)
        for server in links:
            embed.add_field(
                name=server,
                value=links[server],
                inline=False
            )
        await ctx.send(embed=embed)




submission_list = []
async def get_reddit_embed(submission):
    global x, embed, submission_list
    submission_list.append(submission)
    x = submission
    embed = discord.Embed(
        title=submission.title,
        description=submission.selftext,
        url="https://reddit.com"+submission.permalink,
        color=EMBED_COLOR
    )
    author = submission.author
    await submission.load()
    await author.load()
    embed.set_author(
        name=author.name,
        url="https://www.reddit.com/user/"+author.name,
        icon_url=author.icon_img
    )
    if submission.url:
        if submission.media:
            try:
                embed.set_thumbnail(url=submission.media["oembed"]["thumbnail_url"])
            except:
                pass
        elif "/gallery/" in submission.url:
            metadata = submission.media_metadata
            id_ = list(metadata.keys())[0]
            L = metadata[id_]["o"] if "o" in metadata[id_] else metadata[id_]["p"]
            if type(L) == dict:
                L = [L]
            url = L[-1]["u"]
            #url = "https://preview.redd.it/" + id_ + "." + metadata[id_]["m"].split("/")[-1]
            embed.set_image(url=url)
            return embed
        else:
            embed.set_image(url=submission.url)
    embed.set_footer(text=datetime.utcfromtimestamp(submission.created_utc).strftime("Posted %Y/%m/%d %H:%M:%S UTC"))
    return embed





# Run





async def new_reddit_listener(name, channels):
    redstone = await reddit.subreddit(name)
    while not bot.is_ready():
        await asyncio.sleep(1)
    log.info("Connected to r/"+name)

    while True:
        try:
            async for submission in redstone.stream.submissions(skip_existing=True):
                #log.info("r/"+name+":", submission.title)
                try:
                    embed = await get_reddit_embed(submission)
                    for chan_id in channels:
                        await bot.get_channel(chan_id).send(embed=embed)
                except (discord.errors.HTTPException, PrawNotFound):
                    pass
                except Exception as e:
                    log.exception("r/"+name, submission.title, type(e).__name__, e, submission.url)
                    pass # Malformed embed (too long): TODO Shorten if necessary
        except RequestException:
            pass



def run():
    if settings["token"] == "":
        log.exception(RuntimeError("No token found. Please create a bot at https://discord.com/developers/applications and paste the token in the settings file."))
        exit()

    if "reddit" in settings:
        for sub in subreddits:
            asyncio.ensure_future(new_reddit_listener(sub, subreddits[sub]))
    
    try:
        bot.run(settings["token"])
    except discord.errors.LoginFailure:
        log.errror(RuntimeError("Invalid token. Please verify the settings file."))
        exit()
    except Exception as e:
        log.exception(e)





if __name__ == "__main__":
    run()
