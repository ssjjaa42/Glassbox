# Image processing for Glassbox
import logging
import discord
from discord.ext import commands
from modules.pictures import *

logger = logging.getLogger('glassbox')

class GlassPictures(commands.Cog):
    """Image-related commands for a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    async def _get_image(self, ctx: commands.Context, text=''):
        if len(ctx.message.attachments) > 1:
            raise LookupError('Too many images attached!')
        elif len(ctx.message.attachments) == 1:
            image_url = str(ctx.message.attachments[0])
        elif len(ctx.message.attachments) == 0 and text.startswith('https://'):
            words = text.split(' ')
            image_url = words[0]
            text = ' '.join(words[1:])
        elif ctx.message.reference:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if len(message.attachments) > 1:
                raise LookupError('Too many images attached!')
            elif len(message.attachments) == 1:
                image_url = str(message.attachments[0])
            elif len(message.attachments) == 0 and message.content.startswith('https://'):
                words = message.content.split(' ')
                image_url = words[0]
        else:
            raise LookupError('No image provided!')
        return (image_url, text)

    @commands.command()
    async def downey(self, ctx: commands.Context, *, text=''):
        """Robert Downey, Jr. Explaining meme generator."""
        try:
            await ctx.message.delete()
            await ctx.typing()
            pic_path = downey_meme(text)
            await ctx.send(file=discord.File(pic_path))
        except UserWarning as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def inspirational(self, ctx: commands.Context, *, text=''):
        """Inspirational meme generator.

        Can take image inputs from an attachment or a direct URL at the start of the command invocation.
        A pipe character ('|') divides the top row of text from the bottom row.
        The bottom row of text (and the pipe character) is optional.
        """
        try:
            image_url, text = await self._get_image(ctx, text)
        except LookupError as exception:
            await ctx.send(str(exception))
            return
        parts = text.split('|')
        header = parts[0].strip()
        body = ''
        if len(parts) > 1:
            body = parts[1].strip()
        try:
            await ctx.message.delete()
            await ctx.typing()
            pic_path = inspirational_meme(image_url, header, body)
            await ctx.send(file=discord.File(pic_path))
        except UserWarning as exception:
            await ctx.send(str(exception))
        

    @commands.command()
    async def caption(self, ctx: commands.Context, *, text=''):
        """Image and gif caption maker.

        Can take image inputs from an attachment or a direct URL at the start of the command invocation.
        Tenor GIFs are also OK.
        """
        try:
            image_url, text = await self._get_image(ctx, text)
        except LookupError as exception:
            await ctx.send(str(exception))
            return
        try:
            await ctx.message.delete()
            await ctx.typing()
            pic_path = caption(image_url, text)
            await ctx.send(file=discord.File(pic_path))
        except UserWarning as exception:
            await ctx.send(str(exception))

async def setup(bot):
    await bot.add_cog(GlassPictures(bot))
    logger.info('Loaded image commands!')

async def teardown(bot):
    await bot.remove_cog('GlassPictures')
    logger.info('Unloaded image commands.')
