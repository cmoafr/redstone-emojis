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
    
    def equal(self, e1, e2):
        e1 = self.get(e1) or e1
        e2 = self.get(e2) or e2
        return e1 == e2