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
last_edit = {}


def sanitize_text(text: str):
    """Take a raw string and replace unwanted characters with spaces.

    Unwanted characters are defined in this function.
    """
    for c in '`\n':
        text = text.replace(c, ' ')
    text = text.strip()
    return text


@glass.event
async def on_guild_join(guild):
    """Sets up the data folder when joining a new server."""
    root_path = os.path.join(os.path.curdir, 'data', 'serverfiles')
    target_path = os.path.join(root_path, str(guild.id))
    if not os.path.exists(target_path):
        os.mkdir(target_path)


async def print_message(message: discord.Message):
    """Prints a message to the log, sanitizing it first. Also prints the author, current server and channel."""
    global last_channel
    if message.channel != last_channel:
        print(message.guild.name, '/', message.channel.name)
        last_channel = message.channel
    print(f'\t{message.author.display_name}: {sanitize_text(message.content)}')


@glass.event
async def on_ready():
    """Boot actions. Set game and status.

    This should only run once. I'm not sure if it actually will, though.
    """
    print(f'Connected as {glass.user}!')
    game = discord.Activity(type=discord.ActivityType.watching, name='myself think', state='It\'s dark in here')
    await glass.change_presence(status=discord.Status.do_not_disturb, activity=game)

consoles = {}


@glass.command()
async def mkdir(ctx, *, name):
    """Try to make a new directory."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)
    try:
        consoles[ctx.guild.id].mkdir(name, ctx.author.id)
        await ctx.send(f'Folder created.')
    except PermissionError as exception:
        await ctx.send(exception)


@glass.command()
async def rmdir(ctx, *, path):
    """Try to delete a directory."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)
    try:
        consoles[ctx.guild.id].rmdir(path, ctx.author.id)
        await ctx.send(f'Folder deleted.')
    except (NotADirectoryError, PermissionError) as exception:
        await ctx.send(exception)


@glass.command()
async def rm(ctx, *, path):
    """Try to delete a file."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)
    try:
        consoles[ctx.guild.id].rm(path, ctx.author.id)
        await ctx.send(f'File deleted.')
    except IsADirectoryError:
        try:
            consoles[ctx.guild.id].rmdir(path, ctx.author.id)
            await ctx.send(f'Folder deleted.')
        except (NotADirectoryError, PermissionError) as exception:
            await ctx.send(exception)
    except (FileNotFoundError, NotADirectoryError, PermissionError) as exception:
        await ctx.send(exception)


@glass.command()
async def wget(ctx: discord.ext.commands.Context, url='', path=''):
    """Attempt to store a URL in the working directory."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)

    if len(ctx.message.attachments) > 1:
        await ctx.send('Too many files attached!')
        return
    elif len(ctx.message.attachments) == 1:
        path = url
        url = str(ctx.message.attachments[0])

    try:
        consoles[ctx.guild.id].wget(url, path, ctx.author.id)
        await ctx.send('File saved.')
    except (FileNotFoundError, NotADirectoryError, FileExistsError, PermissionError) as exception:
        await ctx.send(str(exception))


@glass.command()
async def mv(ctx, source='', target=''):
    """Move or rename a file."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)

    try:
        consoles[ctx.guild.id].mv(source, target, ctx.author.id)
        await ctx.send('File moved.')
    except (NameError, FileNotFoundError, NotADirectoryError, FileExistsError, PermissionError) as exception:
        await ctx.send(str(exception))


@glass.command()
async def cd(ctx, *, arg=''):
    """Change the directory, and output the new working path."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)

    try:
        consoles[ctx.guild.id].cd(arg)
        await ctx.send('```'+str(consoles[ctx.guild.id])+'```')
    except NotADirectoryError as exception:
        await ctx.send(exception)


@glass.command()
async def ls(ctx, *, path=''):
    """List the contents of the working directory, or folder at path if given."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)

    try:
        contents = consoles[ctx.guild.id].ls(path)
        out = '```\n'
        for filename in contents:
            out += filename + '\n'
        out += '```'
        if len(contents) == 0:
            out = '```\n \n```'
        await ctx.send(out)
    except NotADirectoryError as exception:
        await ctx.send(exception)


@glass.command()
async def pwd(ctx):
    """Outputs the current working directory."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)

    await ctx.send('```'+consoles[ctx.guild.id].pwd()+'```')


@glass.command()
async def upload(ctx: discord.ext.commands.Context, path=''):
    """Upload a file from the system."""
    # Obligatory check to see if the console is initialized yet
    if ctx.guild.id not in consoles:
        consoles[ctx.guild.id] = GlassConsole(ctx.guild.id)

    try:
        # await ctx.send(file=discord.File(consoles[ctx.guild.id].retrieve_file(path)))
        await ctx.send(consoles[ctx.guild.id].retrieve_file(path))
    except FileNotFoundError as exception:
        await ctx.send(str(exception))


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
async def downey(ctx: discord.ext.commands.Context, *, text=''):
    """Robert Downey, Jr. Explaining meme generator."""
    try:
        pic_path = glasspictures.downey_meme(text)
        await ctx.message.delete()
        await ctx.send(file=discord.File(pic_path))
    except UserWarning as exception:
        await ctx.send(str(exception))


@glass.command()
async def inspirational(ctx: discord.ext.commands.Context, *, text=''):
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
            pic_path = glasspictures.inspirational_meme(image_url, header, body)
        await ctx.send(file=discord.File(pic_path))
    except UserWarning as exception:
        await ctx.send(str(exception))


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
    # Print message
    await print_message(message)
    # Do nothing if the message is from us or another bot
    if message.author.bot:
        return

    # DO NOT ENTER FORBIDDEN PLACES
    # TODO make this configurable and persistent and stored in another file
    forbidden = [917229423311331348, 1089892659096719441]
    if message.channel.id in forbidden:
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

    # Be dad
    defense_dict = {
        'i': 'you',
        'i\'m': 'you\'re',
        'im': 'you\'re',
        'i’m': 'you\'re',
        'i`m': 'you\'re, in addition to using weird symbols,',
        'my': 'your',
        'our': 'your',
        'mine': 'your',
        'i\'ve': 'you\'ve',
        'ive': 'you\'ve',
        'i’ve': 'you\'ve',
        'i`ve': 'you\'ve, in addition to used weird symbols,'
    }
    if message.content.lower().startswith('i\'m ') or \
            message.content.lower().startswith('im ') or \
            message.content.lower().startswith('i’m '):
        name = message.content.lower().split(' ', 1)[1]+' '
        while name.startswith('i\'m ') or \
                name.startswith('im ') or \
                name.startswith('i’m ') or \
                name.startswith('i`m '):
            name = name.split(' ', 1)[1]
        if name != '':
            words = []
            for word in name.split():
                if word in defense_dict:
                    words.append(defense_dict[word])
                else:
                    words.append(word)
            name = ' '.join(words)
            name = name.capitalize()
            my_name = message.guild.me.nick if message.guild.me.nick else "Glassbox"
            await message.channel.send(f'Hi {name}, I\'m {my_name}!')

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
            print("No token! Please put a login token in token.txt")
            exit(0)
    try:
        glass.run(token)
    except discord.errors.LoginFailure as login_error:
        print(login_error)
