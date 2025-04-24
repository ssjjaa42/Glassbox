import logging
import os
import json
import asyncio
import discord
from discord.ext import commands
import requests
from samtts import SamTTS


logger = logging.getLogger("glassbox")

settings_path = os.path.join(os.path.curdir, 'data', 'settings')
if not os.path.exists(settings_path):
    os.mkdir(settings_path)
voice_settings_path = os.path.join(settings_path, 'tts.json')
if not os.path.exists(voice_settings_path):
    with open(voice_settings_path, 'x') as f:
        f.write('{}')
tmp_folder_path = os.path.join(os.path.curdir, 'data', 'tmp')
if not os.path.exists(tmp_folder_path):
    os.mkdir(tmp_folder_path)

# Initialize settings
guild_user_channel_bindings = {}
with open(voice_settings_path) as f:
    guild_user_voice_mappings = json.load(f)

streamelements_voices = ['Amy', 'Brian', 'Emma', 'Geraint']
sam_voices = ['Sam', 'Alien', 'Robot']


class TTSSource(discord.FFmpegPCMAudio):
    def __init__(self, source: str):
        super().__init__(source)

    @classmethod
    async def create_source(cls, ctx: commands.Context, text: str, voice: str):
        filepath = os.path.join(tmp_folder_path, f'{voice}_{text}_{ctx.__hash__()}.mp3')
        if voice in streamelements_voices:
            tts = requests.get('https://api.streamelements.com/kappa/v2/speech?', {'voice': voice, 'text': text})\
                .content
            with open(filepath, 'xb') as file:
                file.write(tts)
        elif voice in sam_voices:
            if voice == 'Sam':
                SamTTS().save(text, filepath)
            elif voice == 'Alien':
                SamTTS(100, 64, 200, 150).save(text, filepath)
            elif voice == 'Robot':
                SamTTS(92, 60, 190, 190).save(text, filepath)
        return filepath


class TTSPlayer:
    def __init__(self, ctx: commands.Context):
        self.bot = ctx.bot
        self.__guild = ctx.guild
        self.__cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            # prepare the flag for a new entry
            self.next.clear()

            # wait for next source
            sourcepath = await self.queue.get()
            source = TTSSource(sourcepath)

            while True:
                # check to see if is in voice channel
                if not self.__guild.voice_client:
                    logger.error('Attempted to play from source but voice_client was None!')
                    try:
                        os.remove(sourcepath)
                        source.cleanup()
                    except ValueError:
                        pass
                    return self.destroy(self.__guild)

                # play the file
                for v in sam_voices:
                    if sourcepath.split('/')[-1].startswith(v):
                        source = discord.PCMVolumeTransformer(source, volume=0.3)
                self.__guild.voice_client.play(source,
                                               after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))

                # pause until the sound file is complete
                await self.next.wait()

                self.__guild.voice_client.stop()
                # cleanup ffmpeg process
                try:
                    os.remove(sourcepath)
                    source.cleanup()
                except ValueError:
                    pass

                break

    def destroy(self, guild: discord.Guild):
        return self.bot.loop.create_task(self.__cog.cleanup(guild))


