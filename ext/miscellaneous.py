from discord import File
from discord.ext import commands


@commands.command()
async def notthemxm(ctx):
    await ctx.send(file=File('ext/notthemxm.png'))


@commands.command()
async def sweetland(ctx):
    await ctx.send('https://www.youtube.com/watch?v=ws4vY996y8M')


def setup(bot):
    bot.add_command(notthemxm)
    bot.add_command(sweetland)
