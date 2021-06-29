import collections
import json
import os
import pprint
import re

from discord import Embed
from discord.ext import commands
from discord.utils import escape_markdown
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

CONFIDENCE_INTERVAL = 5
MIN_RATIO_CONFIDENCE = 85
BASE_DOMAIN = 'https://sdvx.in'
BASE_DIFF_NAMES = ['NOV', 'ADV', 'EXH', '', 'MXM']
BASE_DIFF_SUFFIX = ['n', 'a', 'e', '', 'm']
EXTRA_DIFF_NAMES = ['', 'INF', 'GRV', 'HVN', 'VVD']
EXTRA_DIFF_SUFFIX= ['', 'i', 'g', 'h', 'v']

load_dotenv()
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))


@commands.group(invoke_without_command=True, aliases=['sdvx'])
async def sdvxin(ctx, *args):
    """ SDVX.in related commands """
    if ctx.invoked_subcommand is None:
        await search(ctx, query=' '.join(args))


@sdvxin.command(hidden=True)
async def fullsearch(ctx, *, query):
    """ Searches for a SDVX song title, no limit on multiple results. """
    await _search(ctx, query, True)


@sdvxin.command()
async def search(ctx, *, query):
    """ Searches for a SDVX song title. """
    await _search(ctx, query)


async def _search(ctx, query, list_all=False):
    query = query.lower()
    if not query:
        return

    # Search database
    result = collections.defaultdict(list)
    for song_id in song_db:
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
        text = '\n'.join([f'**{escape_markdown(song_db[e[1]]["title"])}** ({e[1]})' for e in result['partial']])

        embed = Embed(title='Multiple results -- refine query or provide song ID.', description=text)
        embed.set_author(name=f'Results for query "{query}":')
        embed.set_footer(text='Powered by sdvx.in')
        await ctx.send(embed=embed)
    else:
        embed = Embed(title='Too many results! Please refine your query.')
        embed.set_author(name=f'Results for query "{query}":')
        embed.set_footer(text='Powered by sdvx.in')
        await ctx.send(embed=embed)


@sdvxin.command(hidden=True)
@commands.has_role(ROLE_ID)
async def listalias(ctx, *, song_id):
    aliases = get_aliases(song_id)
    text = '\n'.join([f'"{escape_markdown(e)}"' for e in aliases])

    embed = Embed(title=f'Aliases for {song_db[song_id]["title"]} ({song_id}):', description=text)
    embed.set_footer(text='Powered by sdvx.in')
    await ctx.send(embed=embed)


@sdvxin.command(hidden=True)
@commands.has_role(ROLE_ID)
async def addalias(ctx, song_id, new_alias):
    d = song_db[song_id]
    if not new_alias.isascii():
        raise ValueError(f'Alias must be ASCII only. (got "{new_alias}")')
    d['alt_title'].append(new_alias)
    save_database()
    print(f'<SDVXIN> Added new alias for ID {song_id}.')

    embed = Embed(title=f'Alias "{new_alias}" added for {d["title"]} ({song_id}).')
    embed.set_footer(text='Powered by sdvx.in')
    await ctx.send(embed=embed)


@sdvxin.command(hidden=True)
@commands.has_role(ROLE_ID)
async def addsong(ctx, song_id, *, json_string):
    if song_id in song_db:
        raise ValueError(f'ID already exists.')

    # Data must at least have:
    # - title
    # - artist
    # - levels
    # Optional:
    # - alt_title (assumed to be [] if not provided)
    # - extra_diff (assumed to be 0 if not provided)
    # - version (will be extracted from song_id if not provided)

    d = json.loads(json_string)
    if not ('title' in d and 'artist' in d and 'levels' in d):
        raise IndexError('Song data missing required fields (title, artist, levels).')

    sd = {
        'title'     : d['title'],
        'artist'    : d['artist'],
        'levels'    : d['levels'],
        'alt_title' : d.get('alt_title', []),
        'extra_diff': d.get('extra_diff', 0),
        'version'   : d.get('alt_title', [song_id[:2], ''])
    }

    song_db[song_id] = sd
    save_database()
    print(f'<SDVXIN> Added new song entry with ID {song_id}.')

    embed = Embed(title=f'New song entry added (ID {song_id}).', description=pprint.pformat(sd))
    embed.set_footer(text='Powered by sdvx.in')
    await ctx.send(embed=embed)


@sdvxin.command(hidden=True)
@commands.has_role(ROLE_ID)
async def overridefield(ctx, song_id, *, json_string):
    if song_id not in song_db:
        raise ValueError(f'ID does not exist.')

    # Allowed fields:
    # - title
    # - artist
    # - levels
    # - alt_title (assumed to be [] if not provided)
    # - extra_diff (assumed to be 0 if not provided)
    # - version (will be extracted from song_id if not provided)
    valid_fields = ['title', 'artist', 'levels', 'alt_title', 'extra_diff', 'version']

    d = json.loads(json_string)
    d = {k: d[k] for k in valid_fields if k in d}

    for k, v in d.items():
        song_db[song_id][k] = v

    save_database()
    print(f'<SDVXIN> Overwrote fields {list(d.keys())} in ID {song_id}.')

    embed = Embed(title=f'Overwrote the following fields in ID {song_id}.', description=pprint.pformat(d))
    embed.set_footer(text='Powered by sdvx.in')
    await ctx.send(embed=embed)


async def send_result(ctx, song_id):
    d = song_db[song_id]
    suffix = 'e.png' if d['levels'][4] == 0 else 'm.png'
    diff_names = [BASE_DIFF_NAMES[i] for i, lv in enumerate(d['levels']) if lv != 0]
    urls = [BASE_DIFF_SUFFIX[i] for i, lv in enumerate(d['levels']) if lv != 0]
    urls = ['/'.join([BASE_DOMAIN, d['version'][0], song_id + s + '.htm']) for s in urls]

    if d['levels'][3] != 0:
        diff_names[3] = EXTRA_DIFF_NAMES[d['extra_diff']]
        urls[3] = '/'.join([BASE_DOMAIN, d['version'][1], song_id + EXTRA_DIFF_SUFFIX[d['extra_diff']] + '.htm'])

    links = []
    for dn, lv, url in zip(diff_names, filter(None, d['levels']), urls):
        links.append(f'[{dn} {lv}]({url})')

    embed = Embed(title=d['artist'], description=' - '.join(links))
    embed.set_author(name=f'{d["title"]} ({song_id})')
    embed.set_thumbnail(url='/'.join([BASE_DOMAIN, d['version'][0], 'jacket', song_id + suffix]))
    embed.set_footer(text='Powered by sdvx.in')
    await ctx.send(embed=embed)


def setup(bot):
    bot.add_command(sdvxin)


def get_aliases(song_id):
    data = song_db[song_id]
    strings = [song_id, data['title']] + data['alt_title']
    if data['title'].isascii():
        strings.append(re.sub('[^a-zA-Z0-9]', ' ', data['title']))
    return [s.lower() for s in strings]


def save_database():
    with open('ext/sdvxin_db.json', 'w') as f:
        json.dump(song_db, f)


with open('ext/sdvxin_db.json', 'r') as f:
    song_db = json.load(f)
