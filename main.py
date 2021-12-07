# bot.py
import discord
import os
import traceback

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ROLE_ID = int(os.getenv('BOT_HANDLER_ID'))  # should be 839485641339306044

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='-', intents=intents)
extensions = [
    'ext.audioplayer',
    'ext.cv',
    'ext.miscellaneous',
    # 'ext.mangadex',
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
    else:
        for arg in args:
            # silently ignore extensions not present
            if arg in bot.extensions:
                bot.reload_extension(arg)
            elif f'ext.{arg}' in bot.extensions:
                bot.reload_extension(f'ext.{arg}')

    print('Reloaded module(s).')
    await ctx.message.add_reaction('🆗')


@bot.listen('on_command_error')
async def error_handler(ctx, err):
    if not isinstance(err, commands.CommandNotFound):
        tb = ''.join(traceback.format_exception(type(err), err, err.__traceback__, limit=2))
        await ctx.message.add_reaction('⛔')
        await ctx.reply(f'{type(err).__name__}: {err}\nTraceback: ```{tb}```', delete_after=10)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


for _ext in extensions:
    bot.load_extension(_ext)
bot.run(TOKEN)
