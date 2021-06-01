# bot.py
import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# client = discord.Client()
bot = commands.Bot(command_prefix='*')


@bot.command()
async def jcjc(ctx):
    await ctx.send('lmao')


@bot.command(hidden=True)
async def reload(ctx, *args):
    if not args:
        for ext in list(bot.extensions):
            bot.reload_extension(ext)
    for arg in args:
        bot.reload_extension(arg)

    await ctx.message.add_reaction('🆗')


@bot.listen('on_command_error')
async def error_handler(ctx, err):
    await ctx.message.add_reaction('⛔')
    await ctx.send(f'{type(err).__name__}: {err}', delete_after=10)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


bot.load_extension('ext.mangadex')
bot.load_extension('ext.sdvxin')
bot.run(TOKEN)
