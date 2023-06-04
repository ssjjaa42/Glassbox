# Dad jokes for Glassbox
import logging
import discord
from discord.ext import commands
from modules.father import *
from modules.settings import forbidden

logger = logging.getLogger('glassbox')

class GlassFather(commands.Cog):
    """Give a Discord Bot dad jokes."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Do nothing if the message is from us or another bot
        if message.author.bot:
            return
        # Keep out of forbidden channels
        if message.channel.id in forbidden():
            return
        # Be dad
        if triggers_dad(message.content):
            try:
                name = parse_name(message.content)
                my_name = message.guild.me.nick if message.guild.me.nick else self.bot.user.name
                await message.channel.send(f'Hi {name}, I\'m {my_name}!')
            except ValueError:
                pass

async def setup(bot):
    await bot.add_cog(GlassFather(bot))
    logger.info('Loaded dad jokes!')

async def teardown(bot):
    await bot.remove_cog('GlassFather')
    logger.info('Unloaded dad jokes.')
