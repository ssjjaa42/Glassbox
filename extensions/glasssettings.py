# Settings for Glassbox
import logging as top_log
from datetime import datetime
import discord
from discord.ext import commands
from modules.settings import *

logger = top_log.getLogger('glassbox')


class GlassSettings(commands.Cog):
    """User configuration commands for a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def allow(self, ctx: commands.Context):
        """Allow the bot to do things in the channel this command was invoked from."""
        if not ctx.message.author.guild_permissions.manage_channels \
                and not ctx.message.author.guild_permissions.administrator:
            await ctx.send('You need to have the Manage Channels permission to change this setting.')
            return
        try:
            remove_forbidden(ctx.channel.id)
            await ctx.send('This channel is now off the blacklist.')
        except IndexError as exception:
            await ctx.send(str(exception))
    
    @commands.command()
    async def deny(self, ctx: commands.Context):
        """Ban the bot from doing things in the channel this command was invoked from."""
        if not ctx.message.author.guild_permissions.manage_channels \
                and not ctx.message.author.guild_permissions.administrator:
            await ctx.send('You need to have the Manage Channels permission to change this setting.')
            return
        try:
            add_forbidden(ctx.channel.id)
            await ctx.send('This channel is now on the blacklist.')
        except IndexError as exception:
            await ctx.send(str(exception))
    
    @commands.command()
    async def log(self, ctx: commands.Context):
        """Tell the bot to record edited messages and deleted messages in the channel this command was invoked from."""
        if not ctx.message.author.guild_permissions.administrator \
                and not ctx.message.author.guild_permissions.manage_server:
            await ctx.send('You need to have the Manage Server permission to change this setting.')
            return
        try:
            add_logging(ctx.guild.id, ctx.channel.id)
            await ctx.send('Now logging edits and deletions to this channel.')
        except IndexError as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def unlog(self, ctx: commands.Context):
        """Tell the bot to stop recording edits and deletions for this server."""
        if not ctx.message.author.guild_permissions.administrator \
                and not ctx.message.author.guild_permissions.manage_server:
            await ctx.send('You need to have the Manage Server permission to change this setting.')
            return
        try:
            clear_logging(ctx.guild.id)
            await ctx.send('I\'m no longer logging edits and deletions in this server.')
            await ctx.send('Hi No longer logging edits and deletions, I\'m--')
        except IndexError as exception:
            await ctx.send(str(exception))

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not str(after.guild.id) in logging():
            return
        embed = discord.Embed(title='Message Edit')
        embed.description = f'[Link to message]({after.jump_url})'
        embed.add_field(name='Channel', value=after.channel.mention, inline=False)
        embed.add_field(name='Original Message', value=before.clean_content)
        for attachment in before.attachments:
            embed.add_field(name=f'Attachment: {attachment.filename}', value=attachment.url, inline=False)
        embed.add_field(name='Edited Message', value=after.clean_content)
        for attachment in after.attachments:
            embed.add_field(name=f'Attachment: {attachment.filename}', value=attachment.url, inline=False)
        embed.set_footer(text=f'{after.author.name}#{after.author.discriminator} • '
                              f'{after.edited_at.strftime("%m/%d/%Y %I:%M %p")}', icon_url=after.author.avatar.url)
        await self.bot.get_channel(logging()[str(after.guild.id)]).send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not str(message.guild.id) in logging():
            return
        embed = discord.Embed(title='Message Delete')
        embed.add_field(name='Channel', value=message.channel.mention, inline=False)
        embed.add_field(name='Original Message', value=message.clean_content)
        for attachment in message.attachments:
            embed.add_field(name=f'Attachment: {attachment.filename}', value=attachment.url, inline=False)
        embed.set_footer(text=f'{message.author.name}#{message.author.discriminator} • '
                              f'{datetime.utcnow().strftime("%m/%d/%Y %I:%M %p")}', icon_url=message.author.avatar.url)
        await self.bot.get_channel(logging()[str(message.guild.id)]).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        logger.info(f'glasssettings: Removed from guild {guild}! Clearing settings for this guild...')
        try:
            clear_logging(guild.id)
        except IndexError:
            pass
        for channel in guild.channels:
            try:
                remove_forbidden(channel.id)
            except IndexError:
                pass


async def setup(bot):
    await bot.add_cog(GlassSettings(bot))
    logger.info('Loaded configuration commands!')


async def teardown(bot):
    await bot.remove_cog('GlassSettings')
    save()
    logger.info('Unloaded configuration commands.')
