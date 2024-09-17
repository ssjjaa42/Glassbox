# Dad jokes for Glassbox
import logging
import os
import json
import discord
from discord.ext import commands
from modules.father import triggers_dad, parse_name
from modules.settings import forbidden

logger = logging.getLogger('glassbox')

settings_path = os.path.join(os.path.curdir, 'data', 'settings')
if not os.path.exists(settings_path):
    os.mkdir(settings_path)
dadjokes_path = os.path.join(settings_path, 'dadjokes.json')
if not os.path.exists(dadjokes_path):
    with open(dadjokes_path, 'x') as f:
        f.write('[]')

# Initialize settings
with open(dadjokes_path) as f:
    dadjoke_banlist = json.load(f)


class GlassFather(commands.Cog):
    """Give a Discord Bot dad jokes."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Do nothing if the message is from us or another bot
        if message.author.bot:
            return
        # Keep out of forbidden servers
        if message.guild.id in dadjoke_banlist:
            return
        # Keep out of forbidden channels
        if message.channel.id in forbidden():
            return
        # Be dad
        if triggers_dad(message.content):
            try:
                name = parse_name(message.clean_content)
                my_name = message.guild.me.nick if message.guild.me.nick else self.bot.user.name
                await message.channel.send(f'Hi {name}, I\'m {my_name}!')
            except ValueError:
                pass

    @commands.group()
    async def dadjokes(self, ctx: commands.Context):
        pass

    @dadjokes.command(name='enable')
    async def enable_(self, ctx: commands.Context):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send('Administrator privileges are required to use this command.\n'
                                  f'-# `{ctx.author.display_name} is not in the sudoers list. '
                                  'This incident will be reported.`')
        if ctx.guild.id in dadjoke_banlist:
            dadjoke_banlist.remove(ctx.guild.id)
            await ctx.send('Enabled dad jokes server-wide!')
        else:
            await ctx.send('Dad jokes were already enabled!')

    @dadjokes.command(name='disable')
    async def disable_(self, ctx: commands.Context):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send('Administrator privileges are required to use this command.\n'
                                  f'-# `{ctx.author.display_name} is not in the sudoers list. '
                                  'This incident will be reported.`')
        if ctx.guild.id not in dadjoke_banlist:
            dadjoke_banlist.append(ctx.guild.id)
            await ctx.send('Disabled dad jokes server-wide!')
        else:
            await ctx.send('Dad jokes were already disabled!')


async def setup(bot):
    await bot.add_cog(GlassFather(bot))
    logger.info('Loaded dad jokes!')


async def teardown(bot):
    with open(dadjokes_path, 'w') as file:
        json.dump(dadjoke_banlist, file)
    await bot.remove_cog('GlassFather')
    logger.info('Unloaded dad jokes.')
