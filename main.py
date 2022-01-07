# bot.py
import discord
import json
import os
import time
import traceback

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))  # should be 839485641339306044
TRACEBACK_LOG_PATH = 'errlog.json'

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='-', intents=intents)
extensions = [
    'ext.audioplayer',
    'ext.cv',
    'ext.miscellaneous',
    'ext.scheduler',
    'ext.sdvxdb',
    'ext.sdvxin',
    'ext.viewer',
    'ext.volforce'
]


@bot.command(hidden=True)
@commands.has_role(ROLE_ID)
async def reload(ctx, *args):
    if not args:
        for ext in list(bot.extensions):
            bot.reload_extension(ext)
        bot.log('Bot', 'Reloaded all modules.')
    else:
        reloaded = []
        for arg in args:
            # silently ignore extensions not present
            if arg in bot.extensions:
                bot.reload_extension(arg)
                reloaded.append(arg)
            elif f'ext.{arg}' in bot.extensions:
                bot.reload_extension(f'ext.{arg}')
                reloaded.append(f'ext.{arg}')
        bot.log('Bot', f'Reloaded modules: {", ".join(reloaded)}.')

    await ctx.message.add_reaction('🆗')


@bot.listen('on_command_error')
async def error_handler(ctx, err):
    if not isinstance(err, commands.CommandNotFound):
        tb = ''.join(traceback.format_exception(type(err), err, err.__traceback__, limit=5))
        await ctx.message.add_reaction('⛔')
        try:
            with open(TRACEBACK_LOG_PATH, 'r') as f:
                traceback_log = json.load(f)
        except IOError:
            traceback_log = []
        data = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'author': f'{ctx.author.name}#{ctx.author.discriminator}',
            'msg_link': ctx.message.jump_url,
            'traceback': f'{type(err).__name__}: {err}\n{tb}'
        }
        traceback_log.append(data)
        with open(TRACEBACK_LOG_PATH, 'w') as f:
            json.dump(traceback_log, f)
        bot.log('Bot', f'Logged {type(err).__name__} to traceback log.')


@bot.event
async def on_ready():
    bot.log('Bot', f'{bot.user} has connected to Discord!')


def log(header, content):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    print(f'[{time_str}] <{header}> {content}')


for _ext in extensions:
    bot.load_extension(_ext)
bot.log = log
bot.run(TOKEN)
