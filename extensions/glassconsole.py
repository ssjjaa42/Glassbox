# Console commands for Glassbox
import os
import logging
import discord
from discord.ext import commands
from modules.console import Console

logger = logging.getLogger('glassbox')

class GlassConsole(commands.Cog):
    """Console-related commands for a Discord bot."""

    def __init__(self, bot):
        self.bot = bot
        self._consoles = {}
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Sets up the data folder when joining a new server."""
        root_path = os.path.join(os.path.curdir, 'data', 'serverfiles')
        target_path = os.path.join(root_path, str(guild.id))
        if not os.path.exists(target_path):
            os.mkdir(target_path)

    @commands.command()
    async def mkdir(self, ctx, *, name):
        """Try to make a new directory."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            self._consoles[ctx.guild.id].mkdir(name, ctx.author.id)
            await ctx.send(f'Folder created.')
        except PermissionError as exception:
            await ctx.send(exception)

    @commands.command()
    async def rmdir(self, ctx, *, path):
        """Try to delete a directory."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            self._consoles[ctx.guild.id].rmdir(path, ctx.author.id)
            await ctx.send(f'Folder deleted.')
        except (NotADirectoryError, PermissionError) as exception:
            await ctx.send(exception)
    
    @commands.command()
    async def rm(self, ctx, *, path):
        """Try to delete a file."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)
        try:
            self._consoles[ctx.guild.id].rm(path, ctx.author.id)
            await ctx.send(f'File deleted.')
        except IsADirectoryError:
            try:
                self._consoles[ctx.guild.id].rmdir(path, ctx.author.id)
                await ctx.send(f'Folder deleted.')
            except (NotADirectoryError, PermissionError) as exception:
                await ctx.send(exception)
        except (FileNotFoundError, NotADirectoryError, PermissionError) as exception:
            await ctx.send(exception)
    
    @commands.command()
    async def wget(self, ctx: discord.ext.commands.Context, url='', path=''):
        """Attempt to store a URL in the working directory."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        if len(ctx.message.attachments) > 1:
            await ctx.send('Too many files attached!')
            return
        elif len(ctx.message.attachments) == 1:
            path = url
            url = str(ctx.message.attachments[0])

        try:
            self._consoles[ctx.guild.id].wget(url, path, ctx.author.id)
            await ctx.send('File saved.')
        except (FileNotFoundError, NotADirectoryError, FileExistsError, PermissionError) as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def mv(self, ctx, source='', target=''):
        """Move or rename a file."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            self._consoles[ctx.guild.id].mv(source, target, ctx.author.id)
            await ctx.send('File moved.')
        except (NameError, FileNotFoundError, NotADirectoryError, FileExistsError, PermissionError) as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def cd(self, ctx, *, arg=''):
        """Change the directory, and output the new working path."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            self._consoles[ctx.guild.id].cd(arg)
            await ctx.send('```'+str(self._consoles[ctx.guild.id])+'```')
        except NotADirectoryError as exception:
            await ctx.send(exception)

    @commands.command()
    async def ls(self, ctx, *, path=''):
        """List the contents of the working directory, or folder at path if given."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            contents = self._consoles[ctx.guild.id].ls(path)
            out = '```\n'
            for filename in contents:
                out += filename + '\n'
            out += '```'
            if len(contents) == 0:
                out = '```\n \n```'
            await ctx.send(out)
        except NotADirectoryError as exception:
            await ctx.send(exception)

    @commands.command()
    async def pwd(self, ctx):
        """Outputs the current working directory."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        await ctx.send('```'+self._consoles[ctx.guild.id].pwd()+'```')

    @commands.command()
    async def upload(self, ctx: discord.ext.commands.Context, path=''):
        """Upload a file from the system."""
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            await ctx.send(self._consoles[ctx.guild.id].retrieve_file(path))
        except FileNotFoundError as exception:
            await ctx.send(str(exception))


async def setup(bot):
    await bot.add_cog(GlassConsole(bot))
    logger.info('Loaded console commands!')

async def teardown(bot):
    await bot.remove_cog('GlassConsole')
    logger.info('Unloaded console commands.')
    