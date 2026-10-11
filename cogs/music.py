import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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
# 🔍 دالة Spotify
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

    # ═══════════════════════════════════════
    # 🔧 دوال مساعدة
    # ═══════════════════════════════════════
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
            if channel:
                await channel.send(embed=embed)
        except:
            pass

    async def _play_logic(self, ctx: commands.Context, query: str):
        """منطق التشغيل - مشترك"""
        search_query = query
        spotify_info = None

        if "spotify.com" in query or (sp and not query.startswith(('http://', 'https://'))):
            spotify_info = search_spotify(query)
            if spotify_info and "search_query" in spotify_info:
                search_query = spotify_info["search_query"]

        song = await self.search_song(search_query)
        if song is None:
            await ctx.send("❌ لم يتم العثور على الأغنية")
            return

        queue = self.get_queue(ctx.guild.id)

        # الانضمام للقناة الصوتية
        if not ctx.guild.voice_client:
            try:
                queue.voice_client = await ctx.author.voice.channel.connect()
            except Exception as e:
                await ctx.send(f"❌ خطأ في الانضمام: {e}")
                return
        else:
            queue.voice_client = ctx.guild.voice_client

        if not queue.is_playing:
            queue.queue.append(song)
            await self.play_next(ctx.guild.id, ctx.channel)
            embed = discord.Embed(
                title="🎵 جاري التشغيل",
                description=f"**[{song['title']}]({song['webpage_url']})**\nبواسطة: {song['uploader']}",
                color=0x1DB954
            )
            if spotify_info and spotify_info.get("thumbnail"):
                embed.set_thumbnail(url=spotify_info["thumbnail"])
            elif song.get('thumbnail'):
                embed.set_thumbnail(url=song['thumbnail'])
            await ctx.send(embed=embed)
        else:
            queue.queue.append(song)
            embed = discord.Embed(
                title="✅ تمت الإضافة للقائمة",
                description=f"**[{song['title']}]({song['webpage_url']})**",
                color=0x3498DB
            )
            if song.get('thumbnail'):
                embed.set_thumbnail(url=song['thumbnail'])
            await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎵 الأوامر الأساسية
    # ═══════════════════════════════════════

    @commands.command(
        name="play",
        aliases=["p", "شغل", "شغ"],
        description="🎵 تشغيل أغنية أو إضافتها للقائمة"
    )
    async def play(self, ctx: commands.Context, *, query: str = None):
        """تشغيل أغنية"""
        if not query:
            await ctx.send("❌ اكتب اسم الأغنية! مثال: `!شغل despacito`", delete_after=8)
            return
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي!", delete_after=8)
            return

        async with ctx.typing():
            await self._play_logic(ctx, query)

    @commands.command(
        name="skip",
        aliases=["s", "تخطي", "سكيب"],
        description="⏭️ تخطي الأغنية الحالية"
    )
    async def skip(self, ctx: commands.Context):
        """تخطي الأغنية"""
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client or not queue.is_playing:
            await ctx.send("❌ مفيش حاجة شغالة", delete_after=6)
            return
        queue.voice_client.stop()
        await ctx.send("⏭️ تم التخطي")

    @commands.command(
        name="stop",
        aliases=["st", "ايقاف", "وقف"],
        description="⏹️ إيقاف التشغيل ومسح القائمة"
    )
    async def stop(self, ctx: commands.Context):
        """إيقاف التشغيل"""
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client:
            await ctx.send("❌ البوت مش في روم صوتي", delete_after=6)
            return
        queue.queue.clear()
        queue.current = None
        queue.is_playing = False
        queue.is_paused = False
        await queue.voice_client.disconnect()
        await ctx.send("⏹️ تم الإيقاف")

    @commands.command(
        name="pause",
        aliases=["pa", "ايقاف-مؤقت"],
        description="⏸️ إيقاف مؤقت"
    )
    async def pause(self, ctx: commands.Context):
        """إيقاف مؤقت"""
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client or not queue.is_playing:
            await ctx.send("❌ مفيش حاجة شغالة", delete_after=6)
            return
        queue.voice_client.pause()
        queue.is_paused = True
        await ctx.send("⏸️ تم الإيقاف المؤقت")

    @commands.command(
        name="resume",
        aliases=["res", "استكمال", "كمل"],
        description="▶️ استكمال التشغيل"
    )
    async def resume(self, ctx: commands.Context):
        """استكمال التشغيل"""
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client or not queue.is_paused:
            await ctx.send("❌ مفيش حاجة موقوفة", delete_after=6)
            return
        queue.voice_client.resume()
        queue.is_paused = False
        await ctx.send("▶️ تم الاستكمال")

    @commands.command(
        name="queue",
        aliases=["q", "قائمة", "القائمة"],
        description="📋 عرض قائمة التشغيل"
    )
    async def queue_cmd(self, ctx: commands.Context):
        """عرض القائمة"""
        queue = self.get_queue(ctx.guild.id)
        if not queue.current and not queue.queue:
            await ctx.send("📭 القائمة فاضية")
            return
        desc = ""
        if queue.current:
            desc += f"🎵 **الآن:** {queue.current['title']}\n\n"
        for i, song in enumerate(queue.queue[:10], 1):
            desc += f"`{i}.` {song['title']}\n"
        embed = discord.Embed(title="🎶 قائمة التشغيل", description=desc, color=0x9B59B6)
        await ctx.send(embed=embed)

    @commands.command(
        name="nowplaying",
        aliases=["np", "الحالية", "الان"],
        description="🎵 عرض الأغنية الحالية"
    )
    async def nowplaying(self, ctx: commands.Context):
        """الأغنية الحالية"""
        queue = self.get_queue(ctx.guild.id)
        if not queue.current:
            await ctx.send("❌ مفيش حاجة شغالة", delete_after=6)
            return
        embed = discord.Embed(
            title="🎵 الأغنية الحالية",
            description=f"**{queue.current['title']}**",
            color=0x1DB954
        )
        if queue.current.get('thumbnail'):
            embed.set_thumbnail(url=queue.current['thumbnail'])
        await ctx.send(embed=embed)

    @commands.command(
        name="volume",
        aliases=["vol", "صوت", "الصوت"],
        description="🔊 تعديل مستوى الصوت (0-100)"
    )
    async def volume(self, ctx: commands.Context, volume: int = None):
        """تعديل الصوت"""
        if volume is None:
            queue = self.get_queue(ctx.guild.id)
            current = int(queue.volume * 100)
            await ctx.send(f"🔊 مستوى الصوت الحالي: **{current}%**")
            return
        if volume < 0 or volume > 100:
            await ctx.send("❌ الصوت من **0** لـ **100**", delete_after=6)
            return
        queue = self.get_queue(ctx.guild.id)
        if not queue.voice_client:
            await ctx.send("❌ البوت مش في روم", delete_after=6)
            return
        queue.volume = volume / 100
        if queue.voice_client.source:
            queue.voice_client.source.volume = queue.volume
        await ctx.send(f"🔊 الصوت: **{volume}%**")

    # ═══════════════════════════════════════
    # 🔀 أمر إضافي: تبديل/خلط القائمة
    # ═══════════════════════════════════════
    @commands.command(
        name="shuffle",
        aliases=["sh", "خلط", "عشوائي"],
        description="🔀 خلط قائمة التشغيل"
    )
    async def shuffle(self, ctx: commands.Context):
        """خلط القائمة"""
        import random
        queue = self.get_queue(ctx.guild.id)
        if len(queue.queue) < 2:
            await ctx.send("❌ القائمة مش كفاية للخلط", delete_after=6)
            return
        random.shuffle(queue.queue)
        await ctx.send("🔀 تم خلط القائمة")

    # ═══════════════════════════════════════
    # ⚠️ معالجة الأخطاء
    # ═══════════════════════════════════════
    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص بيانات: `{error.param.name}`", delete_after=8)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات المدخلة!", delete_after=8)
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("❌ حصل خطأ أثناء تنفيذ الأمر!", delete_after=8)
            print(f"❌ {error}")


async def setup(bot):
    await bot.add_cog(Music(bot))