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





# Run

try:
    with open("settings.json") as f:
        settings = json.load(f)
except FileNotFoundError:
    with open("settings.json", "w") as f:
        f.write("""{
    \"token\": \"INSERT YOUR TOKEN HERE\"
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