class DiscordTTS(commands.Cog):
    """Provides more refined TTS functionality."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild: discord.Guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
            del guild_user_channel_bindings[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx: commands.Context):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = TTSPlayer(ctx)
            self.players[ctx.guild.id] = player
        return player

    @commands.command(name='join', aliases=['connect'])
    async def join_(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Connect to a voice channel.
        Usage: $join [channel]
        """

        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                return await ctx.send('You are not in a voice channel!')

        if ctx.voice_client:
            if ctx.voice_client.channel.id == channel.id:
                return
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f'Connected to {channel}!')

    @commands.command(name='leave')
    async def leave_(self, ctx: commands.Context):
        """Leave and clear TTS settings.
        Usage: $leave
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)

        await self.cleanup(ctx.guild)
        await ctx.send('Goodbye!')

    @commands.group()
    async def tts(self, ctx: commands.Context):
        pass

    @tts.command(name='voices')
    async def voices_(self, ctx: commands.Context):
        response = '\n'.join(streamelements_voices) + '\n'
        response += '\n'.join(sam_voices)
        await ctx.reply(response)

    @tts.command(name='setvoice')
    async def voice_(self, ctx: commands.Context, *, voice: str):
        # ensure voice mapping exists
        if ctx.guild.id not in guild_user_voice_mappings:
            guild_user_voice_mappings[ctx.guild.id] = {}

        voice = voice.lower().capitalize()
        if voice not in streamelements_voices and voice not in sam_voices:
            return await ctx.reply('Invalid voice option! To view a complete list, do $tts voices.')

        # set user voice mapping
        guild_user_voice_mappings[ctx.guild.id][ctx.author.id] = voice
        await ctx.reply(f'Set your TTS voice to {voice}!')

    @tts.command(name='say')
    async def say_(self, ctx: commands.Context, *, text: str):
        # ensure voice client is connected
        if not ctx.voice_client:
            return
        # ensure voice mapping exists
        if ctx.guild.id not in guild_user_voice_mappings:
            guild_user_voice_mappings[ctx.guild.id] = {}

        try:
            voice = guild_user_voice_mappings[ctx.guild.id][ctx.author.id]
        except KeyError:
            voice = 'Brian'

        clean_words = []
        for w in text.split():
            if not w.startswith('http') and not w.startswith('<') and len(w) < 20:
                clean_words.append(w)
        clean_text = ' '.join(clean_words)
        forbidden_characters = '#@/\\:'
        for c in forbidden_characters:
            clean_text = clean_text.replace(c, ' ')

        player = self.get_player(ctx)
        source = await TTSSource.create_source(ctx, clean_text, voice)
        await player.queue.put(source)

    @tts.command(name='bind')
    async def bind_(self, ctx: commands.Context, channel: discord.TextChannel = None):
        # ensure channel mapping exists
        if ctx.guild.id not in guild_user_channel_bindings:
            guild_user_channel_bindings[ctx.guild.id] = {}

        # add channel binding for user
        if channel:
            guild_user_channel_bindings[ctx.guild.id][ctx.author.id] = channel.id
        else:
            guild_user_channel_bindings[ctx.guild.id][ctx.author.id] = ctx.channel.id

        await ctx.reply('Auto-TTS enabled for your messages in the channel! To disable, do $tts unbind.\n'
                        '-# Note: You can only have Auto-TTS enabled for one channel at a time. '
                        'This channel overwrites any previous setting.\n'
                        '-# Note 2: Auto-TTS settings are cleared when I leave the voice channel.')

    @say_.before_invoke
    @bind_.before_invoke
    async def ensure_voice(self, ctx: commands.Context = None):
        if not ctx.voice_client:
            await ctx.invoke(self.join_)

    @tts.command(name='unbind')
    async def unbind_(self, ctx: commands.Context):
        # ensure channel mapping exists
        if ctx.guild.id not in guild_user_channel_bindings:
            guild_user_channel_bindings[ctx.guild.id] = {}

        # remove channel binding for user
        if guild_user_channel_bindings[ctx.guild.id][ctx.author.id]:
            del guild_user_channel_bindings[ctx.guild.id][ctx.author.id]

        await ctx.reply('Auto-TTS disabled.')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ensure channel mapping exists
        if message.guild.id not in guild_user_channel_bindings:
            guild_user_channel_bindings[message.guild.id] = {}

        try:
            if message.channel.id == guild_user_channel_bindings[message.guild.id][message.author.id] \
             and message.author.voice and message.author.voice.channel:
                # wait a half second -- then check to see if the message still exists (looking at you, pluralkit)
                await asyncio.sleep(0.5)
                if message and message.content[0] not in '!$%^&?/':
                    await self.say_(commands.Context(message=message, bot=self.bot, view=None),
                                    text=message.clean_content)
        except KeyError:
            pass


async def setup(bot):
    await bot.add_cog(DiscordTTS(bot))
    logger.info('Loaded TTS!')


async def teardown(bot):
    await bot.remove_cog('DiscordTTS')
    logger.info('Unloaded TTS.')
