import asyncio
import json
import requests
import time
import urllib.parse
from discord import Embed
from discord.ext import commands, tasks
from bs4 import BeautifulSoup


class Scheduler(commands.Cog):
    def __init__(self, bot):
        # load saved data
        self._bot = bot
        self._db_path = 'ext/scheduler_db.json'
        try:
            with open(self._db_path) as f:
                self._db = json.load(f)
        except IOError:
            self._db = {}

        # put tasks in a list
        self._tasks = [
            self.doratama
        ]

        # start them all
        for task in self._tasks:
            task.start()

    def cog_unload(self):
        # stop tasks when cog unloads
        for task in self._tasks:
            task.cancel()

    @tasks.loop(hours=1.0)
    async def doratama(self):
        last_ch = self._db.get('doratama:last_ch')

        url = 'https://ncode.syosetu.com/n4698cv/'
        r = requests.get(url,
                         headers={'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) '
                                                'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                'Chrome/51.0.2704.64 Safari/537.36'})
        soup = BeautifulSoup(r.text)
        chapters = soup.select('.subtitle')

        if last_ch is None:
            last_ch = len(chapters)

        desc = []
        for ch in chapters[last_ch:]:
            link = ch.select_one('a')
            rel_path = link['href']
            ch_url = urllib.parse.urljoin(url, rel_path)
            ch_text = ch.text.strip()
            desc.append(f'・ [{ch_text}]({ch_url})')

        if desc:
            embed = Embed.from_dict({
                    'title': 'New DoraTama chapter!',
                    'description': '\n'.join(desc),
                    'author': {
                        'name': '転生したらドラゴンの卵だった～最強以外目指さねぇ～',
                        'url': 'https://ncode.syosetu.com/n4698cv/',
                        'icon_url': 'https://static.syosetu.com/view/images/narou.ico?psawph'
                    }
            })
            channel = await self._bot.fetch_user(82495095084941312)
            await channel.send(embed=embed)

        self._db['doratama:last_ch'] = last_ch

    @doratama.before_loop
    async def doratama_before(self):
        # ensure task runs on the hour
        cur_time = time.time()
        secs_to_wait = (cur_time // 3600 + 1) * 3600
        await asyncio.sleep(secs_to_wait)

    @doratama.after_loop
    async def doratama_after(self):
        with open(self._db_path, 'w') as f:
            json.dump(self._db, f)


def setup(bot):
    bot.add_cog(Scheduler(bot))
