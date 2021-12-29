import asyncio
import json
import os
import subprocess
import ext._scraper as scraper

from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv

# Script constant
load_dotenv()
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))
VIEWER_DIR = os.path.join('..', 'sdvx-score-viewer')
ASSOC_JSON = os.path.join('ext', 'register.json')
DEVNULL = subprocess.DEVNULL


class LocalViewer(commands.Cog, name='Score Viewer'):
    def __init__(self):
        # global state
        try:
            with open(ASSOC_JSON, 'r') as f:
                self._assoc_obj = json.load(f)
        except IOError:
            self._assoc_obj = {}
        self._process_count = 0
        self._score_queued = asyncio.Event()
        self._score_queued.set()
        self._max_output_lines = 15

    @commands.group()
    async def viewer(self, ctx):
        """ Score viewer related commands """
        if ctx.invoked_subcommand is None:
            pass

    @viewer.command()
    async def register(self, ctx, sdvxid=None):
        """ Associate an SDVX ID with your Discord account. """
        stored_id = self._assoc_obj.get(str(ctx.author.id))
        if sdvxid is None:
            if stored_id is None:
                embed = Embed(title='SDVX score scraper',
                              description='You haven\'t registered a SDVX ID yet.',
                              delete_after=10)
                await ctx.reply(embed=embed)
            else:
                embed = Embed(title='SDVX score scraper',
                              description=f'Your registered SDVX ID is {stored_id}.')
                await ctx.reply(embed=embed)
        else:
            validatedid = scraper.is_sdvx_id(sdvxid)
            if not validatedid:
                embed = Embed(title='SDVX score scraper',
                              description=f'{sdvxid} isn\'t a valid SDVX ID.',
                              delete_after=10)
                await ctx.reply(embed=embed)
            else:
                self._assoc_obj[str(ctx.author.id)] = validatedid
                embed = Embed(title='SDVX score scraper',
                              description=f'Your registered SDVX ID is now {validatedid}.')
                await ctx.reply(embed=embed)
                with open(ASSOC_JSON, 'w') as f:
                    json.dump(self._assoc_obj, f)

    @viewer.command(aliases=['scoreupdate', 'u'])
    async def update(self, ctx, *args):
        """
        Updates the user's scores in the viewer.

        Update may fail if:
        - Profile does not exist
        - Score data is not set to be publicly visible
        - Website is down for maintenance

        Provide 'preview' as an argument to scrape data but not save it ("dry run").
        """
        is_preview = 'preview' in args

        if self._assoc_obj.get(str(ctx.author.id)) is None:
            await ctx.message.add_reaction('⛔')
            await ctx.reply('Register your SDVX ID first with `-viewer register`!', delete_after=10)
            return
        self._process_count += 1
        self._score_queued.clear()

        import time
        cur_time = time.localtime()
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', cur_time)

        embed = Embed(title='SDVX score scraper',
                      description=f'Automated score update initiated at '
                                  f'{time_str}{"" if not is_preview else " (PREVIEW mode)"}.')
        message = await ctx.send(embed=embed)
        sdvx_id = self._assoc_obj.get(str(ctx.author.id))

        try:
            output = await scraper.update_score(message, sdvx_id, preview=is_preview)
        except Exception as e:
            self._process_count -= 1
            if self._process_count == 0:
                self._score_queued.set()
            raise e

        if not is_preview:
            subprocess.call('git add scores/.', stdout=DEVNULL, cwd=VIEWER_DIR)
            subprocess.call(f'git commit scores/. -m '
                            f'"automated score update ({time.strftime("%Y%m%d%H%M%S", cur_time)})"',
                            stdout=DEVNULL, cwd=VIEWER_DIR)
            subprocess.call('git push --porcelain', stdout=DEVNULL, stderr=DEVNULL, cwd=VIEWER_DIR)

        desc = (f'Automated score update finished. '
                f'{len(output["new_entry"])} new {"entry" if len(output["new_entry"]) == 1 else "entries"} '
                f'{"saved" if not is_preview else "found"}.')
        if len(output["new_entry"]) > 0:
            if is_preview:
                desc += '\n\n' + 'New entries to be added:'
            else:
                desc += '\n\n' + 'New entries added:'
            for sstr in output['new_entry'][:self._max_output_lines]:
                desc += f'\n- {sstr}'
            if len(output['new_entry']) > self._max_output_lines:
                entry_word = 'entry' if (len(output['new_entry']) == self._max_output_lines + 1) else 'entries'
                desc += f'\n... ({len(output["new_entry"]) - self._max_output_lines} {entry_word} omitted)'
        if len(output['skipped']) > 0:
            desc += '\n\n' + 'While scraping data, the following song(s) are missing from the database:'
            for sn, sa in output['skipped']:
                desc += f'\n- {sn} / {sa}'

        embed = Embed(title='SDVX score scraper', description=desc)
        await ctx.reply(embed=embed)
        await message.delete(delay=10)

        self._process_count -= 1
        if self._process_count == 0:
            self._score_queued.set()


def setup(bot):
    bot.add_cog(LocalViewer())
