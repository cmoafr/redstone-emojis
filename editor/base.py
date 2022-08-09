import discord
from discord.ext import commands

from functools import lru_cache
from io import BytesIO
from PIL import Image, ImageOps
import requests
from typing import Optional, Tuple

from utils.config import get_config
from utils.shareability import Shareability

BLOCK_SIZE = 64
BORDER_SIZE = 1
INVERT_SIZE = 8

BACKGROUND_COLOR = (54, 57, 63, 0)
BORDER_COLOR = (255, 255, 255, 128)
RENDER_DISTANCE = 5

NONE = "Air"
DEFAULT = "Block"

class BaseView(discord.ui.View):
    def __init__(self, bot: commands.Bot, shareability: Shareability, user_id: int) -> None:
        self.bot = bot
        self.shareability = shareability
        self.user_id = user_id
        self.blocks = get_config("emojis", with_default=False)
        self.block = DEFAULT
        self.x, self.y = 0, 0
        self.grid = {} # (x, y) -> Block (emoji id)
        super().__init__()

    def is_allowed(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator or interaction.user.id in self.bot.config["admin ids"]:
            return True # Bypass Shareability
        return self.shareability != Shareability.VISIBLE or interaction.user.id == self.user_id

    @lru_cache(maxsize=64)
    def get_emoji(self, block: Optional[str] = None, size: int = 16) -> Image.Image:
        if block is None:
            block = self.block
        emoji = self.bot.get_emoji(block)

        if emoji is None:
            self.bot.logger.warning(f"No emoji found with id {block}")
            return Image.new("RGBA", (size, size), BACKGROUND_COLOR)
        
        r = requests.get(str(emoji.url), stream=True)
        return Image.open(r.raw).convert("RGBA").resize((size, size), resample=0)

    #@lru_cache(maxsize=64)
    def process_emoji(self, image: Image.Image, grid_color: Tuple[int, int, int, int], grid_width: int = 1, invert_border_size: int = 0) -> Image.Image:

        # Create border
        if grid_width:
            end = image.width - grid_width
            bg = Image.new("RGBA", image.size, grid_color)
            bg.paste(BACKGROUND_COLOR, (grid_width, grid_width, end, end))
            bg.paste(image, mask=image)
            image = bg

        # Invert the border
        if invert_border_size:
            cropped = image.crop((invert_border_size, invert_border_size, image.width - invert_border_size, image.height - invert_border_size))
            image = ImageOps.invert(image.convert("RGB")).convert("RGBA")
            image.paste(cropped, (invert_border_size, invert_border_size))

        return image

    def get_image(self, render_distance: int = RENDER_DISTANCE, block_size: int = BLOCK_SIZE, border_size: int = BORDER_SIZE, invert_size: int = INVERT_SIZE, expand_cursor: bool = True) -> Image.Image:

        if self.grid:
            # Get the grid bounds
            min_x = min(self.grid, key=lambda x: x[0])[0]
            min_y = min(self.grid, key=lambda x: x[1])[1]
            max_x = max(self.grid, key=lambda x: x[0])[0]
            max_y = max(self.grid, key=lambda x: x[1])[1]

            # Expand to curor
            if expand_cursor:
                min_x = min(min_x, self.x)
                min_y = min(min_y, self.y)
                max_x = max(max_x, self.x)
                max_y = max(max_y, self.y)

        else:
            min_x, min_y, max_x, max_y = self.x, self.y, self.x, self.y

        # Clamp to the render distance
        min_x = max(min_x, self.x - render_distance)
        max_x = min(max_x, self.x + render_distance) + 1
        min_y = max(min_y, self.y - render_distance)
        max_y = min(max_y, self.y + render_distance) + 1

        # Create the image
        image = Image.new(
            "RGBA",
            (
                block_size * (max_x - min_x),
                block_size * (max_y - min_y)
            ),
            BACKGROUND_COLOR
        )

        for x in range(min_x, max_x):
            for y in range(min_y, max_y):

                block = self.grid.get((x, y), self.blocks[NONE])
                invert = x == self.x and y == self.y
                emoji = self.get_emoji(block, block_size)
                emoji = self.process_emoji(emoji, BORDER_COLOR, (not invert)*border_size, invert*invert_size)

                image.paste(
                    emoji, (
                    (x - min_x) * block_size,
                    (y - min_y) * block_size
                ))
        
        return image
    
    async def send(self, interaction: discord.Interaction) -> None:
        image = self.get_image()
        with BytesIO() as image_bin:
            image.save(image_bin, "PNG")
            image_bin.seek(0)
            file = discord.File(image_bin, filename="circuit.png")

        try:
            if interaction.command is None:
                # This wasn't a command so we edit the message
                # to prevent spamming the channel
                await interaction.response.edit_message(content=None, view=self, attachments=[file])
            else:
                await interaction.response.send_message(view=self, file=file, ephemeral=self.shareability == Shareability.PRIVATE)
        except discord.NotFound:
            self.bot.logger.warn("Unkown interaction " + str(interaction.id))
        await self.wait()
