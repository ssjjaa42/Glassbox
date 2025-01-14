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
from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import os

logger = logging.getLogger("glassbox")
embed_color = 0x0033aa
ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio',
                         'quiet': True,
                         'extract_flat': 'in_playlist'})
ytdl2 = yt_dlp.YoutubeDL({'format': 'bestaudio',
                          'quiet': True,
                          'extract_flat': 'in_playlist',
                          'playlist_items': '1:2'})

if not os.path.exists('spotify_api_token.txt'):
    with open('spotify_api_token.txt', 'x') as f:
        f.close()
with open('spotify_api_token.txt', 'r') as f:
    api_tokens = f.read()
    if api_tokens == '':
        logger.error("No Spotify API token! This module will not work properly. "
                     "Please put a developer token and secret in spotify_api_token.txt")
api_tokens = api_tokens.split()
client_id = api_tokens[0]
client_secret = api_tokens[1]
spotify = Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

search_queue = asyncio.Queue()
search_results = {}


async def search_loop(bot: commands.Bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        # wait for next song, 5 minute timeout
        request = await search_queue.get()
        query = request.query
        loop = bot.loop

        # Load Spotify lists
        if query.startswith('https://open.spotify.com/playlist/') \
           or query.startswith('https://open.spotify.com/album/'):
            if query.startswith('https://open.spotify.com/playlist/'):
                logger.info('Parsing Spotify playlist')
                playlist = spotify.playlist(query)
            elif query.startswith('https://open.spotify.com/album/'):
                logger.info('Parsing Spotify album')
                playlist = spotify.album(query)

            logger.info(f'Downloading {len(playlist["tracks"]["items"])} parsed tracks')
            combined_tracks = []
            for track in playlist['tracks']['items']:
                if 'track' in track:
                    track = track['track']
                query = f'{track["artists"][0]["name"]} {track["name"]}'
                query = f'https://www.youtube.com/results?search_query={"+".join(query.split())}'
                to_run = partial(ytdl2.extract_info, url=query, download=False)
                results = await loop.run_in_executor(None, to_run)
                # Attempt 1, see if the first search result works
                try:
                    data = results['entries'][0]
                    if 'duration' not in data:
                        data = {'error': yt_dlp.DownloadError(f'Song not found: {track["name"]}')}
                except IndexError:
                    data = {'error': yt_dlp.DownloadError(f'Song not found: {track["name"]}\n'
                                                          f'Special Case 1: <@{bot.owner_id}>')}
                # Attempt 2, see if the second search result works
                if 'error' in data:
                    try:
                        data = results['entries'][1]
                        if 'duration' not in data:
                            data = {'error': yt_dlp.DownloadError(f'Song not found: {track["name"]}')}
                    except IndexError:
                        data = {'error': yt_dlp.DownloadError(f'Song not found: {track["name"]}\n'
                                                              f'Special Case 2: <@{bot.owner_id}>')}
                if 'error' in data:
                    logger.warning(f'Song not found: {query}')
                combined_tracks.append(data)

            search_results[request.key] = (combined_tracks,
                                           playlist['name'],
                                           playlist['external_urls']['spotify'],
                                           playlist['images'][0]['url'])
            request.flag.set()
            continue

        # Convert single Spotify tracks to YouTube searches
        elif query.startswith('https://open.spotify.com/track/'):
            logger.info('Parsing Spotify track')
            track = spotify.track(query)
            query = f'{track["artists"][0]["name"]} {track["name"]}'
            query = f'https://www.youtube.com/results?search_query={"+".join(query.split())}'

        # Load from URL
        if query.startswith('https://www.youtube.com/playlist'):
            logger.info(f'Downloading whole YouTube playlist: {query}')
            to_run = partial(ytdl.extract_info, url=query, download=False)
        else:
            logger.info(f'Downloading single YouTube track: {query}')
            to_run = partial(ytdl2.extract_info, url=query, download=False)
        try:
            data = await loop.run_in_executor(None, to_run)
        except yt_dlp.DownloadError as e:
            logger.warning(f'Song not found: {e}')
            data = {'error': e}

        search_results[request.key] = data
        request.flag.set()
        continue


class SearchRequest():
    def __init__(self, query: str, flag: asyncio.Event, key: str):
        self.query = query
        self.flag = flag
        self.key = key


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester):
        super().__init__(source, volume=1)
        self.requester = requester

        self.title = data['title']
        self.webpage_url = data['webpage_url']
        self.thumbnail = data['thumbnail']
        self.duration = data['duration']

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, playlist=False):
        search_msg = await ctx.reply('Searching...')
        results_back = asyncio.Event()
        key = ctx.__hash__()
        await search_queue.put(SearchRequest(search, results_back, key))
        await results_back.wait()
        data = search_results[key]
        del search_results[key]
        await search_msg.delete()

        if 'error' in data:
            # Something went wrong.
            raise data['error']

        if search.startswith('https://open.spotify.com/playlist/') \
           or search.startswith('https://open.spotify.com/album/'):
            # The format of data is ([sources], playlist_name, url, thumbnail_url)
            sources = []
            for datum in data[0]:
                if 'error' in datum:
                    await ctx.reply(f'Sorry! {datum["error"]}')
                    continue
                sources.append({'webpage_url': datum['url'],
                                'requester': ctx.author,
                                'title': datum['title'],
                                'thumbnail': datum['thumbnails'][0]['url'],
                                'duration': datum['duration']})
            embed = discord.Embed(title='Playlist queued',
                                  description=f'**[{data[1]}]({data[2]})**\n'
                                  f'**{len(sources)} tracks**',
                                  color=embed_color)
            embed.set_thumbnail(url=data[3])
            await ctx.send(embed=embed)
            return sources
        if 'entries' in data:
            if playlist:
                logger.info('Saved playlist')
                embed = discord.Embed(title='Playlist queued',
                                      description=f'**[{data["title"]}]({data["webpage_url"]})**\n'
                                      f'**{len(data["entries"])} tracks**',
                                      color=embed_color)
                embed.set_thumbnail(url=data['thumbnails'][0]['url'])
                await ctx.send(embed=embed)
                return [{'webpage_url': datum['url'],
                         'requester': ctx.author,
                         'title': datum['title'],
                         'thumbnail': datum['thumbnails'][0]['url'],
                         'duration': datum['duration']} for datum in data['entries']]
            else:
                logger.info('Saved video from search results')
                try:
                    data = data['entries'][0]
                except IndexError:
                    raise yt_dlp.DownloadError('Song not found. \nSpecial Case 3!')
                data['duration'] = int(data['duration'])
                embed = discord.Embed(title='Song queued',
                                      description=f'**[{data["title"]}]({data["url"]})**\n'
                                      f'Length: **{data["duration"]//60}:{(data["duration"]%60):02d}**',
                                      color=embed_color)
                embed.set_thumbnail(url=data['thumbnails'][0]['url'])
                await ctx.send(embed=embed)
                return {'webpage_url': data['url'],
                        'requester': ctx.author,
                        'title': data['title'],
                        'thumbnail': data['thumbnails'][0]['url'],
                        'duration': data['duration']}
        elif 'webpage_url' in data:
            logger.info('Saved video from URL')
            embed = discord.Embed(title='Song queued',
                                  description=f'**[{data["title"]}]({data["webpage_url"]})**\n'
                                  f'Length: **{data["duration"]//60}:{(data["duration"]%60):02d}**',
                                  color=embed_color)
            embed.set_thumbnail(url=data['thumbnail'])
            await ctx.send(embed=embed)
            return {'webpage_url': data['webpage_url'],
                    'requester': ctx.author,
                    'title': data['title'],
                    'thumbnail': data['thumbnail'],
                    'duration': data['duration']}
        else:
            logger.error(f'Unknown data: {data}')

    @classmethod
    async def regather_stream(cls, data):
        requester = data['requester']
        results_back = asyncio.Event()
        key = f'{requester.name}{data["webpage_url"]}'
        await search_queue.put(SearchRequest(data['webpage_url'], results_back, key))
        await results_back.wait()
        data = search_results[key]
        del search_results[key]

        before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        return cls(discord.FFmpegPCMAudio(data['url'], before_options=before_options), data=data, requester=requester)


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
                    source = await YTDLSource.regather_stream(source)
                except Exception as e:
                    await self.__channel.send(f'An error occured in processing your song: {e}', delete_after=10)
                    continue

            while True:
                source.volume = self.volume
                self.current = source
                if not self.__guild.voice_client:
                    logger.error('Attempted to play from source but voice_client was None!')
                    try:
                        source.cleanup()
                    except ValueError:
                        pass
                    return self.destroy(self.__guild)
                self.__guild.voice_client.play(source,
                                               after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                embed = discord.Embed(title='Now playing',
                                      description=f'**[{source.title}]({source.webpage_url})**\n'
                                      f'requested by {source.requester}\n'
                                      f'Length: **{source.duration//60}:{(source.duration%60):02d}**\n'
                                      f'{"**This song is looping.**" if self.looping else ""}',
                                      color=embed_color)
                embed.set_thumbnail(url=source.thumbnail)
                self.np = await self.__channel.send(embed=embed)
                await self.next.wait()

                if self.looping:
                    self.next.clear()
                    new_source = await YTDLSource.regather_stream(source)
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
        bot.loop.create_task(search_loop(bot))

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
            url = f'https://www.youtube.com/results?search_query={"+".join(url.split())}'

        async with ctx.typing():
            player = self.get_player(ctx)
            try:
                if url.startswith('https://www.youtube.com/playlist') \
                     or url.startswith('https://open.spotify.com/playlist/') \
                     or url.startswith('https://open.spotify.com/album/'):
                    # We have a playlist
                    await ctx.send('This is a playlist! Please be patient with this search, '
                                   'you can expect it to take longer than usual.', delete_after=15)
                    sources = await YTDLSource.create_source(ctx, url, playlist=True)
                    for source in sources:
                        if source is None:
                            await ctx.send('An error has occurred!\n'
                                           f'Your lucky day..! This is Mystery Error 1 <@{self.bot.owner_id}> is '
                                           'trying to pin down.\nYour song has not been added to the queue. '
                                           'It\'s likely it couldn\'t be found.')
                            continue
                        await player.queue.put(source)
                else:
                    # Individual video
                    if '&list=' in url:
                        url = url[:url.find('&list=')]
                    source = await YTDLSource.create_source(ctx, url, playlist=False)
                    if source is None:
                        return await ctx.send('An error has occurred!\n'
                                              f'Your lucky day..! This is Mystery Error 2 <@{self.bot.owner_id}> is '
                                              'trying to pin down.\nYour song has not been added to the queue. '
                                              'It\'s likely it couldn\'t be found.')
                    await player.queue.put(source)
            except yt_dlp.DownloadError as e:
                await ctx.reply(e)

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
                if url.startswith('https://www.youtube.com/playlist') \
                     or url.startswith('https://open.spotify.com/playlist/') \
                     or url.startswith('https://open.spotify.com/album/'):
                    # We have a playlist
                    await ctx.send('This is a playlist! Please be patient with this search, '
                                   'you can expect it to take longer than usual.', delete_after=15)
                    sources = await YTDLSource.create_source(ctx, url, playlist=True)
                    for source in sources:
                        if source is None:
                            await ctx.send('An error has occurred!\n'
                                           f'Your lucky day..! This is Mystery Error 1 <@{self.bot.owner_id}> is '
                                           'trying to pin down.\nYour song has not been added to the queue. '
                                           'It\'s likely it couldn\'t be found.')
                            continue
                        await player.queue.put(source)
                else:
                    # Individual video
                    if '&list=' in url:
                        url = url[:url.find('&list=')]
                    source = await YTDLSource.create_source(ctx, url, playlist=False)
                    if source is None:
                        return await ctx.send('An error has occurred!\n'
                                              f'Your lucky day..! This is Mystery Error 2 <@{self.bot.owner_id}> '
                                              'is trying to pin down.\nYour song has not been added to the queue. '
                                              'It\'s likely it couldn\'t be found.')
                    await player.queue.put(source)
            except yt_dlp.DownloadError as e:
                await ctx.reply(e)

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
    async def volume_(self, ctx: commands.Context, volume: float):
        """Change the audio volume.
        Usage: $volume <volume>
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('Not connected to a voice channel.', delete_after=10)

        volume = int(volume)
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
        fmt = '\n'.join([f'**{i+1}. [{_["title"]}]({_["webpage_url"]})**' for i, _ in enumerate(upcoming)])
        if player.looping:
            fmt = '**The current song is looped!**\n' + fmt
        embed = discord.Embed(title=f'Next {len(upcoming)} in queue:',
                              description=fmt,
                              color=embed_color)
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

        source = player.current
        embed = discord.Embed(title='Now playing',
                              description=f'**[{source.title}]({source.webpage_url})**\n'
                              f'requested by {source.requester}\n'
                              f'Length: **{source.duration//60}:{(source.duration%60):02d}**\n'
                              f'{"**This song is looping.**" if player.looping else ""}',
                              color=embed_color)
        embed.set_thumbnail(url=source.thumbnail)
        player.np = await ctx.send(embed=embed)

    @play_.before_invoke
    @playnext_.before_invoke
    async def ensure_voice(self, ctx: commands.Context = None):
        if not ctx.voice_client:
            await ctx.invoke(self.join_)


async def setup(bot: commands.Bot):
    await bot.add_cog(Jukebox(bot))
    logger.info('Loaded music!')


async def teardown(bot: commands.Bot):
    await bot.remove_cog('Jukebox')
    logger.info('Unloaded music.')
