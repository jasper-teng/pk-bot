import json
import pandas
import pprint
import time
import ext._scraper as scraper

from discord import Embed
from discord.ext import commands
from discord.utils import escape_markdown
from dotenv import load_dotenv

load_dotenv()
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))
DB_DIR = '../sdvx-db/'
DB = pandas.read_json('../sdvx-db/db.json')


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

        embed = Embed(title='SDVX database handler',
                      description=f'Automated song database update initiated at {time_str}.')
        message = await ctx.send(embed=embed)

        new_songs = await scraper.update_songs(is_full_update)

        if len(new_songs) > 0:
            print(f'<SDVXDB> Updated database with scraped data ({len(new_songs)} entry(s)).')
            desc = ['Automated song database update finished. Added the following songs:']
        else:
            desc = ['Automated song database update finished. No new songs added.']

        for song_data in new_songs:
            desc.append(f'- {song_data["song_name"]} / {song_data["song_artist"]}')
        embed = Embed(title='SDVX database handler', description='\n'.join(desc))
        await message.edit(embed=embed)

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def link(self, ctx, song_id, sdvxin_id):
        """ Attaches a sdvx.in ID to a song entry. """
        song_id = int(song_id)
        res = DB.loc[DB['sdvxin_id'] == sdvxin_id]
        if res.shape[0] == 1:
            embed = Embed(title=f'Song with ID {sdvxin_id} already exists!')
            embed.set_author(name=f'Results for ID query "{sdvxin_id}":')
            await ctx.send(embed=embed)
            return

        db.loc[song_id].sdvxin_id = sdvxin_id
        save_database()
        print(f'<SDVXDB> Linked song entry ID {song_id} with SDVX.in ID {sdvxin_id}.')

        embed = Embed(title='SDVX database handler',
                      desc=f'New song entry linked (ID {sdvxin_id}).')
        await ctx.send(embed=embed)

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def commit(self):
        """ Commits changes to the repository. """
        cur_time = time.localtime()
        subprocess.call(f'git commit db.json -m '
                        f'"automated song db update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"',
                        stdout=DEVNULL, cwd=DB_DIR)
        subprocess.call('git push --porcelain', stdout=DEVNULL, stderr=DEVNULL, cwd=DB_DIR)
        ctx.msg.add_reaction('🆗')

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def addalias(self, ctx, song_id, new_alias):
        """ Adds a song title alias for a given song ID. """
        song_id = int(song_id)
        res = DB.loc[DB['sdvxin_id'] == song_id]
        if res.shape[0] == 0:
            embed = Embed(title='SDVX database handler',
                          desc=f'No song with ID {song_id} found!')
            embed.set_author(name=f'Results for ID query "{song_id}":')
            await ctx.send(embed=embed)
            return

        song_id = res.index[0]
        if not new_alias.isascii():
            raise ValueError(f'Alias must be ASCII only. (got "{new_alias}")')
        DB.loc[song_id].song_name_alt.append(new_alias)
        save_database()
        print(f'<SDVXIN> Added new alias for ID {song_id}.')

        embed = Embed(title='SDVX database handler',
                      desc=f'Alias "{new_alias}" added for {DB.loc[song_id].song_name} ({song_id}).')
        await ctx.send(embed=embed)

    @svdb.command()
    @commands.has_role(ROLE_ID)
    async def overridefield(self, ctx, sdvxin_id, *, json_string):
        """ Overwrites fields given a song ID. """
        res = DB.loc[DB['sdvxin_id'] == sdvxin_id]
        if res.shape[0] == 0:
            embed = Embed(title='SDVX database handler',
                          desc=f'No song with ID {sdvxin_id} found!')
            embed.set_author(name=f'Results for ID query "{sdvxin_id}":')
            await ctx.send(embed=embed)
            return

        song_id = res.index[0]
        valid_fields = DB.columns

        d = json.loads(json_string)
        d = {k: d[k] for k in valid_fields if k in d}

        for k, v in d.items():
            song_db.loc[song_id][k] = v

        save_database()
        print(f'<SDVXDB> Overwrote fields {list(d.keys())} in ID {sdvxin_id}.')

        embed = Embed(title='SDVX database handler',
                      desc=f'Overwrote the following fields in ID {sdvxin_id}.\n\n' + pprint.pformat(d))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SdvxDatabase())
