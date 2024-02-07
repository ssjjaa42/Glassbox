# Plonking for Glassbox
import logging
import discord
from discord.ext import commands
import modules.plonk as swear_jars
from modules.settings import forbidden

logger = logging.getLogger('glassbox')


class GlassPlonk(commands.Cog):
    """Extension to let bots keep track of bad word usage, on a per-user basis."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Do nothing if the message is from a bot
        if message.author.bot:
            return
        # Stay out of forbidden chats
        if message.channel.id in forbidden():
            return

        # Make sure we have this user's settings
        swear_jars.check(message.author.id)
        # Do nothing if the user has no set jar channel
        if swear_jars.get_channel(message.author.id) is None:
            return
        # Process the message for any swears
        words = discord.utils.remove_markdown(message.content).split()
        count = 0
        for word in words:
            if swear_jars.check_word(''.join(ch for ch in word if ch.isalnum())):
                count += 1
                swear_jars.update(message.author.id)
        # Do nothing if there are no swears
        if count == 0:
            return
        # Assemble a response
        response = 'Plonk'
        for i in range(1, count):
            response += ', plonk'
        response += '!'
        # Send the response
        if message.channel.id != swear_jars.get_channel(message.author.id):
            await message.reply(response)
        await self.bot.get_channel(swear_jars.get_channel(message.author.id)).send(
            f'{response}\n{message.author.mention} now owes ${swear_jars.get_quantity(message.author.id):.2f}!')
        
    @commands.group()
    async def plonk(self, ctx: commands.Context):
        swear_jars.check(ctx.author.id)

    @plonk.command(name='manual')
    async def adjust(self, ctx: commands.Context):
        """Increase your swear jar quantity by some amount.
        Usage: $plonk manual
        """
        if swear_jars.get_channel(ctx.author.id) is None:
            return
        swear_jars.update(ctx.author.id)
        if ctx.channel.id != swear_jars.get_channel(ctx.author.id):
            await ctx.reply('Plonk!')
        await self.bot.get_channel(swear_jars.get_channel(ctx.author.id)).send(
            f'Plonk!\n{ctx.author.mention} now owes ${swear_jars.get_quantity(ctx.author.id):.2f}!')
    
    @plonk.command(name='on')
    async def enable(self, ctx: commands.Context):
        """Enables your swear jar.
        Usage: $plonk on
        """
        if swear_jars.get_channel(ctx.author.id) == ctx.channel.id:
            await ctx.send('Already logging your swears to this channel.')
        else:
            swear_jars.set_channel(ctx.author.id, ctx.channel.id)
            await ctx.send('Now logging your swears to this channel.')
    
    @plonk.command(name='off')
    async def disable(self, ctx: commands.Context):
        """Disables your swear jar.
        Usage: $plonk off
        """
        if swear_jars.get_channel(ctx.author.id) is None:
            await ctx.send('Your swears are not logged.')
        else:
            # TODO check and see, does this produce expected behavior?
            # swear_jars.set_channel(ctx.author.id, -1)
            # swear_jars.set_quantity(ctx.author.id, 0)
            del swear_jars.jars_dict[str(ctx.author.id)]
            await ctx.send('Your swears are no longer logged.')

    @plonk.command(name='reset')
    async def reset(self, ctx: commands.Context, quantity=0.0):
        """Resets your swear jar to a certain amount.
        Usage: $plonk reset [amount]

        Parameters
        ----------
        quantity : float, optional
            Optionally, the amount to set your jar to. Do not include the $.
        """
        if swear_jars.get_channel(ctx.author.id) is None:
            await ctx.send('Your swears are not logged.')
        else:
            swear_jars.set_quantity(ctx.author.id, quantity)
            await ctx.send(f'You now owe ${swear_jars.get_quantity(ctx.author.id):.2f}.')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        logger.info(f'glassplonk: Removed from guild {guild}! Removing swear jars in this server...')
        for user_id in swear_jars.jars_dict:
            if swear_jars.jars_dict[user_id][0] in [channel.id for channel in guild.channels]:
                await guild.get_member(int(user_id)).dm_channel.send(f'I\'ve been removed from the server containing '
                                                                     f'your swear jar. At that time, you owed '
                                                                     f'${swear_jars.get_quantity(int(user_id)):.2f}.')
                del swear_jars.jars_dict[user_id]


async def setup(bot: commands.Bot):
    await bot.add_cog(GlassPlonk(bot))
    logger.info('Loaded swear jars!')


async def teardown(bot: commands.Bot):
    await bot.remove_cog('GlassPlonk')
    swear_jars.save()
    logger.info('Unloaded swear jars.')
