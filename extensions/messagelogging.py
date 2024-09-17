# Extension to log messages to the log file

import logging
import discord
from discord.ext import commands

logger = logging.getLogger("glassbox")

last_channel = None
last_server = None


class MessageLogger(commands.Cog):
    """Add sent messages to the logging system."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        global last_channel
        if message.channel != last_channel:
            logger.debug(f'{message.guild.name} / #{message.channel.name}')
            last_channel = message.channel
        logger.debug(f'    {message.author.display_name} ({message.author.name}): '
                     f'{sanitize_text(message.clean_content)}')
        if len(message.attachments) > 0:
            logger.debug('     |  Files attached:')
            for attachment in message.attachments:
                logger.debug(f'     |      {attachment.filename} ({attachment.url})')


def sanitize_text(text: str):
    """Take a raw string and replace unwanted characters with spaces.

    Unwanted characters are defined in this function.
    """
    for c in '`\n':
        text = text.replace(c, ' ')
    text = text.strip()
    return text


async def setup(bot):
    await bot.add_cog(MessageLogger(bot))
    logger.info('Loaded message logging!')


async def teardown(bot):
    await bot.remove_cog('MessageLogger')
    logger.info('Unloaded message logging.')
