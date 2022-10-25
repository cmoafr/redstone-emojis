import discord
from discord.ext import commands

import asyncio
import asyncpraw
from datetime import datetime

from utils.config import get_config

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reddit(bot))

class Reddit(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.reddit: asyncpraw.Reddit = None
        self.tasks: list[asyncio.Task] = []

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.logger.info("Cog template ready!")

    async def cog_load(self):
        self.reddit = self.create_reddit()
        self.tasks = []
        for subreddit, channels in get_config("reddit").items():
            try:
                self.tasks.append(
                    asyncio.create_task(self.listen(subreddit, channels))
                )
            except Exception as e:
                self.bot.logger.error(e)

    async def cog_unload(self):
        for task in self.tasks:
            task.cancel()
            while not task.done():
                await asyncio.sleep(0.1)
        await self.reddit.close()

    async def listen(self, subreddit: str, channel_ids: list[int]) -> None:
        sub = await self.reddit.subreddit(subreddit)
        channels = []
        async for guild in self.bot.fetch_guilds():
            for chan in (await guild.fetch_channels()):
                if chan.id in channel_ids:
                    channels.append(chan)
        
        self.bot.logger.info("Listening on: r/"+subreddit)
        async for submission in sub.stream.submissions(skip_existing=True):
            try:
                self.bot.logger.debug(f"r/{subreddit}: {submission.title}")
                await self.send(submission, channels)
            except Exception as e:
                self.bot.logger.error(e)

    async def send(self, submission: asyncpraw.reddit.Submission, channels: list[discord.TextChannel]) -> None:
        embed = discord.Embed(
            title=submission.title,
            url=submission.shortlink,
            color=0xFF4500,
            description=submission.selftext
        )
        await submission.author.load() # Load the author icon
        embed.set_author(name=submission.author.name, icon_url=submission.author.icon_img)
        embed.set_image(url=submission.url)
        embed.timestamp = datetime.utcfromtimestamp(submission.created_utc)
        await submission.subreddit.load() # Load the sub name
        embed.set_footer(text="r/"+submission.subreddit.display_name)

        for channel in channels:
            try:
                await channel.send(embed=embed)
            except:
                pass # Missing permissions

    def create_reddit(self) -> asyncpraw.Reddit:
        reddit = asyncpraw.Reddit(
            client_id=self.bot.config["reddit id"],
            client_secret=self.bot.config["tokens"]["reddit"],
            user_agent=self.bot.config["reddit user agent"]
        )
        return reddit
