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


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

bot.run(TOKEN)