# Glassbox
# by ssjjaa

import os
import logging
import random
import discord
from discord.ext import commands
import modules.settings as settings
# import modules.script as script

intents = discord.Intents.default()
intents.message_content = True
glass = commands.Bot(command_prefix='$', intents=intents)

logger = logging.getLogger('glassbox')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(f'%(asctime)s %(levelname)s\t\b\b\b%(name)s %(message)s', '%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

rand = random.Random()
# s_trouble = script.Script(os.path.join(os.path.curdir, 'data', 'scripts', 'trouble.txt'))
last_channel = None
last_server = None
last_edit = {}


def sanitize_text(text: str):
    """Take a raw string and replace unwanted characters with spaces.

    Unwanted characters are defined in this function.
    """
    for c in '`\n':
        text = text.replace(c, ' ')
    text = text.strip()
    return text


async def log_message(message: discord.Message):
    """Prints a message to the log, sanitizing it first. Also prints the author, current server and channel."""
    global last_channel
    if message.channel != last_channel:
        logger.info(f'{message.guild.name} / {message.channel.name}')
        last_channel = message.channel
    logger.info(f'    {message.author.display_name}: {sanitize_text(message.content)}')


@glass.event
async def on_ready():
    """Boot actions. Set game and status.

    This should only run once. I'm not sure if it actually will, though.
    """
    logger.info(f'Connected as {glass.user}!')
    await glass.load_extension('extensions.glasssettings')
    await glass.load_extension('extensions.glassdadjokes')
    await glass.load_extension('extensions.glassconsole')
    await glass.load_extension('extensions.glasspictures')
    await glass.load_extension('extensions.glassplonk')
    game = discord.Activity(type=discord.ActivityType.watching, name='myself think', state='It\'s dark in here')
    await glass.change_presence(status=discord.Status.do_not_disturb, activity=game)


@glass.command()
@commands.is_owner()
async def shutdown(ctx: discord.ext.commands.Context):
    # TODO move this enumeration of extensions from hard-coding to a settings file
    await ctx.send('Shutting down...')
    logger.info('Shutting down...')
    await glass.unload_extension('extensions.glasssettings')
    await glass.unload_extension('extensions.glassdadjokes')
    await glass.unload_extension('extensions.glassconsole')
    await glass.unload_extension('extensions.glasspictures')
    await glass.unload_extension('extensions.glassplonk')
    await glass.close()


@glass.command()
async def roll(ctx: discord.ext.commands.Context, *, text=''):
    """Roll a n-sided die, with optional modifier.

    Format is $roll NdS, or $roll NdS+M. Negative modifiers work.
    """
    try:
        # 2d6+2 becomes 2 6 2
        # 2d6-3 becomes 2 6 -3
        text = text.lower().replace('d', ' ')
        text = text.replace('+', ' ')
        text = text.replace('-', ' -')
        parts = text.split()
        num = int(parts[0])
        sides = int(parts[1])
        modifier = 0
        if len(parts) > 2:
            modifier = int(parts[2])
        total = 0
        rolls = ''
        for i in range(num):
            roll = rand.randint(1, sides)
            total += roll
            rolls += str(roll)
            if i+1 < num:
                rolls += ', '
        total += modifier
        if modifier > 0:
            await ctx.send(rolls+' (+'+str(modifier)+'): **'+str(total)+'**')
        elif modifier < 0:
            await ctx.send(rolls+' ('+str(modifier)+'): **'+str(total)+'**')
        else:
            await ctx.send(rolls+': **'+str(total)+'**')
    except (IndexError, ValueError):
        await ctx.send('Invalid input! Try \"$roll 1d6\"')


@glass.command()
async def catch4k(ctx):
    """Post the last message edited or deleted in the channel."""
    if str(ctx.message.channel.id) not in last_edit.keys():
        await ctx.send('Targeting failure.')
    if last_edit[str(ctx.message.channel.id)][2] is not None:
        await last_edit[str(ctx.message.channel.id)][2].reply(
            f'**Original message by {last_edit[str(ctx.message.channel.id)][1]}:**\n'
            f'{last_edit[str(ctx.message.channel.id)][0]}')
    else:
        await ctx.send(f'**Original message by {last_edit[str(ctx.message.channel.id)][1]}:**\n'
                       f'{last_edit[str(ctx.message.channel.id)][0]}')


@glass.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.channel.id not in last_edit:
        last_edit[str(before.channel.id)] = [0, 0, 0]
    last_edit[str(before.channel.id)][0] = before.clean_content
    last_edit[str(before.channel.id)][1] = before.author.mention
    last_edit[str(before.channel.id)][2] = after


@glass.event
async def on_message_delete(msg: discord.Message):
    if msg.channel.id not in last_edit:
        last_edit[str(msg.channel.id)] = [0, 0, 0]
    last_edit[str(msg.channel.id)][0] = msg.clean_content
    last_edit[str(msg.channel.id)][1] = msg.author.mention
    last_edit[str(msg.channel.id)][2] = None


@glass.event
async def on_message(message):
    """Message handler. Does things, and then runs it through the command system.

    To be clear, things in this message run BEFORE any command runs.
    This method catches bot messages and does not do anything with them besides print them.
    """
    # Log message
    await log_message(message)
    # Do nothing if the message is from us or another bot
    if message.author.bot:
        return

    # DO NOT ENTER FORBIDDEN PLACES (commands are still ok, though.)
    if message.channel.id in settings.forbidden():
        # Note to self. This process_commands is absolutely necessary! Without this, forbidden channels will respond to NO commands.
        # If you want a COMMAND to not run in forbidden channels, please check ctx.channel.id in the command.
        # The process_commands should not be run in ANY other checks, or else it will genuinely run commands multiple times.
        await glass.process_commands(message)
        return

    # Try responding automatically
    responses = {
        '<@1042577738436980877> caramelldansen': 'https://www.youtube.com/watch?v=qz2Ihbm_Mz0',
        '<@1042577738436980877>': f'Hello, {message.author.display_name}.',
        '<@1042577738436980877> l': 'https://cdn.discordapp.com/attachments/546898644947828756/941466286448332800'
                                    '/2845e155a573a63eb0ded10d83ec5b1b13bf9c30c71819728c207b1c4e73a038_1.png',
        'dead chat': 'https://tenor.com/view/undertale-papyrus-undertale-papyrus-dead-chat-dead-chat-xd-gif'
                     '-25913129',
        '<@1042577738436980877> who\'s on first': 'https://cdn.discordapp.com/attachments/678305861978030081'
                                                  '/928228137333051402/hstrhtr.mp4',
        '<@1042577738436980877> big iron': 'https://cdn.discordapp.com/attachments/525830406776553492'
                                           '/901916671105708102/Big_Iron-3.mp4',
        '<@1042577738436980877> shrek': 'https://cdn.discordapp.com/attachments/704856529840504863'
                                        '/707960111553052732/full-shrek1.webm',
        '<@1042577738436980877> puss in boots': 'https://stolen.shoes/embedVideo?video=https://b2.thefileditch.ch/'
                                                'jdmYNfXxTCPUGAlwLnHq.mp4&image=https://www.hollywoodreporter.com/'
                                                'wp-content/uploads/2022/11/'
                                                'Puss-in-Boots-The-Last-Wish-Everett-H-2022.jpg?w=1296'
    }
    if message.content.lower() in responses:
        await message.channel.send(responses[message.content.lower()])

    # Screech
    if '<@1042577738436980877>' in message.content and len(message.content) > 100:
        await message.channel.send('https://cdn.discordapp.com/attachments/740284671535087745/974198322439028736'
                                   '/do_not_push_the_button.mp4')

    # Be my friend
    # TODO amend script reading. I have disabled it until I decide to work on it again.
    # It needs to have the ability to not be so exacting, completing lines if the human stops partway through.
    # trouble = s_trouble
    # if message.content.lower() == 'trouble':
    #     await message.channel.send('Are you Mr. Dunlop?')
    # if trouble.eval(message.content) and trouble.has_next():
    #     trouble.nextline()
    #     if trouble.has_next():
    #         await message.channel.send(trouble.nextline())
    #     else:
    #         trouble.reset()
    #     return
    # else:
    #     trouble.reset()

    global rand
    # ash moment
    if message.author.id == 412713124077109249:
        if 'florida' in message.content.lower() or 'floridian' in message.content.lower():
            await message.add_reaction('🐊')
        elif rand.random() < 0.0625:  # 1 in 16 chance
            await message.add_reaction('<:frogpog:1005330533544370238>')
    # magment
    if message.author.id == 895809582058831882:
        if rand.random() < 0.0625:  # 1 in 16 chance
            await message.add_reaction('<:cat_eyebrowraise:1037610737947906079>')
    # steve moment
    if message.author.id == 913183576281997332:
        if rand.random() < 0.0625:  # 1 in 16 chance
            if rand.random() < 0.5:
                await message.add_reaction('<:huh:1005333474430963753>')
            else:
                await message.add_reaction('<:whatthefuck:1040419073391071353>')
    # kink moment
    if message.author.id == 720442589584556034:
        if rand.random() < 0.125:  # 1 in 8 chance
            await message.add_reaction('<:bonus_chromosome:1011729141151830047>')
    # fork moment
    if message.author.id == 738020641269219329:
        if rand.random() < 0.0625:  # 1 in 16 chance
            await message.add_reaction('<:redditor:741101661170302987>')
    # scott.png
    if message.author.id == 306196186803601409:
        if rand.random() < 0.0625:  # 1 in 16 chance
            await message.add_reaction('<:highsoldier:1066767768042610768>')

    # Mandatory line to make commands work
    await glass.process_commands(message)

if __name__ == '__main__':
    if not os.path.exists('token.txt'):
        with open('token.txt', 'x') as f:
            f.close()
    with open('token.txt', 'r') as f:
        token = f.read()
        if token == '':
            logger.critical("No token! Please put a login token in token.txt")
            exit(0)
    try:
        glass.run(token)
    except discord.errors.LoginFailure as login_error:
        logger.critical(login_error)
