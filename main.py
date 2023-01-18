# Glassbox
# by ssjjaa

import os
import random
import discord
from discord.ext import commands
from glassconsole import GlassConsole
import glasspictures
import script

intents = discord.Intents.default()
intents.message_content = True
glass = commands.Bot(command_prefix='$', intents=intents)

rand = random.Random()
s_trouble = script.Script(os.path.join(os.path.curdir, 'data', 'scripts', 'trouble.txt'))
last_channel = None
last_server = None


def sanitize_text(text: str):
    for c in '`\n':
        text = text.replace(c, ' ')
    text = text.strip()
    return text


@glass.event
async def on_guild_join(guild):
    root_path = os.path.join(os.path.curdir, 'data', 'serverfiles')
    target_path = os.path.join(root_path, str(guild.id))
    if not os.path.exists(target_path):
        os.mkdir(target_path)


async def print_message(message: discord.Message):
    global last_channel
    if message.channel != last_channel:
        print(message.guild.name, '/', message.channel.name)
        last_channel = message.channel
    print(f'\t{message.author.display_name}: {sanitize_text(message.content)}')


async def atr2message(message: discord.Message):
    global rand
    # Say hi
    if message.content == '<@1042577738436980877>':
        await message.channel.send(f'Hello, {message.author.display_name}.')

    # Be dad
    if message.content.lower().startswith('i\'m ') or \
       message.content.lower().startswith('im ') or \
       message.content.lower().startswith('i’m '):
        if len(message.content) < 30:
            name = message.content.lower().split(' ', 1)[1].capitalize()
            await message.channel.send(f'Hi {name}, I\'m The Borg!')

    # kink moment
    if message.author.id == 720442589584556034:
        if rand.random() < 0.125:
            await message.add_reaction('<:bonus_chromosome:1011729141151830047>')
    # fork moment
    if message.author.id == 738020641269219329:
        if rand.random() < 0.0625:
            await message.add_reaction('<:redditor:741101661170302987>')


async def shawty_message(message: discord.Message):
    # Keep out of the stormy garden
    if message.channel.id == 917229423311331348:
        return

    # Mag's swear jar
    if message.author.id == 895809582058831882:
        for swear in [' fuck', ' ass', ' shit', ' bitch', ' cunt']:
            if swear in ' '+message.content.lower():
                # await message.reply('Plonk!')
                pass

    # Be my friend
    trouble = s_trouble
    if message.content.lower() == 'trouble':
        await message.channel.send('Are you Mr. Dunlop?')
    if trouble.eval(message.content) and trouble.has_next():
        trouble.nextline()
        if trouble.has_next():
            await message.channel.send(trouble.nextline())
        else:
            trouble.reset()
        return
    else:
        trouble.reset()

    global rand
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
        '<@1042577738436980877> sonic': 'https://cdn.discordapp.com/attachments/832423825076912128'
                                        '/846624638981242900/Sonic_The_Hedgehog.mp4 '
    }
    if message.content.lower() in responses:
        await message.channel.send(responses[message.content.lower()])

    # Screech
    if '<@1042577738436980877>' in message.content and len(message.content) > 100:
        await message.channel.send('https://cdn.discordapp.com/attachments/740284671535087745/974198322439028736'
                                   '/do_not_push_the_button.mp4')

    # Be dad
    if message.content.lower().startswith('i\'m ') or \
       message.content.lower().startswith('im ') or \
       message.content.lower().startswith('i’m '):
        if len(message.content) < 30:
            # 1 in 2 chance
            if rand.random() < 0.5:
                name = message.content.lower().split(' ', 1)[1].capitalize()
                await message.channel.send(f'Hi {name}, I\'m Glassbox!')

    # ash moment
    if message.author.id == 412713124077109249:
        if 'florida' in message.content.lower() or 'floridian' in message.content.lower():
            await message.add_reaction('🐊')
        # 1 in 16 chance
        elif rand.random() < 0.0625:
            await message.add_reaction('<:frogpog:1005330533544370238>')
    # magment
    if message.author.id == 895809582058831882:
        # 1 in 16 chance
        if rand.random() < 0.0625:
            await message.add_reaction('<:cat_eyebrowraise:1037610737947906079>')
    # steve moment
    if message.author.id == 913183576281997332:
        # 1 in 16 chance
        if rand.random() < 0.0625:
            if rand.random() < 0.5:
                await message.add_reaction('<:huh:1005333474430963753>')
            else:
                await message.add_reaction('<:whatthefuck:1040419073391071353>')


@glass.event
async def on_ready():
    print(f'Connected as {glass.user}!')
    game = discord.Activity(type=discord.ActivityType.watching, name='myself think', state='It\'s dark in here')
    await glass.change_presence(status=discord.Status.do_not_disturb, activity=game)

consoles = {}


@glass.command()
async def cd(ctx, *, arg=''):
    """Change the directory."""
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)
    if arg == '':
        await ctx.send('```\n'+str(consoles[ctx.guild.id])+'\n```')
        return
    try:
        consoles[ctx.guild.id].cd(arg)
    except NotADirectoryError as exception:
        await ctx.send(exception)
    await ctx.send('```\n'+str(consoles[ctx.guild.id])+'\n```')


@glass.command()
async def ls(ctx):
    """List the contents of the current directory."""
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)
    contents = consoles[ctx.guild.id].ls()
    out = '```\n'
    for filename in contents:
        out += filename + '\n'
    out += '```'
    if len(contents) == 0:
        out = '```\n \n```'
    await ctx.send(out)


@glass.command()
async def upload(ctx, path=''):
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)
    if os.path.normpath(path).startswith('..'):
        await ctx.send('Invalid path. Bad user!')
        return
    new_path = os.path.join(consoles[ctx.guild.id].get_path(), path)
    if os.path.isfile(new_path):
        await ctx.send(file=discord.File(new_path))
    else:
        await ctx.send('Invalid path.')


@glass.command()
async def downey(ctx: discord.ext.commands.Context, *, text=''):
    try:
        pic_path = glasspictures.downey_meme(text)
        await ctx.message.delete()
        await ctx.send(file=discord.File(pic_path))
    except UserWarning as exception:
        await ctx.send(str(exception))


@glass.command()
async def inspirational(ctx: discord.ext.commands.Context, *, text=''):
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
            pic_path = glasspictures.inspirational_meme(image_url, header, body)
        await ctx.send(file=discord.File(pic_path))
    except UserWarning as exception:
        await ctx.send(str(exception))


@glass.event
async def on_message(message):
    # Print message
    await print_message(message)
    # Do nothing if the message is from us or another bot
    if message.author.bot:
        return
    # Do stuff if the message is in ATR2
    if message.guild.id == 740284671535087742:
        await atr2message(message)
    # Do stuff if the message is in The Shawty Verse
    if message.guild.id == 910680843704488006:
        await shawty_message(message)
    # Do stuff if the message is in the doghouse
    if message.guild.id == 1040092108712837230:
        await shawty_message(message)
    await glass.process_commands(message)

if __name__ == '__main__':
    if not os.path.exists('token.txt'):
        with open('token.txt', 'x') as f:
            f.close()
    with open('token.txt', 'r') as f:
        token = f.read()
    try:
        glass.run(token)
    except discord.errors.LoginFailure as e:
        print(e)
