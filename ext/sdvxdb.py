import json
import os
import pandas
import pprint
import subprocess
import time
import ext._scraper as scraper

from discord import Embed
from discord.ext import commands
from discord.utils import escape_markdown
from dotenv import load_dotenv
from ext.sdvxin import refresh_database

load_dotenv()
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))
DB_DIR = os.path.join('..', 'sdvx-db')
DB_PATH = os.path.join(DB_DIR, 'db.json')
DB = pandas.read_json(DB_PATH, orient='index')
DEVNULL = subprocess.DEVNULL


class SdvxDatabase(commands.Cog, name='SDVX Database'):
    @commands.group(invoke_without_command=True)
    async def svdb(self, ctx, *args):
        """ SDVX database maintenance commands """
        if ctx.invoked_subcommand is None:
            pass

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def update(self, ctx, is_full_update=False):
        """ Updates the song database. """
        cur_time = time.localtime()
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

        embed = Embed(description=f'Automated song database update initiated at {time_str}.')
        embed.set_author(name='SDVX database handler')
        message = await ctx.send(embed=embed)

        new_songs = await scraper.update_songs(is_full_update)

        if len(new_songs) > 0:
            print(f'<SDVXDB> Updated database with scraped data ({len(new_songs)} entry(s)).')
            desc = ['Automated song database update finished. Added the following songs:']
        else:
            desc = ['Automated song database update finished. No new songs added.']

        for song_data in new_songs:
            desc.append(f'- {song_data["song_name"]} / {song_data["song_artist"]}')
        embed = Embed(description='\n'.join(desc))
        embed.set_author(name='SDVX database handler')
        refresh_database()
        await message.edit(embed=embed)

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def link(self, ctx, song_id, sdvxin_id):
        """ Attaches a SDVX.in ID to a song entry. """
        song_id = int(song_id)
        res = DB.loc[DB['sdvxin_id'] == sdvxin_id]
        if len(res) == 1:
            embed = Embed(title=f'Results for ID query "{sdvxin_id}":',
                          description=f'Song with ID {sdvxin_id} already exists!')
            embed.set_author(name='SDVX database handler')
            await ctx.send(embed=embed)
            return

        if DB.loc[song_id].sdvxin_id == '':
            desc = ''
        else:
            desc = f'\n\n**WARNING**: This overwrote existing SDVX.in ID {DB.loc[song_id].sdvxin_id}'
        DB.loc[song_id, 'sdvxin_id'] = sdvxin_id
        DB.loc[song_id, 'ver_path'] = [[sdvxin_id[:2]], ['']]
        save_database()
        refresh_database()
        print(f'<SDVXDB> Linked song entry ID {song_id} with SDVX.in ID {sdvxin_id}.')

        embed = Embed(description=f'New song entry linked:\n{DB.loc[song_id].song_name} / {DB.loc[song_id].song_artist} ({song_id} <-> {sdvxin_id}).' + desc)
        embed.set_author(name='SDVX database handler')
        await ctx.send(embed=embed)

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def unlinked(self, ctx):
        """ Finds all song entries that are not linked to a SDVX.in entry. """
        songs = DB.loc[DB['sdvxin_id'] == '']
        if len(songs) == 0:
            embed = Embed(title='Missing SDVX.in IDs:',
                          description='All songs are linked!')
            embed.set_author(name='SDVX database handler')
        else:
            desc = []
            for song in songs.itertuples():
                desc.append(f'- {song.song_name} / {song.song_artist} (ID {song.Index})')
            embed = Embed(title='Missing SDVX.in IDs:',
                          description='\n'.join(desc))
            embed.set_author(name='SDVX database handler')
            await ctx.send(embed=embed)

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def commit(self, ctx):
        """ Commits changes to the repository. """
        cur_time = time.localtime()
        subprocess.call(f'git commit db.json -m '
                        f'"song db update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"',
                        stdout=DEVNULL, cwd=DB_DIR)
        subprocess.call('git push --porcelain', stdout=DEVNULL, stderr=DEVNULL, cwd=DB_DIR)
        ctx.message.add_reaction('🆗')

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def addalias(self, ctx, sdvxin_id, *, new_alias):
        """ Adds a song title alias for a given song ID. """
        res = DB.loc[DB['sdvxin_id'] == sdvxin_id]
        if len(res) == 0:
            embed = Embed(title=f'Results for ID query "{sdvxin_id}":',
                          description=f'No song with ID {sdvxin_id} found!')
            embed.set_author(name='SDVX database handler')
            await ctx.send(embed=embed)
            return

        song_id = res.index[0]
        if not new_alias.isascii():
            raise ValueError(f'Alias must be ASCII only. (got "{new_alias}")')
        DB.loc[song_id, 'song_name_alt'].append(new_alias)
        save_database()
        refresh_database()
        print(f'<SDVXIN> Added new alias for ID {song_id}.')

        embed = Embed(description=f'Alias "{new_alias}" added for {DB.loc[song_id].song_name} ({sdvxin_id}).')
        embed.set_author(name='SDVX database handler')
        await ctx.send(embed=embed)

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def overridefield(self, ctx, sdvxin_id, *, json_string):
        """ Overwrites fields given a song ID. """
        res = DB.loc[DB['sdvxin_id'] == sdvxin_id]
        if len(res) == 0:
            embed = Embed(title=f'Results for ID query "{sdvxin_id}":',
                          description=f'No song with ID {sdvxin_id} found!')
            embed.set_author(name='SDVX database handler')
            await ctx.send(embed=embed)
            return

        song_id = res.index[0]
        valid_fields = DB.columns

        d = json.loads(json_string)
        d = {k: d[k] for k in valid_fields if k in d}

        for k, v in d.items():
            DB.loc[song_id, k] = v

        save_database()
        refresh_database()
        print(f'<SDVXDB> Overwrote fields {list(d.keys())} in ID {sdvxin_id}.')

        embed = Embed(description=f'Overwrote the following fields in ID {sdvxin_id}.\n\n' + pprint.pformat(d))
        embed.set_author(name='SDVX database handler')
        await ctx.send(embed=embed)


def save_database():
    DB.to_json(DB_PATH, orient='index')


def setup(bot):
    bot.add_cog(SdvxDatabase())
