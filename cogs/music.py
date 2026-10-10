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
# 🎵 إعدادات yt-dlp - SoundCloud
# ═══════════════════════════════════════
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'default_search': 'scsearch',  # ← SoundCloud Search
    'source_address': '0.0.0.0',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
    """البحث في Spotify وإرجاع معلومات الأغنية"""
    if not sp:
        return None
    
    try:
        if "open.spotify.com" in query:
            if "/track/" in query:
                track_id = query.split("/track/")[1].split("?")[0]
                track = sp.track(track_id)
                return {
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "thumbnail": track['album']['images'][0]['url'] if track['album']['images'] else None,
                    "duration": track['duration_ms'] // 1000,
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
                    "duration": track['duration_ms'] // 1000,
                    "search_query": f"{track['name']} {track['artists'][0]['name']}"
                }
    except Exception as e:
        print(f"⚠️ خطأ في Spotify: {e}")
    
    return None


class MusicQueue:
    """فئة لإدارة قائمة التشغيل لكل سيرفر"""
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
        """البحث عن أغنية على SoundCloud"""
        loop = asyncio.get_event_loop()
        
        # لو رابط مباشر
        if query.startswith('http://') or query.startswith('https://'):
            url = query
        else:
            # بحث SoundCloud
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

    async def play_next(self, guild_id):
        """تشغيل الأغنية التالية"""
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
                self.play_next(guild_id), 
                self.bot.loop
            )

        queue.voice_client.play(source, after=after_play)

    # ═══════════════════════════════════════
    # 🎵 أمر /play
    # ═══════════════════════════════════════
    @app_commands.command(name="play", description="🎵 تشغيل أغنية من SoundCloud أو Spotify")
    @app_commands.describe(query="اسم الأغنية أو الرابط (SoundCloud / Spotify)")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            embed = discord.Embed(
                title="❌ يجب الانضمام لروم صوتي",
                description="يجب أن تكون في روم صوتي لاستخدام الأمر ده",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return

        search_query = query
        spotify_info = None

        # لو Spotify أو بحث عادي، جيب معلومات من Spotify
        if "spotify.com" in query or (sp and not query.startswith(('http://', 'https://'))):
            spotify_info = search_spotify(query)
            if spotify_info and "search_query" in spotify_info:
                search_query = spotify_info["search_query"]

        # البحث في SoundCloud
        song = await self.search_song(search_query)
        
        if song is None:
            embed = discord.Embed(
                title="❌ لم يتم العثور على الأغنية",
                description=f"لم أتمكن من العثور على: `{query}`\nجرب اسم تاني أو رابط مباشر",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return

        queue = self.get_queue(interaction.guild.id)

        # الانضمام للروم
        if not interaction.guild.voice_client:
            try:
                queue.voice_client = await interaction.user.voice.channel.connect()
            except Exception as e:
                embed = discord.Embed(
                    title="❌ خطأ في الانضمام",
                    description=f"لم أتمكن من الانضمام: {e}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
        else:
            queue.voice_client = interaction.guild.voice_client

        # لو مفيش حاجة شغالة
        if not queue.is_playing:
            queue.queue.append(song)
            await self.play_next(interaction.guild.id)
            
            embed = discord.Embed(
                title="🎵 جاري التشغيل",
                description=f"**[{song['title']}]({song['webpage_url']})**\nبواسطة: {song['uploader']}",
                color=0x1DB954
            )
            if spotify_info and spotify_info.get("thumbnail"):
                embed.set_thumbnail(url=spotify_info["thumbnail"])
                embed.add_field(name="🎧 Spotify", value=f"{spotify_info['name']} - {spotify_info['artist']}", inline=False)
            elif song['thumbnail']:
                embed.set_thumbnail(url=song['thumbnail'])
            
            embed.set_footer(text=f"المدة: {self.format_duration(song['duration'])}")
            await interaction.followup.send(embed=embed)
        else:
            queue.queue.append(song)
            
            embed = discord.Embed(
                title="✅ تمت الإضافة لقائمة التشغيل",
                description=f"**[{song['title']}]({song['webpage_url']})**\nبواسطة: {song['uploader']}",
                color=discord.Color.blue()
            )
            if spotify_info and spotify_info.get("thumbnail"):
                embed.set_thumbnail(url=spotify_info["thumbnail"])
                embed.add_field(name="🎧 Spotify", value=f"{spotify_info['name']} - {spotify_info['artist']}", inline=False)
            elif song['thumbnail']:
                embed.set_thumbnail(url=song['thumbnail'])
            
            embed.set_footer(text=f"الموقع: #{len(queue.queue)} | المدة: {self.format_duration(song['duration'])}")
            await interaction.followup.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎧 أمر /spotify-search
    # ═══════════════════════════════════════
    @app_commands.command(name="spotify-search", description="🎧 البحث في Spotify")
    @app_commands.describe(query="اسم الأغنية")
    async def spotify_search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        
        if not sp:
            return await interaction.followup.send("❌ Spotify غير مفعّل")
        
        try:
            results = sp.search(q=query, type='track', limit=5)
            
            if not results['tracks']['items']:
                return await interaction.followup.send("❌ مفيش نتائج")
            
            embed = discord.Embed(
                title="🎧 نتائج Spotify",
                description=f"البحث عن: **{query}**",
                color=0x1DB954
            )
            
            for i, track in enumerate(results['tracks']['items'], 1):
                name = track['name']
                artist = track['artists'][0]['name']
                duration = track['duration_ms'] // 1000
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"👤 {artist}\n⏱️ {self.format_duration(duration)}",
                    inline=False
                )
            
            embed.set_footer(text="استخدم /play لتشغيل الأغنية")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}")

    # ═══════════════════════════════════════
    # ⏸️ /pause
    # ═══════════════════════════════════════
    @app_commands.command(name="pause", description="⏸️ إيقاف الأغنية مؤقتاً")
    async def pause(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client or not queue.is_playing:
            embed = discord.Embed(title="❌ لا يوجد أغنية قيد التشغيل", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        if queue.is_paused:
            embed = discord.Embed(title="⚠️ الأغنية موقوفة بالفعل", color=discord.Color.orange())
            await interaction.response.send_message(embed=embed)
            return

        queue.voice_client.pause()
        queue.is_paused = True
        embed = discord.Embed(title="⏸️ تم الإيقاف المؤقت", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # ▶️ /resume
    # ═══════════════════════════════════════
    @app_commands.command(name="resume", description="▶️ استكمال الأغنية")
    async def resume(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client or not queue.is_paused:
            embed = discord.Embed(title="❌ لا توجد أغنية موقوفة", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        queue.voice_client.resume()
        queue.is_paused = False
        embed = discord.Embed(title="▶️ تم الاستكمال", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # ⏭️ /skip
    # ═══════════════════════════════════════
    @app_commands.command(name="skip", description="⏭️ تخطي الأغنية الحالية")
    async def skip(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client or not queue.is_playing:
            embed = discord.Embed(title="❌ لا يوجد أغنية قيد التشغيل", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        queue.voice_client.stop()
        embed = discord.Embed(title="⏭️ تم التخطي", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # 📋 /queue
    # ═══════════════════════════════════════
    @app_commands.command(name="queue", description="📋 عرض قائمة التشغيل")
    async def queue_display(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.current and not queue.queue:
            embed = discord.Embed(title="📭 قائمة التشغيل فارغة", color=discord.Color.orange())
            await interaction.response.send_message(embed=embed)
            return

        description = ""
        if queue.current:
            description += f"🎵 **الآن:** [{queue.current['title']}]({queue.current['webpage_url']})\n\n"

        if queue.queue:
            description += "**📋 قائمة التشغيل:**\n"
            for i, song in enumerate(queue.queue[:10], 1):
                description += f"`{i}.` [{song['title']}]({song['webpage_url']})\n"
            
            if len(queue.queue) > 10:
                description += f"\n... و {len(queue.queue) - 10} أغاني أخرى"

        embed = discord.Embed(title="🎶 قائمة التشغيل", description=description, color=discord.Color.purple())
        embed.set_footer(text=f"إجمالي: {len(queue.queue) + (1 if queue.current else 0)}")
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # ⏹️ /stop
    # ═══════════════════════════════════════
    @app_commands.command(name="stop", description="⏹️ إيقاف التشغيل والخروج")
    async def stop(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client:
            embed = discord.Embed(title="❌ البوت مش في روم صوتي", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        queue.queue.clear()
        queue.current = None
        queue.is_playing = False
        queue.is_paused = False
        await queue.voice_client.disconnect()

        embed = discord.Embed(title="👋 تم الخروج", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # 🔊 /volume
    # ═══════════════════════════════════════
    @app_commands.command(name="volume", description="🔊 تعديل مستوى الصوت")
    @app_commands.describe(volume="مستوى الصوت من 0 إلى 100")
    async def volume(self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 100]):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client:
            embed = discord.Embed(title="❌ البوت مش في روم صوتي", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        queue.volume = volume / 100
        if queue.voice_client.source:
            queue.voice_client.source.volume = queue.volume

        embed = discord.Embed(title="🔊 تم تعديل الصوت", description=f"مستوى الصوت: **{volume}%**", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # 🎵 /nowplaying
    # ═══════════════════════════════════════
    @app_commands.command(name="nowplaying", description="🎵 عرض الأغنية الحالية")
    async def nowplaying(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.current or not queue.is_playing:
            embed = discord.Embed(title="❌ لا يوجد أغنية قيد التشغيل", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        song = queue.current
        embed = discord.Embed(
            title="🎵 الأغنية الحالية",
            description=f"**[{song['title']}]({song['webpage_url']})**\nبواسطة: {song['uploader']}",
            color=0x1DB954
        )
        if song['thumbnail']:
            embed.set_thumbnail(url=song['thumbnail'])
        
        embed.add_field(name="📊 الصوت", value=f"{int(queue.volume * 100)}%", inline=True)
        embed.add_field(name="⏱️ المدة", value=self.format_duration(song['duration']), inline=True)
        await interaction.response.send_message(embed=embed)

    def format_duration(self, seconds):
        """تنسيق المدة"""
        if not seconds:
            return "0:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"


async def setup(bot):
    await bot.add_cog(Music(bot))