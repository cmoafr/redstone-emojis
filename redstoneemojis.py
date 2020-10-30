import json
import discord
client = discord.Client()
import commands
from threading import Thread
from os import execv
import sys
main = None





class Emoji:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.url = "https://cdn.discordapp.com/emojis/" + str(id) + ".png"
        self.str = "<:" + name + ":" + str(id) + ">"
        self.category = "Error"
        for cat in Main.categories:
            if self.name in Main.categories[cat]:
                self.category = cat
                break

    def __str__(self):
        return self.str

    def __repr__(self):
        return self.name





class Main:

    categories = {}
    emojis = {}

    def get_settings(self):
        global token
        with open("categories.json", "r") as f:
            self.categories = json.load(f)
        with open("settings.json", "r") as f:
            d = json.load(f)
            self.prefix = d["prefix"]
            self.admin_id = d["admin-id"]
            self.debug = d["debug-channel-id"]
            

    def on_enable(self):
        global prefix, client
        self.get_settings()
        self.client = client
        self.get_all_emojis()
        self.get_all_presets()
        client.get_all_members()
        self.running = True

    def on_disable(self):
        try:
            client.logout()
        except e:
            pass

    def reload(self):
        print("Reloading")
        self.turn_off()
        execv(__file__, sys.argv)
        sys.exit()

    def turn_off(self):
        global running
        running = False
        self.running = False


        
    def get_all_emojis(self):
        global emojiList, emojisCategorized
        sortedEmojiList = sorted(client.emojis, key=lambda e : e.name)
        emojiList = []
        emojisCategorized = {}
        for de in sortedEmojiList:
            if de.guild.name.startswith("red emojis "):
                name = de.name
                short = name[0]
                e = Emoji(name, de.id)
                emojiList.append(e)
                if not short in emojisCategorized:
                    emojisCategorized[short] = {}
                emojisCategorized[short][name] = e.url
        self.emojis = emojiList
        self.emojisCategorized = emojisCategorized

    def get_all_presets(self):
        with open("presets.json", "r") as f:
            self.presets = json.load(f)

    def __init__(self, client):
        commands.Main = self
        self.on_enable()





@client.event
async def on_ready():
    global main, msg
    print('Logged in as {0} on {1} guilds.'.format(client.user, len(client.guilds)))
    with open("settings.json", "r") as f:
        await client.change_presence(activity=discord.Activity(name="for " + json.load(f)["prefix"] + "help", type=discord.ActivityType.watching), status=discord.Status.online)
    main = Main(client)

@client.event
async def on_message(event):
    if main == None or not main.running or event.author.bot:
        return
    if event.content.startswith(main.prefix):
        cmd = commands.Command(event)
        if await commands.MotherCommand().execute(cmd):
            return



if __name__ == "__main__":
    try:
        with open("settings.json", "r") as f:
            token = json.load(f)["token"]
        thread = Thread(target=client.run(token))
        del token
        thread.start()
    except:
        raise
