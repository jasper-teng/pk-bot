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

# TODO: use async requests, fix relative paths


@commands.group()
async def viewer(ctx):
    """ Score viewer related commands """
    if IS_PROCESSING:
        await ctx.message.add_reaction('⛔')
        return

    if ctx.invoked_subcommand is None:
        pass


@viewer.command()
async def updatescore(ctx, *sdvx_ids):
    """ Updates the scores in the viewer """
    IS_PROCESSING = True

    import time
    cur_time = time.localtime()
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

    embed = Embed(title='SDVX score scraper', description=f'Automated score update initiated at {time_str}.')
    message = await ctx.send(embed=embed)

    os.chdir(os.path.join('..', 'sdvx-score-viewer'))
    await update_score(message, sdvx_ids)

    subprocess.call('git add scores/.', stdout=subprocess.DEVNULL)
    subprocess.call(f'git commit scores/. -m "automated score update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"', stdout=subprocess.DEVNULL)
    subprocess.call('git push', stdout=subprocess.DEVNULL)

    embed = Embed(title='SDVX score scraper', description='Automated score update finished.')
    await ctx.send(embed=embed)
    await message.delete(delay=10)

    os.chdir(os.path.join('..', 'pk-bot'))
    IS_PROCESSING = False


@viewer.command()
@commands.has_role(ROLE_ID)
async def updatesongs(ctx, is_full_update=False):
    """ Updates the song database in the viewer """
    IS_PROCESSING = True

    import time
    cur_time = time.localtime()
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

    embed = Embed(title='SDVX score scraper', description=f'Automated song database update initiated at {time_str}.')
    message = await ctx.send(embed=embed)

    os.chdir(os.path.join('..', 'sdvx-score-viewer'))
    new_songs = await update_songs(is_full_update)

    subprocess.call(f'git commit song_db.json -m "automated song db update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"', stdout=subprocess.DEVNULL)
    subprocess.call('git push', stdout=subprocess.DEVNULL)

    desc = ['Automated song database update finished. Added the following songs:']
    for song_data in new_songs:
        desc.append(f'- {song_data["song_name"]} / {song_data["song_artist"]}')
    embed = Embed(title='SDVX score scraper', description='\n'.join(desc))
    await message.edit(embed=embed)

    os.chdir(os.path.join('..', 'pk-bot'))
    IS_PROCESSING = False


def setup(bot):
    bot.add_command(viewer)
