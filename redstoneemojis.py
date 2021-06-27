import discord
import json
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands



no_prefix = lambda bot, message: '<' if message.content.startswith('>') else '>'
bot = commands.Bot(command_prefix=no_prefix)
slash = SlashCommand(bot, sync_commands=True)


@bot.event
async def on_ready():
    global command_list, emojis
    command_list = await manage_commands.get_all_commands(bot.user.id, settings["token"])
    del settings["token"]
    emojis = []
    for guild_id in settings["emojis guilds ids"]:
        emojis += bot.get_guild(guild_id).emojis
    emojis.sort(key=lambda e: e.name)
    print("Connected on {} guilds with {} commands.".format(len(bot.guilds), len(command_list)))





# Commands

@slash.slash(name="help", description="Shows the list of all commands.")
async def help(ctx):
    embed = discord.Embed()
    ordered = sorted(command_list, key=lambda cmd: cmd["name"])
    for cmd in ordered:
        name, description = cmd["name"], cmd["description"]
        embed.add_field(name="/"+name, value=description, inline=False)
    await ctx.send(embed=embed)

@slash.slash(name="emojis", description="Shows all emojis.\nWarning: Will spam. Use in appropriate channel.", guild_ids=[460515591900495873])
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
