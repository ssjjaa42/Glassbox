# Image processing for Glassbox
import discord
from discord.ext import commands
from modules.settings import *

class GlassSettings(commands.Cog):
    """User configuration commands for a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def allow(self, ctx: discord.ext.commands.Context):
        """Allow the bot to do things in a the channel this command was invoked from."""
        if not (ctx.message.author.guild_permissions.manage_channels or ctx.message.author.guild_permissions.administrator):
            await ctx.send('You need to have the Manage Channels permission to change this setting.')
            return
        try:
            remove_forbidden(ctx.channel.id)
            await ctx.send('This channel is now off the blacklist.')
        except IndexError as exception:
            await ctx.send(str(exception))
    
    @commands.command()
    async def deny(self, ctx: discord.ext.commands.Context):
        """Ban the bot from doing things in the channel this command was invoked from."""
        if not (ctx.message.author.guild_permissions.manage_channels or ctx.message.author.guild_permissions.administrator):
            await ctx.send('You need to have the Manage Channels permission to change this setting.')
            return
        try:
            add_forbidden(ctx.channel.id)
            await ctx.send('This channel is now on the blacklist.')
        except IndexError as exception:
            await ctx.send(str(exception))


async def setup(bot):
    await bot.add_cog(GlassSettings(bot))
    print('Loaded configuration commands!')
