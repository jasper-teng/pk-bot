import asyncio
import random
from discord import File, FFmpegOpusAudio, DeletedReferencedMessage
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


@commands.command()
async def ligma(ctx):
    """ Who the hell is Steve Jobs?! """
    msg = ctx.message
    if msg.reference is None or isinstance(msg.reference.resolved, DeletedReferencedMessage):
        await ctx.send(file=File('ext/ligma.jpg'))
    else:
        await msg.reference.resolved.reply(file=File('ext/ligma.jpg'))


@commands.group(invoke_without_command=True, aliases=['sweetsland'])
async def sweetland(ctx):
    """ ♫♫♩～ """
    if ctx.invoked_subcommand is None:
        await ctx.send('https://www.youtube.com/watch?v=ws4vY996y8M')


@sweetland.command()
async def play(ctx, channel_num=None):
    """
    Play music in a voice channel.
    
    If channel number isn't given, defaults to the user's voice channel.
    If user isn't in a voice channel, defaults to the first voice channel that is occupied.
    """
    global VOICE_CLIENT
    if VOICE_CLIENT is not None:
        ctx.reply('Stop current playback first before starting it again!', delete_after=10)
        return

    # Select channel
    target_channel = None
    if channel_num is None:
        author = ctx.author
        if author.voice and author.voice.channel is not None:
            target_channel = author.voice.channel
        else:
            for channel in ctx.guild.voice_channels:
                if channel.members:
                    target_channel = channel
                    break
            await ctx.reply('No voice channel available to bind to!')
    else:
        target_channel = ctx.guild.voice_channels[int(channel_num) - 1]
    audio = FFmpegOpusAudio('ext/sweetland.mp3')
    await ctx.message.add_reaction('🆗')

    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    def after(err):
        if err:
            raise err
        def clear():
            stop_event.set()
        loop.call_soon_threadsafe(clear)

    client = await target_channel.connect()
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
    bot.add_command(ligma)
    bot.add_command(sweetland)
