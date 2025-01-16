# Helldivers 2 Updates for Glassbox
import logging
import os
import json
import asyncio
import requests
from discord.ext import commands

logger = logging.getLogger('glassbox')

settings_path = os.path.join(os.path.curdir, 'data', 'settings')
if not os.path.exists(settings_path):
    os.mkdir(settings_path)
mailinglist_path = os.path.join(settings_path, 'democracy.json')
if not os.path.exists(mailinglist_path):
    with open(mailinglist_path, 'x') as f:
        f.write('[0, []]')

# Initialize settings
with open(mailinglist_path) as f:
    raw_in = json.load(f)
    last_update_time = raw_in[0]
    hd2_mailinglist = raw_in[1]

stored_watched_planets = {}


class Democracy(commands.Cog):
    """Provide live Helldivers 2 updates."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        bot.loop.create_task(self.update_loop())

    async def update_loop(self):
        await self.bot.wait_until_ready()
        global stored_watched_planets
        global last_update_time
        while not self.bot.is_closed():
            news = []
            # Update current news
            response = requests.get(f'https://helldiverstrainingmanual.com/api/v1/war/news?from={last_update_time}')
            if response.status_code != 200:
                logger.error('Something went wrong retrieving the Helldivers campaign progress.')
                await asyncio.sleep(300)
                continue
            raw_news = json.loads(response.content)
            for n in raw_news:
                if n['published'] > last_update_time:
                    last_update_time = n['published'] + 1
                    message = n['message']
                    message = message.replace('<i=3>', '**')
                    message = message.replace('<i=1>', '**')
                    message = message.replace('</i>', '**')
                    message = message + '\n'
                    news.append(message)

            # Update current campaigns
            response = requests.get('https://helldiverstrainingmanual.com/api/v1/war/campaign')
            if response.status_code != 200:
                logger.error('Something went wrong retrieving the Helldivers campaign progress.')
                await asyncio.sleep(300)
                continue
            campaign = json.loads(response.content)
            watched_planets = stored_watched_planets.copy()
            stored_watched_planets.clear()
            for planet in campaign:
                # Correct API: "Illuminates" to "Illuminate"
                if planet['faction'] == 'Illuminates':
                    planet['faction'] = 'Illuminate'
                # The planet is newly under siege
                if planet['defense'] and planet['name'] not in watched_planets:
                    news.append(f'**{planet["name"]}** is under siege by the **{planet["faction"]}**!')
                # The planet is under invasion
                elif not planet['defense'] and planet['expireDateTime'] and planet['name'] not in watched_planets:
                    news.append(f'**{planet["name"]}** is being invaded by the **{planet["faction"]}**!')
                # The planet is newly not under siege. But if it shows up here, then it was lost
                elif planet['name'] in watched_planets \
                        and not planet['defense'] and watched_planets[planet['name']]['defense']:
                    news.append(f'**{planet["name"]}** was lost! It is now under the '
                                f'control of the **{planet["faction"]}**!')
                stored_watched_planets[planet['name']] = planet
            for planetName in watched_planets.keys():
                # The planet is no longer being fought over: A campaign is over
                if planetName not in [p['name'] for p in campaign]:
                    # The planet was formerly a defense: The defense is complete
                    if watched_planets[planetName]['defense']:
                        news.append(f'**{planetName}** was successfully defended from the '
                                    f'**{watched_planets[planetName]["faction"]}**!')
                    # The planet was under invasion
                    elif not watched_planets[planetName]['defense'] and watched_planets[planetName]['expireDateTime']:
                        # The percentage was ~100%: The invasion was repelled
                        if watched_planets[planetName]['percentage'] > 99.5:
                            news.append(f'The **{watched_planets[planetName]["faction"]}** invasion of '
                                        f'**{planetName}** was repelled!')
                        else:
                            news.append(f'The **{watched_planets[planetName]["faction"]}** completed their invasion '
                                        f'of **{planetName}**!')
                    # The planet is ~100% liberated: The liberation is complete
                    elif watched_planets[planetName]['percentage'] > 99.5:
                        news.append(f'**{planetName}** was liberated from the '
                                    f'**{watched_planets[planetName]["faction"]}**!')

            if len(news) > 0:
                news_str = ''
                while len(news) > 0:
                    if len(news_str + news[0] + '\n') > 2000:
                        for channel_id in hd2_mailinglist:
                            await self.bot.get_channel(channel_id).send(news_str)
                        news_str = ''
                    news_str += news.pop(0) + '\n'
                for channel_id in hd2_mailinglist:
                    await self.bot.get_channel(channel_id).send(news_str)

            for planet in campaign:
                stored_watched_planets[planet['name']] = planet

            await asyncio.sleep(300)

    @commands.group()
    async def democracy(self, ctx: commands.Context):
        pass

    @democracy.command(name='enable')
    async def enable_(self, ctx: commands.Context):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send('Administrator privileges are required to use this command.\n'
                                  f'-# `{ctx.author.display_name} is not in the sudoers list. '
                                  'This incident will be reported.`')
        if ctx.channel.id not in hd2_mailinglist:
            hd2_mailinglist.append(ctx.channel.id)
            await ctx.send('Subscribed to **Strohmann News!**\n'
                           '-# Approved by the Ministry of Truth')
        else:
            await ctx.send('You are already subscribed to **Strohmann News!**')

    @democracy.command(name='disable')
    async def disable_(self, ctx: commands.Context):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send('Administrator privileges are required to use this command.\n'
                                  f'-# `{ctx.author.display_name} is not in the sudoers list. '
                                  'This incident will be reported.`')
        if ctx.channel.id in hd2_mailinglist:
            hd2_mailinglist.remove(ctx.channel.id)
            await ctx.send('Unsubscribed from **Strohmann News!**\n'
                           '-# This action has been reported to your Democracy Officer.')
        else:
            await ctx.send('You wish to get further still from Managed Democracy? Do what you will.\n'
                           '-# Watch your back, traitor.')


async def setup(bot):
    await bot.add_cog(Democracy(bot))
    logger.info('Loaded Democracy!')


async def teardown(bot):
    with open(mailinglist_path, 'w') as file:
        json.dump([last_update_time, hd2_mailinglist], file)
    await bot.remove_cog('Democracy')
    logger.info('Unloaded Democracy.')
