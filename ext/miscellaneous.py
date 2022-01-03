import collections
import random
import time
from discord import File, DeletedReferencedMessage
from discord.ext import commands
from discord.utils import escape_markdown


class Images(commands.Cog):
    def __init__(self):
        self._denzel = 0
        self._hydrate = 0

    @staticmethod
    async def send_image(ctx, img_path):
        msg = ctx.message
        if msg.reference is None or isinstance(msg.reference.resolved, DeletedReferencedMessage):
            await ctx.send(file=File(img_path))
        else:
            await msg.reference.resolved.reply(file=File(img_path))

    @commands.command()
    async def notthemxm(self, ctx):
        """ Holy shit nice score-- """
        await self.send_image(ctx, 'ext/imgs/notthemxm.png')
    
    @commands.command()
    async def ligma(self, ctx):
        """ Who the hell is Steve Jobs?! """
        await self.send_image(ctx, 'ext/imgs/ligma.jpg')
    
    @commands.command()
    async def imperial(self, ctx):
        """ im the worst new imperial """
        await self.send_image(ctx, 'ext/imgs/imperial.png')
    
    @commands.command()
    async def gaming(self, ctx):
        """ now that's what I call gaming """
        await self.send_image(ctx, 'ext/imgs/gaming.jpg')
    
    @commands.command()
    async def jasper(self, ctx):
        """ im allergic to jasper's shit """
        await self.send_image(ctx, 'ext/imgs/jasper.png')
    
    @commands.command(aliases=['18', '🔞'])
    async def horney(self, ctx):
        """ acab """
        await self.send_image(ctx, 'ext/imgs/horney.jpg')
    
    @commands.command()
    async def hydrate(self, ctx):
        """ friendly reminder to drink a cup of water """
        if self._hydrate:
            await self.send_image(ctx, 'ext/imgs/hydrate2.jpg')
        else:
            await self.send_image(ctx, 'ext/imgs/hydrate1.jpg')
        self._hydrate = 1 - self._hydrate
    
    @commands.command()
    async def goodbye(self, ctx):
        """ you're so sucks. goodbye. """
        await self.send_image(ctx, 'ext/imgs/goodbye.png')
    
    @commands.command()
    async def denzel(self, ctx):
        """ has anyone ever beat you up before """
        if self._denzel:
            await self.send_image(ctx, 'ext/imgs/denzel2.png')
        else:
            await self.send_image(ctx, 'ext/imgs/denzel1.png')
        self._denzel = 1 - self._denzel
    
    @commands.command()
    async def jbl(self, ctx):
        """ LOVE """
        await self.send_image(ctx, 'ext/imgs/jbl.png')
    
    @commands.command()
    async def candii(self, ctx):
        """ sapphirehime """
        await self.send_image(ctx, 'ext/imgs/gnome.png')
    
    @commands.command()
    async def israel(self, ctx):
        """ whats wrong with u israel """
        await self.send_image(ctx, 'ext/imgs/israel.png')
    
    @commands.command()
    async def plywood(self, ctx):
        """ this is an absolute win """
        await self.send_image(ctx, 'ext/imgs/plywood.jpg')
    
    @commands.command()
    async def emma(self, ctx):
        """ altona good chart ok """
        await self.send_image(ctx, 'ext/imgs/emma.png')
    
    @commands.command()
    async def sexualtension(self, ctx):
        """ Sexual Tension On The PK Server . """
        await self.send_image(ctx, 'ext/imgs/pktension.png')
    
    @commands.command()
    async def piu(self, ctx):
        """ why the fuck am i playing this game """
        await self.send_image(ctx, 'ext/imgs/piu.png')
    
    @commands.command()
    async def er(self, ctx):
        """ presenting to the emergency room """
        await self.send_image(ctx, 'ext/imgs/lormaigai.jpg')
    
    @commands.command()
    async def knobs(self, ctx):
        """ what's wiggling """
        await self.send_image(ctx, 'ext/imgs/knobs.jpg')
    
    @commands.command()
    async def foot(self, ctx):
        """ Theorem: I have a big mouth | Proof: """
        await self.send_image(ctx, 'ext/imgs/foot.png')
    
    @commands.command()
    async def rave(self, ctx):
        """ why does he look like rave """
        await self.send_image(ctx, 'ext/imgs/rave.jpg')
    
    @commands.command()
    async def marsh(self, ctx):
        """ 🇧🇷 """
        await self.send_image(ctx, 'ext/imgs/marsh.png')


