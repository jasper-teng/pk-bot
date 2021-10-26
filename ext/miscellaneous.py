import collections
import random
import time
from discord import Embed, File, DeletedReferencedMessage
from discord.ext import commands
from discord.utils import escape_markdown

BREAD_COUNTER = [0, 0, 0, 0]
LAST_REFRESH = None
ALLOWED_TEXT = {
    'd'        : (0, 0),
    'c'        : (0, 1),
    'b'        : (0, 2),
    'a'        : (0, 3),
    'a+'       : (0, 4),
    'aa'       : (0, 5),
    'aa+'      : (0, 6),
    'aaa'      : (0, 7),
    'aaa+'     : (0, 8),
    's'        : (0, 9),
    'played'   : (1, 0),
    'clear'    : (1, 1),
    'exc'      : (1, 2),
    'excessive': (1, 2),
    'uc'       : (1, 3),
    'p'        : (1, 4),
    'perfect'  : (1, 4),
    'puc'      : (1, 4)
}
CLEAR_MARK = [
    (0.5, 'PLAYED'),
    (1.0, 'CLEAR'),
    (1.02, 'EXCESSIVE'),
    (1.05, 'UC'),
    (1.1, 'PUC')
]
GRADES = [
    (0.79, 0, 7_000_000),
    (0.82, 7_000_000, 8_000_000),
    (0.85, 8_000_000, 8_700_000),
    (0.88, 8_700_000, 9_000_000),
    (0.91, 9_000_000, 9_300_000),
    (0.94, 9_300_000, 9_500_000),
    (0.97, 9_500_000, 9_700_000),
    (1, 9_700_000, 9_800_000),
    (1.02, 9_800_000, 9_900_000),
    (1.05, 9_900_000, 10_000_000)
]
GRADE_NAMES = ['D', 'C', 'B', 'A', 'A+', 'AA', 'AA+', 'AAA', 'AAA+', 'S']


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
async def denzel(ctx, *, state=[]):
    """ has anyone ever beat you up before """
    if state:
        state.pop()
        await send_image(ctx, 'ext/denzel2.png')
    else:
        state.append(1)
        await send_image(ctx, 'ext/denzel1.png')


@commands.command()
async def jbl(ctx):
    """ LOVE """
    await send_image(ctx, 'ext/jbl.png')


@commands.command()
async def candii(ctx):
    """ sapphirehime """
    await send_image(ctx, 'ext/gnome.png')


@commands.command()
async def israel(ctx):
    """ whats wrong with u israel """
    await send_image(ctx, 'ext/israel.png')


@commands.command()
async def plywood(ctx):
    """ this is an absolute win """
    await send_image(ctx, 'ext/plywood.jpg')


@commands.command()
async def emma(ctx):
    """ altona good chart ok """
    await send_image(ctx, 'ext/emma.png')


@commands.command()
async def sexualtension(ctx):
    """ Sexual Tension On The PK Server . """
    await send_image(ctx, 'ext/pktension.png')


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
        BREAD_COUNTER = [0, 0, 0, 0]

    BREAD_COUNTER[0] += 1
    if random.random() < 0.01:
        BREAD_COUNTER[2] += 1
        await ctx.reply(file=File('ext/bread3.png'))
        with open('ext/ssr_pulls.txt', 'a') as f:
            f.write(f'{ctx.author.id}\n')
    elif random.random() < 0.11:
        BREAD_COUNTER[1] += 1
        await ctx.reply(file=File('ext/bread2.png'))
    elif random.random() < 0.21:
        BREAD_COUNTER[3] += 1
        await ctx.reply(file=File('ext/bread4.png'))
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
        texts.append(f'out of those, {BREAD_COUNTER[3]} ({BREAD_COUNTER[3]/BREAD_COUNTER[0]*100:.2f}%) of them were gartic jasper')
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


