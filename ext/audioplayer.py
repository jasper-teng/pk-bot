import asyncio
from discord import FFmpegOpusAudio
from discord.ext import commands


class AudioPlayer(commands.Cog, name='VC Stuff'):
    def __init__(self):
        self._voice_client = None
        self._cur_channel = None
        self._audio_file = None

    @commands.command(aliases=['sweetsland'])
    async def sweetland(self, ctx, channel_num=None):
        """ ♫♫♩～ """
        await self._play(ctx, 'ext/sweetland.mp3', channel_num)

    @commands.command()
    async def shart(self, ctx, channel_num=None):
        """ AAAAAAAAAAAAAAAA """
        await self._play(ctx, 'ext/shart.mp3', channel_num)

    @commands.command()
    async def stop(self, ctx):
        if self._voice_client is None:
            return

        client = self._voice_client
        self._voice_client = None

        client.stop()
        await client.disconnect()
        await ctx.message.add_reaction('🆗')

    async def _play(self, ctx, fn, channel_num):
        """
        Play music in a voice channel.

        If channel number isn't given, defaults to the user's voice channel.
        If user isn't in a voice channel, defaults to the first voice channel that is occupied.
        """
        if self._voice_client is not None:
            if self._audio_file == fn:
                return
            else:
                self._audio_file = fn

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
                if target_channel is None:
                    await ctx.reply('No voice channel available to bind to!')
                    return
        else:
            target_channel = ctx.guild.voice_channels[int(channel_num) - 1]
        audio = FFmpegOpusAudio(fn)
        await ctx.message.add_reaction('🆗')

        stop_event = asyncio.Event()
        loop = asyncio.get_event_loop()

        def after(err):
            if err:
                raise err

            def clear():
                stop_event.set()
            loop.call_soon_threadsafe(clear)

        if self._cur_channel is None:
            client = await target_channel.connect()
            self._cur_channel = target_channel
            self._voice_client = client
            client.play(audio, after=after)
        elif self._cur_channel != target_channel:
            client = self._voice_client
            await self._voice_client.move_to(target_channel)
            self._cur_channel = target_channel
            client.source = audio
        else:
            client = self._voice_client
            client.source = audio
            return

        await stop_event.wait()
        await client.disconnect()
        self._voice_client = None
        self._cur_channel = None
        self._audio_file = None


def setup(bot):
    bot.add_cog(AudioPlayer())