class BreadGacha(commands.Cog, name='Bread Facha'):
    def __init__(self):
        self._bread_counter = [0, 0, 0, 0]
        self._last_refresh = None

    @commands.command()
    async def bread(self, ctx):
        """ bread craftsingle banana craftsingle """
        current_time = time.strftime('%Y%m%d')
        if self._last_refresh is None or current_time > self._last_refresh:
            self._last_refresh = current_time
            self._bread_counter = [0, 0, 0, 0]
    
        self._bread_counter[0] += 1
        if random.random() < 0.01:
            self._bread_counter[2] += 1
            await ctx.reply(file=File('ext/imgs/bread3.png'))
            with open('ext/ssr_pulls.txt', 'a') as f:
                f.write(f'{ctx.author.id}\n')
        elif random.random() < 0.11:
            self._bread_counter[1] += 1
            await ctx.reply(file=File('ext/imgs/bread2.png'))
        elif random.random() < 0.21:
            self._bread_counter[3] += 1
            await ctx.reply(file=File('ext/imgs/bread4.png'))
        else:
            await ctx.reply('bread craftsingle banana craftsingle', file=File('ext/imgs/bread.png'))
    
    @commands.command()
    async def breadstats(self, ctx):
        """ did you just pull 2 jaspers in a row?? """
        with open('ext/ssr_pulls.txt', 'r') as f:
            member_list = list(f)
        texts = [
            f'-bread has been used {self._bread_counter[0]} times today'
        ]
        if self._bread_counter[0] > 0:
            texts.append(f'out of those, {self._bread_counter[1]} '
                         f'({self._bread_counter[1]/self._bread_counter[0]*100:.2f}%) of them were jasper')
            texts.append(f'out of those, {self._bread_counter[3]} '
                         f'({self._bread_counter[3]/self._bread_counter[0]*100:.2f}%) of them were gartic jasper')
            texts.append(f'and {self._bread_counter[2]} '
                         f'({self._bread_counter[2]/self._bread_counter[0]*100:.2f}%) of them were SSR jasper')
        await ctx.reply('\n'.join(texts))
    
        if member_list:
            texts = ['Top pullers:']
            place = 1
            for whoid, count in collections.Counter(member_list).most_common():
                user = ctx.guild.get_member(int(whoid.strip()))
                if user is not None:
                    if count > 1:
                        texts.append(f'{place}. `{escape_markdown(user.nick or user.name)}` ({count} times)')
                    else:
                        texts.append(f'{place}. `{escape_markdown(user.nick or user.name)}` ({count} time)')
                    place += 1
            await ctx.send('\n'.join(texts))


@commands.command()
async def acs(ctx):
    """ tgbtg tbiytb """
    await ctx.reply('tgbtg tbiytb')


@commands.command()
async def josh(ctx):
    """ tastes quite bad """
    await ctx.reply('https://cdn.discordapp.com/attachments/648560458420322306/820551483019100160/evans.mp4')


@commands.command(aliases=['egg'])
async def taylorswift(ctx):
    """ someday, i'll be living in a big old city """
    await ctx.reply('https://va.media.tumblr.com/tumblr_mhd8usvaeJ1qmjzvz.mp4')


def setup(bot):
    bot.add_cog(Images())
    bot.add_cog(BreadGacha())
    bot.add_command(acs)
    bot.add_command(josh)
    bot.add_command(taylorswift)
