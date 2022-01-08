import collections
import os
import pandas
import re

from discord import Embed
from discord.ext import commands
from discord.utils import escape_markdown
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

CONFIDENCE_INTERVAL = 5
MIN_RATIO_CONFIDENCE = 85
BASE_DOMAIN = 'https://sdvx.in'
BASE_DIFF_NAMES = ['NOV', 'ADV', 'EXH', 'MXM', '']
BASE_DIFF_SUFFIX = ['n', 'a', 'e', 'm', '']
EXTRA_DIFF_NAMES = ['', '', 'INF', 'GRV', 'HVN', 'VVD']
EXTRA_DIFF_SUFFIX = ['', '', 'i', 'g', 'h', 'v']

load_dotenv()
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))
DB_PATH = os.path.join('..', 'sdvx-db', 'db.json')
DB = pandas.read_json(DB_PATH, orient='index')


class SdvxInLinker(commands.Cog, name='sdvx.in'):
    @commands.group(invoke_without_command=True, aliases=['sdvx'])
    async def sdvxin(self, ctx, *args):
        """ SDVX.in related commands """
        if ctx.invoked_subcommand is None:
            await self.search(ctx, query=' '.join(args))

    @sdvxin.command(hidden=True)
    async def fullsearch(self, ctx, *, query):
        """ Searches for a SDVX song title, no limit on multiple results. """
        await _search(ctx, query, True)

    @sdvxin.command()
    async def search(self, ctx, *, query):
        """ Searches for a SDVX song title. """
        await _search(ctx, query)


async def _search(ctx, query, list_all=False):
    query = query.lower()
    if not query:
        return

    # Search database
    result = collections.defaultdict(list)
    for song_id in DB.index:
        if DB.loc[song_id].sdvxin_id == '':
            continue
        strings = get_aliases(song_id)

        result['ratio'].append((max([fuzz.ratio(query, s) for s in strings]), song_id))
        partial_result = [fuzz.partial_ratio(query, s) for s in strings if len(s) >= len(query)]
        if partial_result:
            result['partial'].append((max(partial_result), song_id))

    # Filter out results
    # Pick a result if there's only 1 outcome for "ratio"
    # Otherwise, use "partial"
    result['ratio'] = [e for e in result['ratio'] if e[0] >= MIN_RATIO_CONFIDENCE]
    result['ratio'].sort(reverse=True)
    result['ratio'] = [e for e in result['ratio'] if result['ratio'][0][0] - e[0] <= CONFIDENCE_INTERVAL]

    if len(result['ratio']) == 1:
        song_id = result['ratio'][0][1]
        await send_result(ctx, song_id)
        return

    result['partial'].sort(reverse=True)
    result['partial'] = [e for e in result['partial'] if result['partial'][0][0] - e[0] <= CONFIDENCE_INTERVAL]

    if len(result['partial']) == 0:
        embed = Embed(title='No results found!')
        embed.set_author(name=f'Results for query "{query}":')
        embed.set_footer(text='Powered by sdvx.in')
        await ctx.send(embed=embed)

    if len(result['partial']) == 1:
        song_id = result['partial'][0][1]
        await send_result(ctx, song_id)
        return

    if len(result['partial']) <= 5 or list_all:
        text = '\n'.join([f'**{escape_markdown(DB.loc[e[1]].song_name)}** ({DB.loc[e[1]].sdvxin_id})' for e in result['partial']])

        embed = Embed(title='Multiple results -- refine query or provide song ID.', description=text)
        embed.set_author(name=f'Results for query "{query}":')
        embed.set_footer(text='Powered by sdvx.in')
        await ctx.send(embed=embed)
    else:
        embed = Embed(title='Too many results! Please refine your query.')
        embed.set_author(name=f'Results for query "{query}":')
        embed.set_footer(text='Powered by sdvx.in')
        await ctx.send(embed=embed)


async def send_result(ctx, song_id):
    d = DB.loc[song_id]
    suffix = 'e.png' if d.difficulties[3] == 0 else 'm.png'
    diff_names = [BASE_DIFF_NAMES[i] for i, lv in enumerate(d.difficulties)]
    urls = [BASE_DIFF_SUFFIX[i] for i, lv in enumerate(d.difficulties)]
    urls = ['/'.join([BASE_DOMAIN, d.ver_path[0], d.sdvxin_id + s + '.htm']) for s in urls]

    if d.difficulties[4] != 0:
        diff_names[4] = EXTRA_DIFF_NAMES[d.inf_ver]
        urls[4] = '/'.join([BASE_DOMAIN,
                            d.ver_path[1] or d.ver_path[0],
                            d.sdvxin_id + EXTRA_DIFF_SUFFIX[d.inf_ver] + '.htm'])

    links = []
    for dn, lv, url in zip(diff_names, d.difficulties, urls):
        if lv == 0:
            continue
        links.append(f'[{dn} {lv}]({url})')

    embed = Embed(title=d.song_artist, description=' - '.join(links))
    embed.set_author(name=f'{d.song_name} ({d.sdvxin_id})')
    embed.set_thumbnail(url='/'.join([BASE_DOMAIN, d.ver_path[0], 'jacket', d.sdvxin_id + suffix]))
    embed.set_footer(text='Powered by sdvx.in')
    await ctx.send(embed=embed)


def get_aliases(song_id):
    data = DB.loc[song_id]
    strings = [data.sdvxin_id, data.song_name] + data.song_name_alt
    if data.song_name.isascii():
        strings.append(re.sub('[^a-zA-Z0-9]', ' ', data.song_name))
    return [s.lower() for s in strings]


def refresh_database():
    global DB
    DB = pandas.read_json(DB_PATH, orient='index')


def setup(bot):
    bot.add_cog(SdvxInLinker())
