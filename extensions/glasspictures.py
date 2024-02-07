# Image processing for Glassbox
import logging
import discord
from discord.ext import commands
import modules.pictures as pictures

logger = logging.getLogger('glassbox')


async def _get_image(ctx: commands.Context, text=''):
    image_url = ''
    if len(ctx.message.attachments) > 1:
        raise LookupError('Too many images attached!')
    elif len(ctx.message.attachments) == 1:
        image_url = ctx.message.attachments[0].url
    elif len(ctx.message.attachments) == 0 and text.startswith('https://'):
        words = text.split(' ')
        image_url = words[0]
        text = ' '.join(words[1:])
    elif ctx.message.reference:
        message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if len(message.attachments) > 1:
            raise LookupError('Too many images attached!')
        elif len(message.attachments) == 1:
            image_url = message.attachments[0].url
        elif len(message.attachments) == 0 and message.content.startswith('https://'):
            words = message.content.split(' ')
            image_url = words[0]
    else:
        raise LookupError('No image provided!')
    return image_url, text


class GlassPictures(commands.Cog):
    """Image-related commands for a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['rdj'])
    async def downey(self, ctx: commands.Context, *, text=''):
        """Robert Downey, Jr. Explaining meme generator.
        Usage: $downey {text}

        Parameters
        ----------
        text : str
            The text to make RDJ say in his explanation.
        """
        try:
            await ctx.message.delete()
            await ctx.typing()
            pic_path = pictures.downey_meme(text)
            await ctx.send(file=discord.File(pic_path))
        except UserWarning as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def inspirational(self, ctx: commands.Context, *, text=''):
        """Inspirational meme generator.\n
        Usage: $inspirational [URL] {top text}|[bottom text]

        This command can take image inputs from\n
          - an attachment to the message that calls this command\n
          - a URL, placed before the text\n
          - the attachment of a message the message that calls this command is in reply to\n
        A pipe character ('|') divides the top row of text from the bottom row.\n
        The bottom row of text (and by extension the pipe character) is optional.\n

        Parameters
        ----------
        text : str
            The top text, optionally prefixed with an image URL or followed by a pipe character ('|') and the bottom
            text.
        """
        try:
            image_url, text = await _get_image(ctx, text)
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
            pic_path = pictures.inspirational_meme(image_url, header, body)
            await ctx.send(file=discord.File(pic_path))
        except (UserWarning, LookupError) as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def caption(self, ctx: commands.Context, *, text=''):
        """Image caption maker.\n
        Usage: $caption [URL] {text}

        This command can take image inputs from\n
          - an attachment to the message that calls this command\n
          - a URL, placed before the caption\n
          - the attachment of a message the message that calls this command is in reply to

        Parameters
        ----------
        text : str
            The text of the caption, optionally prefixed with the URL of the image to caption if that's how the image
            is provided.
        """
        try:
            image_url, text = await _get_image(ctx, text)
        except LookupError as exception:
            await ctx.send(str(exception))
            return
        try:
            await ctx.message.delete()
            await ctx.typing()
            pic_path = pictures.caption(image_url, text)
            await ctx.send(file=discord.File(pic_path))
        except (UserWarning, LookupError) as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def reverse(self, ctx: commands.Context, *, text=''):
        """Reverses a GIF.\n
        Usage: $reverse [URL]

        This command can take image inputs from\n
          - an attachment to the message that calls this command\n
          - a URL\n
          - the attachment of a message the message that calls this command is in reply to

        Parameters
        ----------
        text : str
            Optionally, the URL of the GIF to reverse.
        """
        try:
            image_url, text = await _get_image(ctx, text)
        except LookupError as exception:
            await ctx.send(str(exception))
            return
        try:
            await ctx.message.delete()
            await ctx.typing()
            pic_path = pictures.reverse(image_url)
            await ctx.send(file=discord.File(pic_path))
        except (UserWarning, LookupError) as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def makegif(self, ctx: commands.Context, text=''):
        """Makes a static image a GIF.\n
        Probably useful for PC users who want to save a reaction image to their Favorite GIFs collection.\n
        Usage: $makegif [URL]

        This command can take image inputs from\n
          - an attachment to the message that calls this command\n
          - a URL\n
          - the attachment of a message the message that calls this command is in reply to

        Parameters:
        -----------
        text : str
            Optionally, the URL of the image to make a GIF.
        """
        try:
            image_url, text = await _get_image(ctx, text)
        except LookupError as exception:
            await ctx.send(str(exception))
            return
        try:
            await ctx.typing()
            pic_path = pictures.make_gif(image_url)
            await ctx.send(file=discord.File(pic_path))
        except (UserWarning, LookupError, ValueError) as exception:
            await ctx.send(str(exception))


async def setup(bot):
    await bot.add_cog(GlassPictures(bot))
    logger.info('Loaded image commands!')


async def teardown(bot):
    await bot.remove_cog('GlassPictures')
    logger.info('Unloaded image commands.')
