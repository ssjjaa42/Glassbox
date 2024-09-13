# Look at me. I'm the hero now
# Large swaths of code borrowed from https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
import logging
import asyncio
from async_timeout import timeout
import itertools
import discord
from discord.ext import commands
# from discord import app_commands
from functools import partial
import yt_dlp

logger = logging.getLogger("glassbox")

ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': False, 'quiet': True})


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester):
        super().__init__(source, volume=1)
        self.requester = requester

        self.title = data['title']
        self.webpage_url = data['webpage_url']

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop, playlist=False):
        search_msg = await ctx.send('Searching...', delete_after=10)

        loop = loop or asyncio.get_event_loop()
        to_run = partial(ytdl.extract_info, url=search, download=False)
        data = await loop.run_in_executor(None, to_run)
        await search_msg.delete()
        if 'entries' in data:
            if playlist:
                data = data
                await ctx.send(f'Queued **{data["title"]} ({len(data["entries"])} tracks)**')
                return [{'webpage_url': datum['webpage_url'],
                         'requester': ctx.author,
                         'title': datum['title']} for datum in data['entries']]
            else:
                try:
                    data = data['entries'][0]
                except IndexError:
                    return
                await ctx.send(f'Queued **{data["title"]}**')
                return {'webpage_url': data['webpage_url'],
                        'requester': ctx.author,
                        'title': data['title']}
        elif 'webpage_url' in data:
            await ctx.send(f'Queued **{data["title"]}**')
            return {'webpage_url': data['webpage_url'],
                    'requester': ctx.author,
                    'title': data['title']}

    @classmethod
    async def regather_stream(cls, data, *, loop):
        loop = loop or asyncio.get_event_loop()
        try:
            requester = data['requester']

            to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
            data = await loop.run_in_executor(None, to_run)
        except Exception:
            raise ValueError('Song not found.')
        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer:
    def __init__(self, ctx: commands.Context):
        self.bot = ctx.bot
        self.__guild = ctx.guild
        self.__channel = ctx.channel
        self.__cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None
        self.volume = 1
        self.current = None
        self.looping = False

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # wait for next song, 5 minute timeout
                async with timeout(300):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self.__guild)

            if not isinstance(source, YTDLSource):
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self.__channel.send(f'An error occured in processing your song: {e}', delete_after=10)
                    continue

            while True:
                source.volume = self.volume
                self.current = source
                self.__guild.voice_client.play(source,
                                               after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                embed = discord.Embed(title='Now playing',
                                      description=f'**{source.title}**\n'
                                      f'requested by {source.requester}\n'
                                      f'{"This song is looping." if self.looping else ""}',
                                      color=0xaa0000)
                self.np = await self.__channel.send(embed=embed)
                await self.next.wait()

                if self.looping:
                    self.next.clear()
                    new_source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                    # cleanup ffmpeg process
                    source.cleanup()
                    source = new_source
                else:
                    # cleanup ffmpeg process
                    try:
                        source.cleanup()
                    except ValueError:
                        pass
                    break

            self.current = None

            try:
                # no longer playing the song
                # await self.np.delete()
                pass
            except discord.HTTPException:
                pass

    def destroy(self, guild: discord.Guild):
        return self.bot.loop.create_task(self.__cog.cleanup(guild))


class Jukebox(commands.Cog):
    """Extension for playing music in voice channels. Praise!"""

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
        except KeyError:
            pass

    def get_player(self, ctx: commands.Context):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
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

    @commands.command(name='play')
    async def play_(self, ctx: commands.Context, * song: str):
        """Queue some audio from a URL or search results.
        Usage: $play <song>
        """

        url = ' '.join(song)

        if not url.startswith('http://') and not url.startswith('https://'):
            # We have a non-URL, so a search query
            url = f'ytsearch:{url}'

        async with ctx.typing():
            player = self.get_player(ctx)
            try:
                if url.startswith('https://www.youtube.com/playlist') or '?list=' in url:
                    # We have a playlist
                    sources = await YTDLSource.create_source(ctx, url, loop=self.bot.loop, playlist=True)
                    for source in sources:
                        await player.queue.put(source)
                else:
                    # Individual video
                    source = await YTDLSource.create_source(ctx, url, loop=self.bot.loop, playlist=False)
                    await player.queue.put(source)
            except yt_dlp.utils.DownloadError:
                await ctx.send('An error occurred in processing your song: If this is a Spotify link, Vitreum knows '
                               'about this error, and he\'ll get to fixing that eventually.',
                               delete_after=10)

    @commands.command(name='playnext')
    async def playnext_(self, ctx: commands.Context, * song: str):
        """Queue some audio from a URL or search results.
        Usage: $playnext <song>
        """

        url = ' '.join(song)

        if not url.startswith('http://') and not url.startswith('https://'):
            # We have a non-URL, so a search query
            url = f'ytsearch:{url}'

        async with ctx.typing():
            player = self.get_player(ctx)
            q_size = player.queue.qsize()
            try:
                if url.startswith('https://www.youtube.com/playlist') or '?list=' in url:
                    # We have a playlist
                    sources = await YTDLSource.create_source(ctx, url, loop=self.bot.loop, playlist=True)
                    for source in sources:
                        await player.queue.put(source)
                else:
                    # Individual video
                    source = await YTDLSource.create_source(ctx, url, loop=self.bot.loop, playlist=False)
                    await player.queue.put(source)
            except yt_dlp.utils.DownloadError:
                await ctx.send('An error occurred. If this is a Spotify link, Vitreum knows '
                               'about this error, and he\'ll get to fixing that eventually.')

            for _ in range(q_size):
                await player.queue.put(await player.queue.get())

    @commands.command(name='stop', aliases=['leave'])
    async def stop_(self, ctx: commands.Context):
        """Stop, wholly. Also clears queues and settings.
        Usage: $stop
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)

        self.get_player(ctx).looping = False
        await self.cleanup(ctx.guild)
        await ctx.send('Goodbye!')

    @commands.command(name='pause')
    async def pause_(self, ctx: commands.Context):
        """Pause. Temporarily.
        Usage: $pause
        """

        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)
        elif ctx.voice_client.is_paused():
            return await ctx.send('Already paused! Unpause with $music resume.', delete_after=10)

        ctx.voice_client.pause()
        await ctx.send('Paused.')

    @commands.command(name='resume')
    async def resume_(self, ctx: commands.Context):
        """Resume playing, if paused.
        Usage: $resume
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)
        elif not ctx.voice_client.is_paused():
            return await ctx.send('Not paused!', delete_after=10)

        ctx.voice_client.resume()
        await ctx.send('Resumed.')

    @commands.command(name='skip')
    async def skip_(self, ctx: commands.Context, index: int = 0):
        """Skip the currently playing song, or remove one from a queue.
        Usage: $skip [index]
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)

        if ctx.voice_client.is_paused():
            pass
        elif not ctx.voice_client.is_playing():
            return

        if index == 0:
            ctx.voice_client.stop()
            return await ctx.send('Skipped!')

        index -= 1
        player = self.get_player(ctx)
        upcoming = list(itertools.islice(player.queue._queue, player.queue.qsize()))
        if not -1 < index < len(upcoming):
            return await ctx.send(f'Invalid index! Current queue size: **{len(upcoming)}**', delete_after=10)

        removed = upcoming.pop(index)

        new_queue = asyncio.Queue()
        for source in upcoming:
            await new_queue.put(source)
        player.queue = new_queue

        await ctx.send(f'Removed **{removed["title"]}** from the queue.')

    @commands.command(name='loop')
    async def loop_(self, ctx: commands.Context):
        """Toggle looping for the current song.
        Usage: $loop"""

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)
        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('Not currently playing anything!')

        if player.looping:
            player.looping = False
            await ctx.send('Looping disabled.')
        else:
            player.looping = True
            await ctx.send('Looping enabled.')

    @commands.command(name='volume')
    async def volume_(self, ctx: commands.Context, volume: int):
        """Change the audio volume.
        Usage: $volume <volume>
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)

        if not 0 <= volume <= 100:
            return await ctx.send('Please enter a REASONABLE volume level.', delete_after=10)

        player = self.get_player(ctx)
        if ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100
        player.volume = volume / 100
        await ctx.send(f'Changed volume to **`{volume}%`**')

    @commands.command(name='queue', aliases=['q', 'playlist'])
    async def queue_info(self, ctx: commands.Context):
        """See the upcoming songs in the queue.
        Usage: $queue
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('The queue is empty.')

        upcoming = list(itertools.islice(player.queue._queue, 0, 8))
        fmt = '\n'.join([f'**{i+1}. `{_["title"]}`**' for i, _ in enumerate(upcoming)])
        if player.looping:
            fmt = '**The current song is looped!**\n' + fmt
        embed = discord.Embed(title=f'Next {len(upcoming)} in queue:',
                              description=fmt,
                              color=0xaa0000)
        await ctx.send(embed=embed)

    @commands.command(name='clear')
    async def clear_(self, ctx: commands.Context):
        """Clear the queue.
        Usage: $clear"""

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)

        player = self.get_player(ctx)
        while not player.queue.empty():
            await player.queue.get()
        await ctx.send('Cleared the queue!')

    @commands.command(name='now_playing', aliases=['np', 'current', 'currentsong', 'playing'])
    async def now_playing_(self, ctx: commands.Context):
        """Display information about the currently playing song.
        Usage: $now_playing
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('Not currently playing anything!', delete_after=10)

        try:
            # await player.np.delete()
            pass
        except discord.HTTPException:
            pass

        embed = discord.Embed(title='Now playing',
                              description=f'**{ctx.voice_client.source.title}**\n'
                              f'requested by {ctx.voice_client.source.requester}\n'
                              f'{"This song is looping." if player.looping else ""}',
                              color=0xaa0000)
        player.np = await ctx.send(embed=embed)

    @play_.before_invoke
    @playnext_.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.invoke(self.join_)


async def setup(bot):
    await bot.add_cog(Jukebox(bot))
    logger.info('Loaded music!')


async def teardown(bot):
    await bot.remove_cog('Jukebox')
    logger.info('Unloaded music.')
