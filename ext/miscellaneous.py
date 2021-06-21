from discord import File
from discord.ext import commands


@commands.command()
async def notthemxm(ctx):
    await ctx.send(file=File('ext/notthemxm.png'))


def setup(bot):
    bot.add_command(notthemxm)
