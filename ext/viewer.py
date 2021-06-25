import os
import subprocess
import time

from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv
from ext._scraper import update_score, update_songs

IS_PROCESSING = False

load_dotenv()
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))
VIEWER_DIR = os.path.join('..', 'sdvx-score-viewer')
DEVNULL = subprocess.DEVNULL
EVENT_LOOP = None

# TODO: handle scrape failures more gracefully


@commands.group()
async def viewer(ctx):
    """ Score viewer related commands """
    if ctx.invoked_subcommand is None:
        pass


@viewer.command()
async def scoreupdate(ctx, *sdvx_ids):
    """ Updates the scores in the viewer """
    global IS_PROCESSING

    if IS_PROCESSING:
        await ctx.message.add_reaction('⛔')
        await ctx.send('Please wait until the currently running process finishes.', delete_after=10)
        return
    IS_PROCESSING = True

    import time
    cur_time = time.localtime()
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

    embed = Embed(title='SDVX score scraper', description=f'Automated score update initiated at {time_str}.')
    message = await ctx.send(embed=embed)

    try:
        await update_score(message, EVENT_LOOP, sdvx_ids)
    except Exception as e:
        IS_PROCESSING = False
        raise e

    subprocess.call('git add scores/.', stdout=DEVNULL, cwd=VIEWER_DIR)
    subprocess.call(f'git commit scores/. -m "automated score update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"', stdout=DEVNULL, cwd=VIEWER_DIR)
    subprocess.call('git push --porcelain', stdout=DEVNULL, cwd=VIEWER_DIR)

    embed = Embed(title='SDVX score scraper', description='Automated score update finished.')
    await ctx.send(embed=embed)
    await message.delete(delay=10)

    IS_PROCESSING = False


@viewer.command()
@commands.has_role(ROLE_ID)
async def songupdate(ctx, is_full_update=False):
    """ Updates the song database in the viewer """
    global IS_PROCESSING

    if IS_PROCESSING:
        await ctx.message.add_reaction('⛔')
        await ctx.send('Please wait until the currently running process finishes.', delete_after=10)
        return
    IS_PROCESSING = True

    import time
    cur_time = time.localtime()
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

    embed = Embed(title='SDVX score scraper', description=f'Automated song database update initiated at {time_str}.')
    message = await ctx.send(embed=embed)

    try:
        new_songs = await update_songs(EVENT_LOOP, is_full_update)
    except Exception as e:
        IS_PROCESSING = False
        raise e

    subprocess.call(f'git commit song_db.json -m "automated song db update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"', stdout=DEVNULL, cwd=VIEWER_DIR)
    subprocess.call('git push --porcelain', stdout=DEVNULL, cwd=VIEWER_DIR)

    if new_songs:
        desc = ['Automated song database update finished. Added the following songs:']
    else:
        desc = ['Automated song database update finished. No new songs added.']

    for song_data in new_songs:
        desc.append(f'- {song_data["song_name"]} / {song_data["song_artist"]}')
    embed = Embed(title='SDVX score scraper', description='\n'.join(desc))
    await message.edit(embed=embed)

    IS_PROCESSING = False


def setup(bot):
    bot.add_command(viewer)
    EVENT_LOOP = bot.loop
