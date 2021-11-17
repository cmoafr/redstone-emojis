import discord
from discord.ext.commands import Bot
from discord_slash import SlashCommand
import json
import os



no_prefix = lambda bot, message: '<' if message.content.startswith('>') else '>'
bot = Bot(command_prefix=no_prefix)
slash = SlashCommand(bot, sync_commands=True)



@bot.event
async def on_ready():
    print("Bot ready!")



# TODO: Error handling
if __name__ == "__main__":

    with open("settings.json") as f:
        settings = json.load(f)
    
    for root, dirs, files in os.walk("./cogs"):
        for filename in files:
            if filename.endswith(".py"):
                bot.load_extension("cogs." + filename[:-3])

    bot.run(settings["token"])
