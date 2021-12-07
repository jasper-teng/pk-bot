import itertools
import math
from discord import Embed
from discord.ext import commands

ALLOWED_TEXT = {
    'd': (0, 0),
    'c': (0, 1),
    'b': (0, 2),
    'a': (0, 3),
    'a+': (0, 4),
    'aa': (0, 5),
    'aa+': (0, 6),
    'aaa': (0, 7),
    'aaa+': (0, 8),
    's': (0, 9),
    'played': (1, 0),
    'clear': (1, 1),
    'exc': (1, 2),
    'excessive': (1, 2),
    'uc': (1, 3),
    'p': (1, 4),
    'perfect': (1, 4),
    'puc': (1, 4)
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
    (1.05, 9_900_000, 10_000_001)
]
GRADE_NAMES = ['D', 'C', 'B', 'A', 'A+', 'AA', 'AA+', 'AAA', 'AAA+', 'S']


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

    # separate args
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
        volforce = int(kwargs['volforce'] * 10) / 10
        lv_bound = math.ceil(volforce / 2 / 1.1 / 1.05)
        output = []
        for lv, cm_info in itertools.product(range(lv_bound, min(21, lv_bound + 3)), CLEAR_MARK):
            cm_mult, cm_name = cm_info
            if cm_name == 'PUC':
                if volforce == score_to_vf(10_000_000, cm_mult, lv):
                    output.append(f'- {cm_name} on a Lv{lv} chart.')
            else:
                score = vf_to_score(volforce, cm_mult, lv)
                if score:
                    output.append(f'- {score:,} {cm_name} on a Lv{lv} chart.')

        embed_title = f'{volforce} VF can be obtained by:'
        if not output:
            output.append('Cannot be achieved!')
        embed_desc = '\n'.join(output)
    else:
        if kwargs['score']:
            pass
        elif kwargs['clear_mark'] == 4:  # PUC implies 10 000 000 score
            kwargs['score'] = 1
        elif kwargs['level'] and kwargs['grade'] is None:
            kwargs['score'], kwargs['level'] = kwargs['level'], kwargs['score']
        elif kwargs['grade'] is not None:
            kwargs['mode'] = 'GRADE'
            kwargs['score'] = GRADES[kwargs['grade']][1]

        if kwargs['score']:
            # normalize score
            score = kwargs['score']
            while score <= 1_000_000:
                score *= 10
            # all the different modes
            output = []
            if kwargs['level'] and kwargs['clear_mark'] is not None and kwargs['mode'] == 'SCORE':
                lv = kwargs['level']
                cm_mult, cm_name = CLEAR_MARK[kwargs['clear_mark']]
                if (kwargs['clear_mark'] != 4) ^ (score == 10_000_000):
                    volforce = score_to_vf(score, cm_mult, lv)
                    output.append(f'- {volforce} VF with {cm_name} on a Lv{lv} chart.')
                else:
                    output.append('Cannot be achieved!')
                embed_title = f'Calculation for SCORE={score:,}, LV={lv}, CLRMARK={cm_name}:'
                embed_desc = '\n'.join(output)
            elif kwargs['level'] and kwargs['clear_mark'] is not None and kwargs['mode'] == 'GRADE':
                lv = kwargs['level']
                cm_mult, cm_name = CLEAR_MARK[kwargs['clear_mark']]
                grade_mult, sc_low, sc_high = GRADES[kwargs['grade']]
                grade_name = GRADE_NAMES[kwargs['grade']]
                if kwargs['clear_mark'] == 4 and kwargs['grade'] != 9:
                    output.append('Cannot be achieved!')
                elif kwargs['clear_mark'] == 4 and kwargs['grade'] == 9:
                    volforce = score_to_vf(10_000_000, cm_mult, lv)
                    output.append(f'- {volforce} VF with {cm_name} on a Lv{lv} chart.')
                else:
                    volforce = score_to_vf(sc_low, cm_mult, lv)
                    sc_est = sc_low
                    while True:
                        output.append(f'- {volforce} VF with {sc_est:,} {cm_name} on a Lv{lv} chart.')
                        volforce = int(10 * volforce + 1) / 10
                        sc_est = vf_to_score(volforce, cm_mult, lv)
                        if sc_est is None or sc_est >= sc_high:
                            break
                embed_title = f'Calculation for GRADE={grade_name}, LV={lv}, CLRMARK={cm_name}:'
                embed_desc = '\n'.join(output)
            elif kwargs['clear_mark'] is not None:
                cm_mult, cm_name = CLEAR_MARK[kwargs['clear_mark']]
                if (kwargs['clear_mark'] != 4) ^ (score == 10_000_000):
                    for lv in range(17, 21):
                        volforce = score_to_vf(score, cm_mult, lv)
                        output.append(f'- {volforce} VF with {cm_name} on a Lv{lv} chart.')
                else:
                    output.append('Cannot be achieved!')
                embed_title = f'Calculation for SCORE={score:,}, CLRMARK={cm_name}:'
                embed_desc = '\n'.join(output)
            elif kwargs['level'] is not None:
                lv = kwargs['level']
                for cm_mult, cm_name in CLEAR_MARK:
                    if (cm_name == 'PUC') ^ (score == 10_000_000):
                        continue
                    volforce = score_to_vf(score, cm_mult, lv)
                    output.append(f'- {volforce} VF with {cm_name} on a Lv{lv} chart.')
                embed_title = f'Calculation for SCORE={score:,}, LV={lv}:'
                embed_desc = '\n'.join(output)
            else:
                for lv in range(17, 21):
                    for cm_mult, cm_name in CLEAR_MARK:
                        if (cm_name == 'PUC') ^ (score == 10_000_000):
                            continue
                        volforce = score_to_vf(score, cm_mult, lv)
                        output.append(f'- {volforce} VF with {cm_name} on a Lv{lv} chart.')
                embed_title = f'Calculation for SCORE={score:,}:'
                embed_desc = '\n'.join(output)
        else:
            # nothing can be interpreted as score
            embed_title = 'Error!'
            embed_desc = 'Score/grade not found.'

    embed = Embed(title=embed_title, description=embed_desc)
    await ctx.send(embed=embed)


def vf_to_score(volforce, clear_multiplier, chart_level):
    """ Return score yielding a given volforce at a certain level and clear mark. """
    for grade_info in GRADES:
        grade_mult, sc_low, sc_high = grade_info
        low_bound = math.ceil(volforce / 2 / chart_level / grade_mult / clear_multiplier * 10_000_000)
        high_bound = math.floor((volforce + 0.1) / 2 / chart_level / grade_mult / clear_multiplier * 10_000_000)
        if sc_low <= low_bound < sc_high:
            return low_bound
        elif sc_low <= high_bound < sc_high:
            return sc_low


def score_to_vf(score, clear_multiplier, chart_level):
    """ Compute volforce given score, clear multiplier and chart level. """
    for grade_info in GRADES:
        grade_mult, sc_low, sc_high = grade_info
        if sc_low <= score < sc_high:
            return int(2 * chart_level * clear_multiplier * grade_mult * score / 1_000_000) / 10


def setup(bot):
    bot.add_command(vf)
