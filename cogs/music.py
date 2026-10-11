import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional

# ═══════════════════════════════════════
# 🎧 إعدادات Spotify
# ═══════════════════════════════════════
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        ))
        print("✅ تم الاتصال بـ Spotify")
    except Exception as e:
        print(f"⚠️ فشل الاتصال بـ Spotify: {e}")

# ═══════════════════════════════════════
# 🎵 إعدادات yt-dlp
# ═══════════════════════════════════════
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'default_search': 'scsearch',
    'source_address': '0.0.0.0',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'age_limit': 100,
    'no_check_certificates': True,
    'geo_bypass': True,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel panic'
}


# ═══════════════════════════════════════
# 🔍 دوال Spotify
# ═══════════════════════════════════════
def search_spotify(query: str):
    if not sp:
        return None
    try:
        if "open.spotify.com" in query and "/track/" in query:
            track_id = query.split("/track/")[1].split("?")[0]
            track = sp.track(track_id)
            return {
                "name": track['name'],
                "artist": track['artists'][0]['name'],
                "thumbnail": track['album']['images'][0]['url'] if track['album']['images'] else None,
                "search_query": f"{track['name']} {track['artists'][0]['name']}"
            }
        else:
            results = sp.search(q=query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return {
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "thumbnail": track['album']['images'][0]['url'] if track['album']['images'] else None,
                    "search_query": f"{track['name']} {track['artists'][0]['name']}"
                }
    except Exception as e:
        print(f"⚠️ خطأ Spotify: {e}")
    return None


class MusicQueue:
    def __init__(self):
        self.queue = []
        self.current = None
        self.voice_client = None
        self.volume = 0.5
        self.is_playing = False
        self.is_paused = False


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    async def search_song(self, query: str):
        loop = asyncio.get_event_loop()
        if query.startswith(('http://', 'https://')):
            url = query
        else:
            url = f"scsearch1:{query}"
        try:
            data = await loop.run_in_executor(
                None,
                lambda: yt_dlp.YoutubeDL(YDL_OPTIONS).extract_info(url, download=False)
            )
            if data is None:
                return None
            if 'entries' in data:
                if not data['entries']:
                    return None
                data = data['entries'][0]
            return {
                'title': data.get('title', 'Unknown'),
                'url': data.get('url', ''),
                'webpage_url': data.get('webpage_url', ''),
                'duration': data.get('duration', 0),
                'thumbnail': data.get('thumbnail', ''),
                'uploader': data.get('uploader', 'Unknown')
            }
        except Exception as e:
            print(f"❌ خطأ في البحث: {e}")
            return None

    async def play_next(self, guild_id, channel):
        queue = self.get_queue(guild_id)
        if not queue.queue:
            queue.current = None
            queue.is_playing = False
            return
        song = queue.queue.pop(0)
        queue.current = song
        queue.is_playing = True
        queue.is_paused = False

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(song['url'], **FFMPEG_OPTIONS),
            volume=queue.volume
        )

        def after_play(error):
            if error:
                print(f"❌ خطأ في التشغيل: {error}")
            asyncio.run_coroutine_threadsafe(
                self.play_next(guild_id, channel),
                self.bot.loop
            )

        queue.voice_client.play(source, after=after_play)

        embed = discord.Embed(
            title="🎵 يتم التشغيل الآن",
            description=f"**{song['title']}**",
            color=0x1DB954
        )
        if song.get('thumbnail'):
            embed.set_thumbnail(url=song['thumbnail'])
        try:
            await channel.send(embed=embed)
        except:
            pass

    # ═══════════════════════════════════════
    # 🎵 منطق play (مشترك)
    # ═══════════════════════════════════════
    async def _play_logic(self, guild, user, voice_channel, query, respond):
        """منطق التشغيل - مشترك بين Slash و Text"""
        search_query = query
        spotify_info = None

        # لو Spotify أو بحث عادي
        if "spotify.com" in query or (sp and not query.startswith(('http://', 'https://'))):
            spotify_info = search_spotify(query)
            if spotify_info and "search_query" in spotify_info:
                search_query = spotify_info["search_query"]

        song = await self.search_song(search_query)
        if song is None:
            await respond("❌ لم يتم العثور على الأغنية")
            return

        queue = self.get_queue(guild.id)

        # الانضمام
        if not guild.voice_client:
            try:
                queue.voice_client = await voice_channel.connect()
            except Exception as e:
                await respond(f"❌ خطأ في الانضمام: {e}")
                return
        else:
            queue.voice_client = guild.voice_client

        if not queue.is_playing:
            queue.queue.append(song)
            await self.play_next(guild.id, respond.__self__.channel if hasattr(respond, '__self__') else None)
            embed = discord.Embed(
                title="🎵 جاري التشغيل",
                description=f"**[{song['title']}]({song['webpage_url']})**\nبواسطة: {song['uploader']}",
                color=0x1DB954
            )
            if spotify_info and spotify_info.get("thumbnail"):
                embed.set_thumbnail(url=spotify_info["thumbnail"])
            elif song.get('thumbnail'):
                embed.set_thumbnail(url=song['thumbnail'])
            await respond(embed=embed)
        else:
            queue.queue.append(song)
            embed = discord.Embed(
                title="✅ تمت الإضافة للقائمة",
                description=f"**[{song['title']}]({song['webpage_url']})**",
                color=0x3498DB
            )
            if song.get('thumbnail'):
                embed.set_thumbnail(url=song['thumbnail'])
            await respond(embed=embed)

    # ═══════════════════════════════════════
    # 🎵 SLASH COMMANDS
    # ═══════════════════════════════════════
    @app_commands.command(name="play", description="🎵 تشغيل أغنية")
    @app_commands.describe(query="اسم الأغنية أو الرابط")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        if not interaction.user.voice:
            return await interaction.followup.send("❌ لازم تكون في روم صوتي!")

        async def respond(content=None, embed=None):
            if embed:
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(content)

        await self._play_logic(
            interaction.guild,
            interaction.user,
            interaction.user.voice.channel,
            query,
            respond
        )

    @app_commands.command(name="skip", description="⏭️ تخطي الأغنية")
    async def skip_slash(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue.voice_client or not queue.is_playing:
            return await interaction.response.send_message("❌ مفيش حاجة شغالة", ephemeral=True)
        queue.voice_client.stop()
        await interaction.response.send_message("⏭️ تم التخطي")

    @app_commands.command(name="stop", description="⏹️ إيقاف التشغيل")
    async def stop_slash(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue.voice_client:
            return await interaction.response.send_message("❌ البوت مش في روم صوتي", ephemeral=True)
        queue.queue.clear()
        queue.current = None
        queue.is_playing = False
        await queue.voice_client.disconnect()
        await interaction.response.send_message("⏹️ تم الإيقاف")

    @app_commands.command(name="pause", description="⏸️ إيقاف مؤقت")
    async def pause_slash(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue.voice_client or not queue.is_playing:
            return await interaction.response.send_message("❌ مفيش حاجة شغالة", ephemeral=True)
        queue.voice_client.pause()
        queue.is_paused = True
        await interaction.response.send_message("⏸️ تم الإيقاف المؤقت")

    @app_commands.command(name="resume", description="▶️ استكمال")
    async def resume_slash(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue.voice_client or not queue.is_paused:
            return await interaction.response.send_message("❌ مفيش حاجة موقوفة", ephemeral=True)
        queue.voice_client.resume()
        queue.is_paused = False
        await interaction.response.send_message("▶️ تم الاستكمال")

    @app_commands.command(name="queue", description="📋 قائمة التشغيل")
    async def queue_slash(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue.current and not queue.queue:
            return await interaction.response.send_message("📭 القائمة فاضية")
        desc = ""
        if queue.current:
            desc += f"🎵 **الآن:** {queue.current['title']}\n\n"
        for i, song in enumerate(queue.queue[:10], 1):
            desc += f"`{i}.` {song['title']}\n"
        embed = discord.Embed(title="🎶 قائمة التشغيل", description=desc, color=0x9B59B6)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="🎵 الأغنية الحالية")
    async def nowplaying_slash(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue.current:
            return await interaction.response.send_message("❌ مفيش حاجة شغالة", ephemeral=True)
        embed = discord.Embed(
            title="🎵 الأغنية الحالية",
            description=f"**{queue.current['title']}**",
            color=0x1DB954
        )
        if queue.current.get('thumbnail'):
            embed.set_thumbnail(url=queue.current['thumbnail'])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="🔊 تعديل الصوت")
    @app_commands.describe(volume="مستوى الصوت (0-100)")
    async def volume_slash(self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 100]):
        queue = self.get_queue(interaction.guild.id)
        if not queue.voice_client:
            return await interaction.response.send_message("❌ البوت مش في روم", ephemeral=True)
        queue.volume = volume / 100
        if queue.voice_client.source:
            queue.voice_client.source.volume = queue.volume
        await interaction.response.send_message(f"🔊 الصوت: **{volume}%**")

    # ═══════════════════════════════════════
    # 🎵 TEXT COMMANDS (للاختصارات)
    # ═══════════════════════════════════════
    @commands.command(name="play", aliases=["p"])
    async def play_text(self, ctx, *, query: str = None):
        """!play - تشغيل أغنية"""
        if not query:
            return await ctx.send("❌ اكتب اسم الأغنية! مثال: `شغ despacito`")
        if not ctx.author.voice:
            return await ctx.send("❌ لازم تكون في روم صوتي!")

        async def respond(content=None, embed=None):
            if embed:
                await ctx.send(embed=embed)
            else:
                await ctx.send(content)

        await self._play_logic(
            ctx.guild,
            ctx.author,
            ctx.author.voice.channel,
            query,
            respond
        )

    @commands.command(name="skip")
    async def skip_text(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client or not queue.is_playing:
            return await ctx.send("❌ مفيش حاجة شغالة")
        queue.voice_client.stop()
        await ctx.send("⏭️ تم التخطي")

    @commands.command(name="stop")
    async def stop_text(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client:
            return await ctx.send("❌ البوت مش في روم")
        queue.queue.clear()
        queue.current = None
        queue.is_playing = False
        await queue.voice_client.disconnect()
        await ctx.send("⏹️ تم الإيقاف")

    @commands.command(name="pause")
    async def pause_text(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client or not queue.is_playing:
            return await ctx.send("❌ مفيش حاجة شغالة")
        queue.voice_client.pause()
        queue.is_paused = True
        await ctx.send("⏸️ تم الإيقاف المؤقت")

    @commands.command(name="resume")
    async def resume_text(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client or not queue.is_paused:
            return await ctx.send("❌ مفيش حاجة موقوفة")
        queue.voice_client.resume()
        queue.is_paused = False
        await ctx.send("▶️ تم الاستكمال")

    @commands.command(name="queue")
    async def queue_text(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue.current and not queue.queue:
            return await ctx.send("📭 القائمة فاضية")
        desc = ""
        if queue.current:
            desc += f"🎵 **الآن:** {queue.current['title']}\n\n"
        for i, song in enumerate(queue.queue[:10], 1):
            desc += f"`{i}.` {song['title']}\n"
        embed = discord.Embed(title="🎶 قائمة التشغيل", description=desc, color=0x9B59B6)
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying_text(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue.current:
            return await ctx.send("❌ مفيش حاجة شغالة")
        embed = discord.Embed(
            title="🎵 الأغنية الحالية",
            description=f"**{queue.current['title']}**",
            color=0x1DB954
        )
        if queue.current.get('thumbnail'):
            embed.set_thumbnail(url=queue.current['thumbnail'])
        await ctx.send(embed=embed)

    @commands.command(name="volume", aliases=["vol"])
    async def volume_text(self, ctx, volume: int = None):
        if volume is None:
            return await ctx.send("❌ اكتب مستوى الصوت (0-100)")
        if volume < 0 or volume > 100:
            return await ctx.send("❌ الصوت من 0 لـ 100")
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client:
            return await ctx.send("❌ البوت مش في روم")
        queue.volume = volume / 100
        if queue.voice_client.source:
            queue.voice_client.source.volume = queue.volume
        await ctx.send(f"🔊 الصوت: **{volume}%**")


async def setup(bot):
    await bot.add_cog(Music(bot))