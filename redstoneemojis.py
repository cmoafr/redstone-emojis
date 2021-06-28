import discord
import json
import re
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands



no_prefix = lambda bot, message: '<' if message.content.startswith('>') else '>'
bot = commands.Bot(command_prefix=no_prefix)
slash = SlashCommand(bot, sync_commands=True)

emoji_full_pattern = re.compile("<:[a-zA-Z0-9]{2,32}:[0-9]*>")
emoji_pattern = re.compile(":[a-zA-Z0-9]{2,32}:")




@bot.event
async def on_ready():
    command_list = await manage_commands.get_all_commands(bot.user.id, settings["token"])
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
    
    print("Connected on {} guilds with {} commands.".format(len(bot.guilds), len(command_list)))





# Commands

@slash.slash(name="help", description="Shows the list of all commands.")
async def help(ctx):
    ordered = sorted(command_list, key=lambda cmd: cmd["name"])
    embed = discord.Embed(
        title="Commands:",
        color=0xff0000
    )
    for cmd in ordered:
        embed.add_field(
            name="/" + cmd["name"],
            value=cmd["description"],
            inline=False
        )
    await ctx.send(embed=embed)



@slash.slash(name="echo", description="Send back the message with the correct format.", options=[
    manage_commands.create_option(name="message", description="Message to be formated and echoed back", option_type=3, required=True)
])
async def echo(ctx, message):
    
    formated = ""
    re_all = [(x.start(), x.end()) for x in re.finditer(":[a-zA-Z0-9_]{2,32}:", message)]
    re_formated = [(x.start(), x.end()) for x in re.finditer("<:[a-zA-Z0-9_]{2,32}:[0-9]*>", message)]
    index = 0

    # Replace emojis
    for start, end in re_all:
        for start_, end_ in re_formated:
            if start >= start_ and end <= end_: # Is formated
                sub = message[start_+2:end_-1]
                name, id_ = sub.split(":")
                if name in emojis_dict and emojis_dict[name].id == int(id_): # Is known
                    formated += message[index:end_]
                else: # Is unkown
                    formated += message[index:start_] + ":" + name + ":"
                index = end_
                break
        else: # Is not formated
            name = message[start+1:end-1]
            if name in emojis_dict: # Is known
                formated += message[index:start] + "<:" + name + ":" + str(emojis_dict[name].id) + ">"
            else: # Is unkown
                formated += message[index:end]
            index = end
    if index < len(message):
        formated += message[index:]
    
    formated = formated.replace("\\n", "\n")
    await ctx.send(formated)



@slash.slash(name="emojis", description="Shows all emojis.\nWarning: Will spam. Use in appropriate channel.")
async def emojis(ctx):
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



@slash.slash(name="github", description="Link to the Github of this bot")
async def github(ctx):
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





# Run

try:
    with open("settings.json") as f:
        settings = json.load(f)
except FileNotFoundError:
    with open("settings.json", "w") as f:
        f.write("""{
    \"token\": \"INSERT YOUR TOKEN HERE\"
    \"emojis guilds ids\": []
}""")
    raise FileNotFoundError("Settings file not found. Please put your Discord bot token in the newly created file.")

if settings["token"] == "":
    raise RuntimeError("No token found. Please create a bot at https://discord.com/developers/applications and paste the token in the settings file.")

try:
    bot.run(settings["token"])
except discord.errors.LoginFailure:
    raise RuntimeError("Invalid token. Please verify the settings file.")
except Exception as e:
    raise e
