import discord
import json
import re
from discord.ext.commands import Bot
from discord_slash import SlashCommand, SlashContext, SlashCommandOptionType
from discord_slash.utils import manage_commands



EMPTY = "\u200b"

no_prefix = lambda bot, message: '<' if message.content.startswith('>') else '>'

emoji_full_pattern = re.compile("<:[a-zA-Z0-9_]{2,32}:[0-9]*>")
emoji_pattern = re.compile(":[a-zA-Z0-9_]{2,32}:")





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



def format_msg(message):
    if len(message) == 0:
        return EMPTY

    # Convert layers
    if type(message) in (list, tuple):
        if type(message[0]) == str:
            message = [message]
        if len(message) == 1:
            string = "\n".join(message[0])
        else:
            layers = []
            for i, list_ in enumerate(message):
                layer = "**Layer " + str(i+1) + ":**\n"
                layer += "\n".join(list_)
                layers.append(layer)
            string = "\n\n".join(layers)
    else:
        string = message
    
    formated = ""
    re_all = [(x.start(), x.end()) for x in re.finditer(":[a-zA-Z0-9_]{2,32}:", string)]
    re_formated = [(x.start(), x.end()) for x in re.finditer("<:[a-zA-Z0-9_]{2,32}:[0-9]*>", string)]
    index = 0

    # Replace emojis
    for start, end in re_all:
        for start_, end_ in re_formated:
            if start >= start_ and end <= end_: # Is formated
                sub = string[start_+2:end_-1]
                name, id_ = sub.split(":")
                if name in emojis_dict and emojis_dict[name].id == int(id_): # Is known
                    formated += string[index:end_]
                else: # Is unkown
                    formated += string[index:start_] + ":" + name + ":"
                index = end_
                break
        else: # Is not formated
            name = string[start+1:end-1]
            if name in emojis_dict: # Is known
                formated += string[index:start] + "<:" + name + ":" + str(emojis_dict[name].id) + ">"
            else: # Is unkown
                formated += string[index:end]
            index = end
    if index < len(string):
        formated += string[index:]
    
    formated = formated.replace("\\n", "\n").strip()
    split = []
    indexes = [0]
    for i in range(len(formated)):
        if formated[i:i+2] == "\n\n":
            if i - indexes[-1] >= 2000:
                return ["Message is too long and could not be sent."]
            if i - indexes[0] >= 2000:
                a, b = indexes[0], indexes[-1]
                split.append(formated[a:b].strip())
                indexes = [indexes[-1]]
            indexes.append(i)
    split.append(formated[indexes[0]:].strip())
    return split





bot = Bot(command_prefix=no_prefix)
slash = SlashCommand(bot, sync_commands=True)
commands = Commands(slash)

default_settings = '''{
    "token": "INSERT YOUR TOKEN HERE"
    "emojis guilds ids": [],
    "discord links": {
        "Bot": "https://discord.gg/e5Jag3kuxq"
    }
}'''



try:
    with open("settings.json") as f:
        settings = json.load(f)
except FileNotFoundError:
    with open("settings.json", "w") as f:
        f.write()
    raise FileNotFoundError("Settings file not found. Please put your Discord bot token in the newly created file.")



try:
    with open("presets.json") as f:
        presets = json.load(f)
except FileNotFoundError:
    presets = {"and":[[":hd::g1::j1::g0::g0::g0::g0:",":g0::g0::fk::eb::g1::j6::hx:",":hd::g1::j1::g0::g0::g0::g0:"]]}





@bot.event
async def on_ready():
    global emojis, emojis_dict
    commands_list = await manage_commands.get_all_commands(bot.user.id, settings["token"])
    del settings["token"]

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
    
    print("Connected on {} guilds with {} ({}) commands.".format(len(bot.guilds), len(commands.list), len(commands_list)))





# Commands

@commands.register()
async def help(ctx):
    """
    Shows the list of all commands
    """
    global embed
    ordered = sorted(commands.list, key=lambda cmd: cmd.name)
    embed = discord.Embed(
        title="Commands:",
        color=0xff0000
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



@commands.register()
async def github(ctx):
    """
    Link to the Github of this bot
    """
    embed = discord.Embed(
        title="cmoafr/redstone-emojis",
        url="https://github.com/cmoafr/redstone-emojis",
        description="Here you go :)",
        color=0xff0000
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
            split = format_msg(presets[name])
            for msg in split:
                await ctx.send(msg)
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
        embed = discord.Embed(color=0xff0000)
        for server in links:
            embed.add_field(
                name=server,
                value=links[server],
                inline=False
            )
        await ctx.send(embed=embed)





# Run

if settings["token"] == "":
    raise RuntimeError("No token found. Please create a bot at https://discord.com/developers/applications and paste the token in the settings file.")

try:
    bot.run(settings["token"])
except discord.errors.LoginFailure:
    raise RuntimeError("Invalid token. Please verify the settings file.")
except Exception as e:
    raise e