@commands.command()
async def vf(ctx, *args):
    """
    Volforce calculator
    
    command has behaves differently depending on input. unrecognized input
      will be discarded.
    after discards, if a numeric value with decimal point is found, command
    executes an inverse lookup. otherwise it computes volforce.
    inverse lookup -> calculates score that achieves at least that volforce.
      decimal point required. input is rounded down to nearest tenth.
    volforce computer -> calculates volforce yield given certain parameters.
      score is required. can be provided as exact value or grade.
      score -> gives volforce values for Lv17-20 and different clear marks.
      score + level -> calculates volforce for different clear marks.
      score + clear mark -> calculates volforce for Lv17-20.
      score + level + clear mark -> calculates exact volforce.
      score overrides grade. grade behaves as score except when level and clear
        mark are given. breakpoints within the grade will be calculated.
    """
    import math

    kwargs = {
        'numeric': [],
        'alpha': [],
        'volforce': None,
        'score': None,
        'level': None,
        'grade': None,
        'clear_mark': None,
        'mode': 'SCORE'
    }
    for arg in args:
        try:
            val_float = float(arg)
            val_int = int(val_float)
            if '.' in arg:
                kwargs['numeric'].append(val_float)
            else:
                kwargs['numeric'].append(val_int)
        except ValueError:
            kwargs['alpha'].append(arg)

    # check numeric entries
    for val in kwargs['numeric']:
        if isinstance(val, float):
            kwargs['volforce'] = val
            break
        else:
            val = int(val)
            if 1 <= val <= 20:
                if kwargs['level']:
                    kwargs['score'] = kwargs['level']
                kwargs['level'] = val
            elif not kwargs['score']:
                kwargs['score'] = val
            # break once both are filled
            if kwargs['level'] and kwargs['score']:
                break

    # check non-number entries
    for val in kwargs['alpha']:
        if val.lower() not in ALLOWED_TEXT:
            continue
        typ, idx = ALLOWED_TEXT[val.lower()]
        if typ == 0 and not kwargs['grade']:
            kwargs['grade'] = idx
        elif typ == 1 and not kwargs['clear_mark']:
            kwargs['clear_mark'] = idx
        # break once both are filled
        if kwargs['grade'] and kwargs['clear_mark']:
            break
    
    # finally calculate
    if kwargs['volforce']:
        # figure out the lower bound on level
        # multiplying VF by 10 to not deal with floats
        vf_ref = int(kwargs['volforce'] * 10)
        lv_bound = math.ceil(vf_ref / 2 / 1.1 / 1.05 / 10)
        output = []
        for lv in range(lv_bound, min(21, lv_bound + 3)):
            for cm_info in CLEAR_MARK:
                cm_mult, cm_name = cm_info
                if cm_name != 'PUC':
                    for grade_info in GRADES:
                        grade_mult, sc_lo, sc_hi = grade_info
                        sc_est = math.ceil(vf_ref / 2 / lv / cm_mult / grade_mult * 1_000_000)
                        if sc_lo <= sc_est < sc_hi:
                            output.append(f'- {sc_est:,} {cm_name} on a Lv{lv} chart.')
                else:
                    if vf_ref == int(lv * 2 * 1.1 * 1.05 * 10):
                        output.append(f'- {cm_name} on a Lv{lv} chart.')
        
        embed_title = f'{vf_ref / 10} VF can be obtained by:'
        if not output:
            output.append('Cannot be achieved!')
        embed_desc = '\n'.join(output)
    else:
        if kwargs['score']:
            pass
        elif kwargs['level'] and kwargs['grade'] is None:
            kwargs['score'], kwargs['level'] = kwargs['level'], kwargs['score']
        elif kwargs['grade'] is not None:
            kwargs['mode'] = 'GRADE'
            kwargs['score'] = GRADES[kwargs['grade']][1]
        else:
            # nothing can be interpreted as score
            embed_title = 'Error!'
            embed_desc = 'Score/grade not found.'

        if kwargs['score']:
            # normalize score
            while True:
                if 1_000_000 < kwargs['score'] <= 10_000_000:
                    break
                kwargs['score'] *= 10
            score = kwargs['score']
            # all the different modes
            output = []
            if kwargs['level'] and kwargs['clear_mark'] is not None and kwargs['mode'] == 'SCORE':
                cm_info = CLEAR_MARK[kwargs['clear_mark']]
                cm_mult, cm_name = cm_info
                if kwargs['clear_mark'] == 4 and score == 10_000_000:
                    vf = int(2 * lv * cm_mult * grade_mult * 10) / 10
                    output.append(f'- {vf} VF with PUC on a Lv{lv} chart.')
                elif kwargs['clear_mark'] != 4 and score != 10_000_000:
                    lv = kwargs['level']
                    for grade_info in GRADES:
                        grade_mult, sc_lo, sc_hi = grade_info
                        if sc_lo <= score < sc_hi:
                            vf = int(2 * lv * cm_mult * grade_mult * score / 1_000_000) / 10
                            output.append(f'- {vf} VF with {cm_name} on a Lv{lv} chart.')
                else:
                    output.append('Cannot be achieved!')
                embed_title = f'Calculation for SCORE={score:,}, LV={lv}, CLRMARK={cm_name}:'
                embed_desc = '\n'.join(output)
            elif kwargs['level'] and kwargs['clear_mark'] is not None and kwargs['mode'] == 'GRADE':
                lv = kwargs['level']
                cm_info = CLEAR_MARK[kwargs['clear_mark']]
                cm_mult, cm_name = cm_info
                if kwargs['clear_mark'] == 4 and kwargs['grade'] != 9:
                    output.append('Cannot be achieved!')
                elif kwargs['clear_mark'] == 4 and kwargs['grade'] == 9:
                    vf = int(2 * lv * cm_mult * grade_mult * 10) / 10
                    output.append(f'- {vf} VF with PUC on a Lv{lv} chart.')
                else:
                    grade_info = GRADES[kwargs['grade']]
                    grade_mult, sc_lo, sc_hi = grade_info
                    grade_name = GRADE_NAMES[kwargs['grade']]
                    base_vf = int(2 * lv * cm_mult * grade_mult * sc_lo / 1_000_000)
                    output.append(f'- {base_vf / 10} VF with {sc_lo:,} {cm_name} on a Lv{lv} chart.')
                    while True:
                        base_vf += 1
                        sc_est = math.ceil(base_vf / 2 / lv / cm_mult / grade_mult * 1_000_000)
                        if sc_est >= sc_hi:
                            break
                        output.append(f'- {base_vf / 10} VF with {sc_est:,} {cm_name} on a Lv{lv} chart.')
                embed_title = f'Calculation for GRADE={grade_name}, LV={lv}, CLRMARK={cm_name}:'
                embed_desc = '\n'.join(output)
            elif kwargs['clear_mark'] is not None:
                cm_info = CLEAR_MARK[kwargs['clear_mark']]
                cm_mult, cm_name = cm_info
                if kwargs['clear_mark'] == 4 and score == 10_000_000:
                    for lv in range(17, 21):
                        vf = int(2 * lv * cm_mult * grade_mult * 10) / 10
                        output.append(f'- {vf} VF with PUC on a Lv{lv} chart.')
                elif kwargs['clear_mark'] != 4 and score != 10_000_000:
                    for lv in range(17, 21):
                        for grade_info in GRADES:
                            grade_mult, sc_lo, sc_hi = grade_info
                            if sc_lo <= score < sc_hi:
                                vf = int(2 * lv * cm_mult * grade_mult * score / 1_000_000) / 10
                                output.append(f'- {vf} VF with {cm_name} on a Lv{lv} chart.')
                else:
                    output.append('Cannot be achieved!')
                embed_title = f'Calculation for SCORE={score:,}, CLRMARK={cm_name}:'
                embed_desc = '\n'.join(output)
            elif kwargs['level'] is not None:
                lv = kwargs['level']
                if score == 10_000_000:
                    vf = int(2 * lv * cm_mult * grade_mult * 10) / 10
                    output.append(f'- {vf} VF with PUC on a Lv{lv} chart.')
                else:
                    for cm_info in CLEAR_MARK:
                        cm_mult, cm_name = cm_info
                        if cm_name == 'PUC':
                            continue
                        for grade_info in GRADES:
                            grade_mult, sc_lo, sc_hi = grade_info
                            if sc_lo <= score < sc_hi:
                                vf = int(2 * lv * cm_mult * grade_mult * score / 1_000_000) / 10
                                output.append(f'- {vf} VF with {cm_name} on a Lv{lv} chart.')
                embed_title = f'Calculation for SCORE={score:,}, LV={lv}:'
                embed_desc = '\n'.join(output)
            else:
                for lv in range(17, 21):
                    if score == 10_000_000:
                        vf = int(2 * lv * cm_mult * grade_mult * 10) / 10
                        output.append(f'- {vf} VF with PUC on a Lv{lv} chart.')
                    else:
                        for cm_info in CLEAR_MARK:
                            cm_mult, cm_name = cm_info
                            if cm_name == 'PUC':
                                continue
                            for grade_info in GRADES:
                                grade_mult, sc_lo, sc_hi = grade_info
                                if sc_lo <= score < sc_hi:
                                    vf = int(2 * lv * cm_mult * grade_mult * score / 1_000_000) / 10
                                    output.append(f'- {vf} VF with {cm_name} on a Lv{lv} chart.')
                embed_title = f'Calculation for SCORE={score:,}:'
                embed_desc = '\n'.join(output)

    embed = Embed(title=embed_title, description=embed_desc)
    await ctx.send(embed=embed)


def setup(bot):
    bot.add_command(notthemxm)
    bot.add_command(ligma)
    bot.add_command(imperial)
    bot.add_command(gaming)
    bot.add_command(jasper)
    bot.add_command(horney)
    bot.add_command(hydrate)
    bot.add_command(goodbye)
    bot.add_command(denzel)
    bot.add_command(jbl)
    bot.add_command(candii)
    bot.add_command(israel)
    bot.add_command(plywood)
    bot.add_command(emma)
    bot.add_command(sexualtension)
    bot.add_command(acs)
    bot.add_command(bread)
    bot.add_command(breadstats)
    bot.add_command(vf)
