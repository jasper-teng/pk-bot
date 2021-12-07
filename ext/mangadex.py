import io
import math
import requests

from discord import File
from discord.ext import commands

LAST_MESSAGE = None


@commands.group()
async def mangadex(ctx):
    """ Mangadex related commands """
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid subcommand.', delete_after=5)


@mangadex.command()
async def search(ctx, *, raw_query):
    """ Searches mangas. Optionally, provide page number after query, separated with | """
    chunks = raw_query.split('|')
    if len(chunks) == 0:
        await ctx.message.add_reaction('🆖')
        return
    elif len(chunks) == 1:
        query = chunks[0]
        page = 1
    else:
        query = chunks[0]
        page = int(chunks[1])

    params = {
        'limit': 10,
        'offset': 10 * (page - 1),
        'title': query,
        'order[updatedAt]': 'desc'
    }
    result = requests.get('https://api.mangadex.org/manga', params).json()

    out = [f'Page {page} of {math.ceil(result["total"] / 10)}', '']

    for manga in result['results']:
        out.append(f'{manga["data"]["attributes"]["title"]}')
        out.append(f'    ID: {manga["data"]["id"]}')

    await ctx.send('```' + '\n'.join(out) + '```')


@mangadex.command(name='list')
async def chapter_list(ctx, manga_id, page=1):
    """ Lists manga chapters """
    params = {
        'limit': 10,
        'offset': 10 * (page - 1),
        'order[chapter]': 'desc'
    }
    result = requests.get(f'https://api.mangadex.org/manga/{manga_id}/feed', params).json()

    out = [f'Page {page} of {math.ceil(result["total"] / 10)}', '']

    for chapter in result['results']:
        out.append(f'V.{chapter["data"]["attributes"]["volume"]} '
                   f'C.{chapter["data"]["attributes"]["chapter"]} '
                   f'{chapter["data"]["attributes"]["title"]}')
        out.append(f'    ID: {chapter["data"]["id"]}')

    await ctx.send('```' + '\n'.join(out) + '```')


@mangadex.command()
async def show(ctx, chapter_id, *page):
    """ Display chapter pages """
    global LAST_MESSAGE

    params = {
        'ids[0]': chapter_id
    }
    result = requests.get('https://api.mangadex.org/chapter', params).json()
    chapter_hash = result['results'][0]['data']['attributes']['hash']
    pages = result['results'][0]['data']['attributes']['dataSaver']

    result = requests.get(f'https://api.mangadex.org/at-home/server/{chapter_id}').json()
    base_url = result['baseUrl']

    chapter_pages = []
    if not page:
        for purl in pages:
            result = requests.get(f'{base_url}/data-saver/{chapter_hash}/{purl}').content
            chapter_pages.append(File(io.BytesIO(result), purl))
    else:
        for pnum in page:
            try:
                purl = pages[int(pnum) - 1]
                result = requests.get(f'{base_url}/data-saver/{chapter_hash}/{purl}').content
                chapter_pages.append(File(io.BytesIO(result), purl))
            except IndexError:
                pass

    if chapter_pages:
        if LAST_MESSAGE is not None:
            await LAST_MESSAGE.delete()

        LAST_MESSAGE = await ctx.send(files=chapter_pages)
    else:
        await ctx.message.add_reaction('🆖')


def setup(bot):
    bot.add_command(mangadex)
