import discord

class Emojis:

    def __init__(self, emojis):
        self.emojis = emojis

    def get(self, emoji):
        if type(emoji) == discord.Emoji:
            return emoji
        
        elif type(emoji) == int:
            for e in self.emojis:
               if e.id == emoji:
                   return e

        elif type(emoji) == str:
            for e in self.emojis:
                if e.name == emoji:
                    return e

        return None