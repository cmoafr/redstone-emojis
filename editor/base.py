import discord

from functools import lru_cache
from io import BytesIO
from PIL import Image, ImageOps
import requests

from utils.config import get_config

BLOCK_SIZE = 64
BORDER_SIZE = 8
RENDER_DISTANCE = 5

class BaseView(discord.ui.View):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.blocks = get_config("blocks")
        self.block = self.blocks["iron_block"]
        self.x, self.y = 0, 0
        self.grid = {} # (x, y) -> Block
        super().__init__()

    @lru_cache(maxsize=64)
    def get_emoji(self, block=None, size=16, invert_border=False, border_size=1):
        if block is None:
            block = self.block

        # Get the image
        emoji = self.bot.get_emoji(block)
        if emoji is None:
            image = Image.new("RGBA", (size, size), (54, 57, 63, 0))
            self.bot.logger.warning(f"No emoji found with id {block}")
        else:
            r = requests.get(str(emoji.url), stream=True)
            image = Image.open(r.raw)
        image = image.convert("RGBA").resize((size, size), resample=0)

        # Invert the border
        if invert_border:
            cropped = image.crop((border_size, border_size, image.width - border_size, image.height - border_size))
            image = ImageOps.invert(image.convert("RGB")).convert("RGBA")
            image.paste(cropped, (border_size, border_size))
        
        return image

    def get_image(self):
        if self.grid:
            # Get the grid bounds
            min_x = min(self.grid, key=lambda x: x[0])[0]
            min_y = min(self.grid, key=lambda x: x[1])[1]
            max_x = max(self.grid, key=lambda x: x[0])[0]
            max_y = max(self.grid, key=lambda x: x[1])[1]

            # Expand to curor
            min_x = min(min_x, self.x)
            min_y = min(min_y, self.y)
            max_x = max(max_x, self.x)
            max_y = max(max_y, self.y)

        else:
            min_x, min_y, max_x, max_y = self.x, self.y, self.x, self.y

        # Clamp to the render distance
        min_x = max(min_x, self.x - RENDER_DISTANCE)
        max_x = min(max_x, self.x + RENDER_DISTANCE) + 1
        min_y = max(min_y, self.y - RENDER_DISTANCE)
        max_y = min(max_y, self.y + RENDER_DISTANCE) + 1

        # Create the image
        image = Image.new(
            "RGBA", (
            BLOCK_SIZE * (max_x - min_x),
            BLOCK_SIZE * (max_y - min_y)
        ))
        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                block = self.grid.get((x, y), self.blocks["air"])
                invert = x == self.x and y == self.y
                emoji = self.get_emoji(block, BLOCK_SIZE, invert, BORDER_SIZE)
                image.paste(
                    emoji, (
                    (x - min_x) * BLOCK_SIZE,
                    (y - min_y) * BLOCK_SIZE
                ))
        
        return image
    
    async def send(self, interaction: discord.Interaction):
        image = self.get_image()
        with BytesIO() as image_bin:
            image.save(image_bin, "PNG")
            image_bin.seek(0)
            file = discord.File(image_bin, filename="circuit.png")

        if interaction.command is None:
            # This wasn't a command so we edit the message
            # to prevent spamming the channel
            await interaction.response.edit_message(view=self, attachments=[file])
        else:
            await interaction.response.send_message(view=self, file=file, ephemeral=True)
        await self.wait()
