# Image processing for Glassbox
import discord
from discord.ext import commands
from modules.pictures import *

class GlassPictures(commands.Cog):
    """Image-related commands for a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def downey(self, ctx: discord.ext.commands.Context, *, text=''):
        """Robert Downey, Jr. Explaining meme generator."""
        try:
            pic_path = downey_meme(text)
            await ctx.message.delete()
            await ctx.send(file=discord.File(pic_path))
        except UserWarning as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def inspirational(self, ctx: discord.ext.commands.Context, *, text=''):
        """Inspirational meme generator.

        Can take image inputs from an attachment or a direct URL at the start of the command invocation.
        A pipe character ('|') divides the top row of text from the bottom row.
        The bottom row of text (and the pipe character) is optional.
        """
        if len(ctx.message.attachments) > 1:
            await ctx.send('Too many images attached!')
            return
        elif len(ctx.message.attachments) == 1:
            image_url = str(ctx.message.attachments[0])
        elif len(ctx.message.attachments) == 0 and text.startswith('https://'):
            words = text.split(' ')
            image_url = words[0]
            words.pop(0)
            text = ' '.join(words)
        else:
            await ctx.send('No image provided!')
            return
        parts = text.split('|')
        header = parts[0].strip()
        body = ''
        if len(parts) > 1:
            body = parts[1].strip()
        try:
            await ctx.message.delete()
            async with ctx.typing():
                pic_path = inspirational_meme(image_url, header, body)
            await ctx.send(file=discord.File(pic_path))
        except UserWarning as exception:
            await ctx.send(str(exception))


async def setup(bot):
    await bot.add_cog(GlassPictures(bot))
    print('Loaded image commands!')
