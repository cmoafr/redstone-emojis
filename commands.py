import discord

Main = None


    
class Command:
	
    def __init__(self, original):
        message = original.content
        split = message.replace(Main.prefix, "", 1).split(" ")
        command = split[0]
        args = split[1:]
        self.original = original
        self.message = message
        self.command = command
        self.args = args
        self.arg = " ".join(args)

    def to_format(self, text):
        text = text.replace("\\n", "\n")
        for e in Main.emojis:
            text = text.replace(":"+e.name+":", e.str)
        return text

    async def send_msg(self, message, format=False):
        message = message.strip()
        if " -deloriginal" in self.message:
            message = message.replace(" -deloriginal", "")
            await self.original.delete()
        if format:
            message = self.to_format(message)
        split = message.split("\n\n")
        chan = self.original.channel
        for line in split:
            if len(line) > 2000:
                await chan.send("Error: The response is too long.")
                return
        msg = ""
        for line in split:
            if len(msg) + len(line) > 1998:
                await chan.send(msg)
                msg = line
            else:
                msg += "\n\n" + line
        await chan.send(msg)

    async def send_layers(self, layers):
        message = ""
        for i,layer in enumerate(layers):
            if len(layers) != 1:
                message += "\n**__Layer " + str(i+1) + ":__**\n"
            message += layer + "\n\n"
        await self.send_msg(message, True)



class MotherCommand:

    commands = {}

    name = None
    description = ""
    usage = ""
    hide = False
    admin_only = False
    def __init__(self):
        if not self.name:
            self.name = self.__class__.__name__.lower()

    async def run(self, command):
        pass

    def register_command(self, cmd):
        command = cmd()
        if command.name != None and not command.name in self.commands:
            self.commands[command.name] = command

    def register_all_commands(self):
        for c in MotherCommand.__subclasses__():
            self.register_command(c)

    async def execute(self, command):
        if not Main.running:
            return False
        if len(self.commands) == 0:
            self.register_all_commands()
        cmd = self.commands["default"]
        name = command.command
        if name in self.commands:
            cmd = self.commands[name]
        if cmd.admin_only and command.original.author.id != Main.admin_id:
            await command.send_msg("Sorry but you do not have sufficient permission tu run this command.")
            return False
        try:
            await cmd.run(command)
            return True
        except Exception as e:
            Main.turn_off()
            await command.send_msg("Uhhh ... Something went wrong. Sorry.\nBot has been deactivated to prevent further problems.")
            await Main.client.get_channel(Main.debug).send(Main.client.get_user(Main.admin_id).mention + "\nError: " + command.original.jump_url + " " + cmd.name + " " + command.arg + "\n" + str(e))
            raise e
            return False



class Default(MotherCommand):
    hide = True
    async def run(self, command):
        if not command.message.strip().startswith(Main.prefix):
            return
        await command.send_msg("I don't know this command. Use the help command instead to get more help.")

class Categories(MotherCommand):
    description = "Same as `" + Main.prefix + "emojis` but with categorized.\nWarning: It will spam the channel. Please use it somewere appropriate."
    def __init__(self):
        super().__init__()
        self.description = "Same as `" + Main.prefix + PrintEmojis.name + "` but with categorized."
    async def run(self, command):
        for cat in list(Main.categories.keys()):
            message = "\u200b\n__**" + cat + ":**__\n"
            for i,name in enumerate(sorted(list(Main.categories[cat].keys()))):
                for e in Main.emojis:
                    if e.name == name:
                        break
                message += e.str
                if (i+1)%60 == 0:
                    await command.send_msg(message)
                    message = ""
            if message:
                await command.send_msg(message + "\u200b")

class Echo(MotherCommand):
    description = "Formats your message using emojis and sends it back."
    usage = "<message> [-nomention] [-deloriginal]"
    async def run(self, command):
        if command.arg == "":
            await command.send_msg("Cannot send an empty message!")
        await command.send_msg(command.arg, True)

class Help(MotherCommand):
    description = "Shows this message"
    async def run(self, command):
        no_description_placeholder = "\u200b" # Cannot be empty. Default: "\u200b"
        showhidden = "-hidden" in command.message and command.original.author.id == Main.admin_id
        list_ = list(self.commands.keys())
        list_.sort()
        eb = discord.Embed()
        eb.color = discord.Color(0xff0000)
        eb.title = "List of all the commands:"
        for name in list_:
            cmd = self.commands[name]
            if not cmd.hide or showhidden:
                usage = Main.prefix + cmd.name + " " + cmd.usage
                eb.add_field(name=usage, value=(cmd.description or no_description_placeholder), inline=False)
        await command.original.channel.send(embed=eb)

class List(MotherCommand):
    description = "Returns a list of all the presets."
    async def run(self, command):
        list_ = list(Main.presets.keys())
        list_.sort()
        eb = discord.Embed()
        eb.color = discord.Color(0xff0000)
        eb.title = "List of all the presets:"
        eb.description = " | ".join(list_)
        await command.original.channel.send(embed=eb)

class Preset(MotherCommand):
    description = "Search for the corresponding emoji build and sends it."
    usage = "<name>"
    async def run(self, command):
        if len(command.args) != 1:
            await command.send_msg("Argument error. Usage: " + Main.prefix + "preset <name>", True, False)
            return
        name = command.args[0]
        if name in Main.presets:
            await command.send_layers(Main.presets[name])
            return
        await command.send_msg("Sorry. I could not find this preset.\nPlease check the list using the `" + Main.prefix + "list` command.", True)

class PrintEmojis(MotherCommand):
    name = "emojis"
    description = "Print a list of all the emojis.\nWarning: It will spam the channel. Please use it somewere appropriate."
    async def run(self, command):
        message = ""
        for i,e in enumerate(sorted(Main.emojis, key=lambda e: e.name)):
            message += e.str
            if (i+1)%60 == 0:
                message += "\n\n"
        await command.send_msg(message + "\u200b")

class PrintPresets(MotherCommand):
    name = "printpresets"
    description = "Print all the available presets.\nWarning: It will spam the channel. Please use it somewere appropriate."
    hide = True
    async def run(self, command):
        for name in Main.presets:
            await command.send_msg(name + ":")
            await command.send_layers(Main.presets[name])

class Reload(MotherCommand):
    hide = True
    admin_only = True
    async def run(self, command):
        Main.reload()
