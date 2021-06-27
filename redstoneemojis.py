import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands



bot = commands.Bot(command_prefix=None)
slash = SlashCommand(bot, sync_commands=True)
token = None


@bot.event
async def on_ready():
    global command_list, token
    command_list = await manage_commands.get_all_commands(bot.user.id, token)
    del token
    print("Connected on {} guilds with {} commands.".format(len(bot.guilds), len(command_list)))





# Commands

@slash.slash(name="help", description="Shows the list of all commands.")
async def _help(ctx, guild_ids=[460515591900495873]):
    embed = discord.Embed()
    ordered = sorted(command_list, key=lambda cmd: cmd["name"])
    for cmd in ordered:
        name, description = cmd["name"], cmd["description"]
        embed.add_field(name="/"+name, value=description, inline=False)
    await ctx.send(embed=embed)





# Run

try:
    with open("token") as f:
        token = f.read()
except FileNotFoundError:
    with open("token", "w"):
        pass
    raise FileNotFoundError("Token file not found. Please put your Discord bot token in the newly created file.")

if token == "":
    raise RuntimeError("No token found. Please create a bot at https://discord.com/developers/applications and paste the token in the corresponding file.")

try:
    bot.run(token)
except discord.errors.LoginFailure:
    raise RuntimeError("Invalid token. Please verify the \"token\" file.")
