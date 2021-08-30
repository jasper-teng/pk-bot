import collections
import random
import time
from discord import File, DeletedReferencedMessage
from discord.ext import commands
from discord.utils import escape_markdown

BREAD_COUNTER = [0, 0, 0]
LAST_REFRESH = None


async def send_image(ctx, img_path):
    msg = ctx.message
    if msg.reference is None or isinstance(msg.reference.resolved, DeletedReferencedMessage):
        await ctx.send(file=File(img_path))
    else:
        await msg.reference.resolved.reply(file=File(img_path))


@commands.command()
async def notthemxm(ctx):
    """ Holy shit nice score-- """
    await send_image(ctx, 'ext/notthemxm.png')


@commands.command()
async def ligma(ctx):
    """ Who the hell is Steve Jobs?! """
    await send_image(ctx, 'ext/ligma.jpg')


@commands.command()
async def imperial(ctx):
    """ im the worst new imperial """
    await send_image(ctx, 'ext/imperial.png')


@commands.command()
async def gaming(ctx):
    """ now that's what I call gaming """
    await send_image(ctx, 'ext/gaming.jpg')


@commands.command()
async def jasper(ctx):
    """ im allergic to jasper's shit """
    await send_image(ctx, 'ext/jasper.png')


@commands.command(aliases=['18', '🔞'])
async def horney(ctx):
    """ acab """
    await send_image(ctx, 'ext/horney.jpg')


@commands.command()
async def hydrate(ctx):
    """ friendly reminder to drink a cup of water """
    await send_image(ctx, 'ext/hydrate.jpg')


@commands.command()
async def goodbye(ctx):
    """ you're so sucks. goodbye. """
    await send_image(ctx, 'ext/goodbye.png')


@commands.command()
async def acs(ctx):
    """ tgbtg tbiytb """
    await ctx.reply('tgbtg tbiytb')


@commands.command()
async def bread(ctx):
    """ bread craftsingle banana craftsingle """
    global LAST_REFRESH, BREAD_COUNTER
    current_time = time.strftime('%Y%m%d')
    if LAST_REFRESH is None or current_time > LAST_REFRESH:
        LAST_REFRESH = current_time
        BREAD_COUNTER = [0, 0, 0]

    BREAD_COUNTER[0] += 1
    if random.random() < 0.01:
        BREAD_COUNTER[2] += 1
        await ctx.reply(file=File('ext/bread3.png'))
        with open('ext/ssr_pulls.txt', 'a') as f:
            f.write(f'{ctx.author.id}\n')
    elif random.random() < 0.1:
        BREAD_COUNTER[1] += 1
        await ctx.reply(file=File('ext/bread2.png'))
    else:
        await ctx.reply('bread craftsingle banana craftsingle', file=File('ext/bread.png'))


@commands.command()
async def breadstats(ctx):
    """ did you just pull 2 jaspers in a row?? """
    global BREAD_COUNTER
    with open('ext/ssr_pulls.txt', 'r') as f:
        member_list = list(f)
    texts = [
        f'-bread has been used {BREAD_COUNTER[0]} times today'
    ]
    if BREAD_COUNTER[0] > 0:
        texts.append(f'out of those, {BREAD_COUNTER[1]} ({BREAD_COUNTER[1]/BREAD_COUNTER[0]*100:.2f}%) of them were jasper')
        texts.append(f'and {BREAD_COUNTER[2]} ({BREAD_COUNTER[2]/BREAD_COUNTER[0]*100:.2f}%) of them were SSR jasper')
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


def setup(bot):
    bot.add_command(notthemxm)
    bot.add_command(ligma)
    bot.add_command(imperial)
    bot.add_command(gaming)
    bot.add_command(jasper)
    bot.add_command(horney)
    bot.add_command(hydrate)
    bot.add_command(goodbye)
    bot.add_command(acs)
    bot.add_command(bread)
    bot.add_command(breadstats)
