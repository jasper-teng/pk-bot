import asyncio
import json
import os
import subprocess
import time
import ext._scraper as scraper

from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv

# Global state
IS_PROCESSING = 0
PROCESS_COUNT = 0
SCORE_QUEUED = asyncio.Event()
SCORE_QUEUED.set()

# Script constant
PROCESS_SONG = 1
PROCESS_SCORE = 2

load_dotenv()
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))
VIEWER_DIR = os.path.join('..', 'sdvx-score-viewer')
ASSOC_JSON = os.path.join('ext', 'register.json')
ASSOC_OBJ = None
DEVNULL = subprocess.DEVNULL


@commands.group()
async def viewer(ctx):
    """ Score viewer related commands """
    if ctx.invoked_subcommand is None:
        pass


@viewer.command()
async def register(ctx, sdvxid=None):
    global ASSOC_OBJ

    stored_id = ASSOC_OBJ.get(str(ctx.author.id))
    if sdvxid is None:
        if stored_id is None:
            embed = Embed(title='SDVX score scraper', description='You haven\'t registered a SDVX ID yet.', delete_after=10)
            await ctx.reply(embed=embed)
        else:
            embed = Embed(title='SDVX score scraper', description=f'Your registered SDVX ID is {stored_id}.')
            await ctx.reply(embed=embed)
    else:
        validatedid = scraper.is_sdvx_id(sdvxid)
        if not validatedid:
            embed = Embed(title='SDVX score scraper', description=f'{sdvxid} isn\'t a valid SDVX ID.', delete_after=10)
            await ctx.reply(embed=embed)
        else:
            ASSOC_OBJ[str(ctx.author.id)] = validatedid
            embed = Embed(title='SDVX score scraper', description=f'Your registered SDVX ID is now {validatedid}.')
            await ctx.reply(embed=embed)
            with open(ASSOC_JSON, 'w') as f:
                json.dump(ASSOC_OBJ, f)


@viewer.command()
async def scoreupdate(ctx):
    """
    Updates the user's scores in the viewer.
    
    Update may fail if:
    - Profile does not exist
    - Score data is not set to be publicly visible
    - Website is down for maintenance
    """
    global IS_PROCESSING, SCORE_QUEUED, ASSOC_OBJ, PROCESS_COUNT

    if ASSOC_OBJ.get(str(ctx.author.id)) is None:
        await ctx.message.add_reaction('⛔')
        await ctx.reply('Register your SDVX ID first with `-viewer register`!', delete_after=10)
        return
    # elif IS_PROCESSING == PROCESS_SCORE:
        # await ctx.reply('This request is now queued.')
        # await SCORE_QUEUED.wait()
    elif IS_PROCESSING == PROCESS_SONG:
        await ctx.message.add_reaction('⛔')
        await ctx.reply('Please wait until the currently running process finishes.', delete_after=10)
        return
    IS_PROCESSING = PROCESS_SCORE
    PROCESS_COUNT += 1
    SCORE_QUEUED.clear()

    import time
    cur_time = time.localtime()
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

    embed = Embed(title='SDVX score scraper', description=f'Automated score update initiated at {time_str}.')
    message = await ctx.send(embed=embed)
    sdvx_id = ASSOC_OBJ.get(str(ctx.author.id))

    try:
        output = await scraper.update_score(message, sdvx_id)
    except Exception as e:
        PROCESS_COUNT -= 1
        if PROCESS_COUNT == 0:
            IS_PROCESSING = 0
            SCORE_QUEUED.set()
        raise e

    subprocess.call('git add scores/.', stdout=DEVNULL, cwd=VIEWER_DIR)
    subprocess.call(f'git commit scores/. -m "automated score update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"', stdout=DEVNULL, cwd=VIEWER_DIR)
    subprocess.call('git push --porcelain', stdout=DEVNULL, stderr=DEVNULL, cwd=VIEWER_DIR)

    desc = f'Automated score update finished. {output["new_count"]} new {"entry" if output["new_count"] == 1 else "entries"} saved.'
    if len(output['skipped']) > 0:
        desc += '\n\n' + 'While scraping data, the following song(s) are missing from the database:'
        for sn, sa in output['skipped']:
            desc += f'\n- {sn} / {sa}'

    embed = Embed(title='SDVX score scraper', description=desc)
    await ctx.reply(embed=embed)
    await message.delete(delay=10)

    PROCESS_COUNT -= 1
    if PROCESS_COUNT == 0:
        IS_PROCESSING = 0
        SCORE_QUEUED.set()


@viewer.command()
@commands.has_role(ROLE_ID)
async def songupdate(ctx, is_full_update=False):
    """ Updates the song database in the viewer. """
    global IS_PROCESSING, PROCESS_COUNT

    if IS_PROCESSING:
        await ctx.message.add_reaction('⛔')
        await ctx.send(f'Please wait until the currently running process ({PROCESS_COUNT}) finishes.', delete_after=10)
        return
    IS_PROCESSING = PROCESS_SONG

    import time
    cur_time = time.localtime()
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

    embed = Embed(title='SDVX score scraper', description=f'Automated song database update initiated at {time_str}.')
    message = await ctx.send(embed=embed)

    try:
        new_songs = await scraper.update_songs(is_full_update)
    except Exception as e:
        IS_PROCESSING = 0
        raise e

    subprocess.call(f'git commit song_db.json -m "automated song db update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"', stdout=DEVNULL, cwd=VIEWER_DIR)
    subprocess.call('git push --porcelain', stdout=DEVNULL, stderr=DEVNULL, cwd=VIEWER_DIR)

    if new_songs:
        desc = ['Automated song database update finished. Added the following songs:']
    else:
        desc = ['Automated song database update finished. No new songs added.']

    for song_data in new_songs:
        desc.append(f'- {song_data["song_name"]} / {song_data["song_artist"]}')
    embed = Embed(title='SDVX score scraper', description='\n'.join(desc))
    await message.edit(embed=embed)

    IS_PROCESSING = 0


def setup(bot):
    global ASSOC_OBJ
    try:
        with open(ASSOC_JSON, 'r') as f:
            ASSOC_OBJ = json.load(f)
    except IOError:
        ASSOC_OBJ = {}
    bot.add_command(viewer)
