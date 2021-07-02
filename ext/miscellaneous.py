import asyncio
import random
from discord import File, FFmpegOpusAudio
from discord.ext import commands

VOICE_CLIENT = None


@commands.command()
async def notthemxm(ctx):
    """ Holy shit nice score-- """
    await ctx.send(file=File('ext/notthemxm.png'))


@commands.command()
async def bread(ctx):
    """ bread craftsingle banana craftsingle """
    if random.random() < 0.1:
        await ctx.send(file=File('ext/bread2.png'))
    else:
        await ctx.send(file=File('ext/bread.png'))
        await ctx.send('bread craftsingle banana craftsingle')


@commands.group(invoke_without_command=True, aliases=['sweetsland'])
async def sweetland(ctx):
    """ ♫♫♩～ """
    if ctx.invoked_subcommand is None:
        await ctx.send('https://www.youtube.com/watch?v=ws4vY996y8M')


@sweetland.command()
async def play(ctx):
    global VOICE_CLIENT
    if VOICE_CLIENT is not None:
        return

    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    def after(err):
        if err:
            raise err
        def clear():
            stop_event.set()
        loop.call_soon_threadsafe(clear)

    channel = ctx.guild.voice_channels[0]
    audio = FFmpegOpusAudio('ext/sweetland.mp3')
    await ctx.message.add_reaction('🆗')

    client = await channel.connect()
    VOICE_CLIENT = client
    client.play(audio, after=after)

    await stop_event.wait()
    await client.disconnect()
    VOICE_CLIENT = None


@sweetland.command()
async def stop(ctx):
    global VOICE_CLIENT
    if VOICE_CLIENT is None:
        return

    client = VOICE_CLIENT
    VOICE_CLIENT = None

    client.stop()
    await client.disconnect()
    await ctx.message.add_reaction('🆗')


def setup(bot):
    bot.add_command(notthemxm)
    bot.add_command(bread)
    bot.add_command(sweetland)
