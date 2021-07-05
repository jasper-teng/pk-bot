import asyncio
import os
import subprocess
import time

from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv
from ext._scraper import update_score, update_songs

# Global state
IS_PROCESSING = 0
SCORE_QUEUED = asyncio.Event()
SCORE_QUEUED.set()

# Script constant
PROCESS_SONG = 1
PROCESS_SCORE = 2

load_dotenv()
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))
VIEWER_DIR = os.path.join('..', 'sdvx-score-viewer')
DEVNULL = subprocess.DEVNULL


@commands.group()
async def viewer(ctx):
    """ Score viewer related commands """
    if ctx.invoked_subcommand is None:
        pass


@viewer.command()
async def scoreupdate(ctx, *sdvx_ids):
    """
    Updates the scores in the viewer.
    
    Send command with no arguments to update all scores in the database.
    """
    global IS_PROCESSING, SCORE_QUEUED

    if IS_PROCESSING == PROCESS_SCORE:
        await ctx.reply('This request is now queued.')
        await SCORE_QUEUED.wait()
    elif IS_PROCESSING == PROCESS_SONG:
        await ctx.message.add_reaction('⛔')
        await ctx.send('Please wait until the currently running process finishes.', delete_after=10)
        return
    IS_PROCESSING = PROCESS_SCORE
    SCORE_QUEUED.clear()

    import time
    cur_time = time.localtime()
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

    embed = Embed(title='SDVX score scraper', description=f'Automated score update initiated at {time_str}.')
    message = await ctx.send(embed=embed)

    try:
        await update_score(message, sdvx_ids)
    except Exception as e:
        IS_PROCESSING = 0
        SCORE_QUEUED.set()
        raise e

    subprocess.call('git add scores/.', stdout=DEVNULL, cwd=VIEWER_DIR)
    subprocess.call(f'git commit scores/. -m "automated score update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"', stdout=DEVNULL, cwd=VIEWER_DIR)
    subprocess.call('git push --porcelain', stdout=DEVNULL, stderr=DEVNULL, cwd=VIEWER_DIR)

    embed = Embed(title='SDVX score scraper', description='Automated score update finished.')
    await ctx.reply(embed=embed)
    await message.delete(delay=10)

    IS_PROCESSING = 0
    SCORE_QUEUED.set()


@viewer.command()
@commands.has_role(ROLE_ID)
async def songupdate(ctx, is_full_update=False):
    """ Updates the song database in the viewer. """
    global IS_PROCESSING

    if IS_PROCESSING:
        await ctx.message.add_reaction('⛔')
        await ctx.send('Please wait until the currently running process finishes.', delete_after=10)
        return
    IS_PROCESSING = PROCESS_SONG

    import time
    cur_time = time.localtime()
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

    embed = Embed(title='SDVX score scraper', description=f'Automated song database update initiated at {time_str}.')
    message = await ctx.send(embed=embed)

    try:
        new_songs = await update_songs(is_full_update)
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
    bot.add_command(viewer)
