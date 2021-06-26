import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext



bot = commands.Bot("")
slash = SlashCommand(bot)



@bot.event
async def on_ready():
    print("Connected")

@bot.event
async def on_message(event):
    print("Message received")

"""
@slash.slash(name="example")
async def example(event, arg=None):
    print("Example command received")
"""





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
