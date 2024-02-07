# Console commands for Glassbox
import os
import shutil
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
        """Try to make a new directory in this location.\n
        Usage: $mkdir {name}

        Parameters:
        -----------
        name : str
            The name of the folder to create.
        """
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
        """Try to delete a directory.\n
        Usage: $rmdir {path}

        Parameters:
        -----------
        path : str
            The folder to delete.
        """
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
        """Try to delete a file.\n
        Usage: $rm {path}

        Parameters:
        -----------
        path : str
            The file to delete.
        """
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
        """Download a file from a URL.\n
        Usage: $wget {URL} {path}

        Parameters:
        -----------
        url : str
            The URL of the file to download.
        path : str
            The path or name to save the file under.
        """
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
        """Move or rename a file.\n
        Usage: $mv {source} {target}

        Parameters:
        -----------
        source : str
            The name or location of the file to move.
        target : str
            The new name or location to move the file to.
        """
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            self._consoles[ctx.guild.id].mv(source, target, ctx.author.id)
            await ctx.send('File moved.')
        except (NameError, FileNotFoundError, NotADirectoryError, FileExistsError, PermissionError) as exception:
            await ctx.send(str(exception))

    @commands.command()
    async def cd(self, ctx, *, path=''):
        """Change the current directory, and output the new working path.\n
        Usage: $cd [path]

        If no path is given, it will reset the working path to the home directory (~).

        Parameters:
        -----------
        path : str
            Optionally, the folder to move to.
        """
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            self._consoles[ctx.guild.id].cd(path)
            await ctx.send('```'+str(self._consoles[ctx.guild.id])+'```')
        except NotADirectoryError as exception:
            await ctx.send(exception)

    @commands.command()
    async def ls(self, ctx, *, path=''):
        """List the contents of a directory.\n
        Usage: $ls [path]

        In practice, no path will be given, in which case the contents of the current directory will be displayed,
        but if a path is provided, the contents of that folder will be displayed instead.

        Parameters:
        -----------
        path : str
            Optionally, the folder to display the contents of.
        """
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
        """Displays the path of the current working directory.\n
        Usage: $pwd
        """
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        await ctx.send('```'+self._consoles[ctx.guild.id].pwd()+'```')

    @commands.command()
    async def upload(self, ctx: discord.ext.commands.Context, path=''):
        """Upload a file from the system to Discord.\n
        Usage: $upload {path}

        Parameters:
        -----------
        path : str
            The file to upload.
        """
        # Obligatory check to see if the console is initialized yet
        if ctx.guild.id not in self._consoles:
            self._consoles[ctx.guild.id] = Console(ctx.guild.id)

        try:
            await ctx.send(self._consoles[ctx.guild.id].retrieve_file(path))
        except FileNotFoundError as exception:
            await ctx.send(str(exception))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        logger.info(f'glassconsole: Removed from guild {guild}! Deleting user files...')
        server_dir = os.path.join(os.path.curdir, 'data', 'serverfiles', str(guild.id))
        if os.path.exists(server_dir):
            shutil.rmtree(server_dir)


async def setup(bot):
    await bot.add_cog(GlassConsole(bot))
    logger.info('Loaded console commands!')


async def teardown(bot):
    await bot.remove_cog('GlassConsole')
    logger.info('Unloaded console commands.')
    