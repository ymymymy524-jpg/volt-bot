import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp
from typing import Optional

# إعدادات yt-dlp
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel panic'
}

class MusicQueue:
    """فئة لإدارة قائمة التشغيل لكل سيرفر"""
    def __init__(self):
        self.queue = []  # قائمة الأغاني
        self.current = None  # الأغنية الحالية
        self.voice_client = None  # عميل الصوت
        self.volume = 0.5  # الصوت الافتراضي 50%
        self.is_playing = False
        self.is_paused = False

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # قاموس queues لكل guild_id

    # دالة لجلب أو إنشاء queue للسيرفر
    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    # دالة للبحث عن أغنية على YouTube
    async def search_song(self, query: str):
        """البحث عن أغنية على YouTube وإرجاع معلوماتها"""
        loop = asyncio.get_event_loop()
        
        # إذا كان رابط مباشر
        if query.startswith('http://') or query.startswith('https://'):
            url = query
        else:
            # البحث عن الكلمة
            url = f"ytsearch1:{query}"

        try:
            # استخراج معلومات الفيديو
            data = await loop.run_in_executor(
                None, 
                lambda: yt_dlp.YoutubeDL(YDL_OPTIONS).extract_info(url, download=False)
            )

            if data is None:
                return None

            # إذا كان بحث، نأخذ أول نتيجة
            if 'entries' in data:
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

    # دالة لتشغيل الأغنية التالية من الـ queue
    async def play_next(self, guild_id):
        """تشغيل الأغنية التالية من قائمة التشغيل"""
        queue = self.get_queue(guild_id)
        
        if not queue.queue:
            queue.current = None
            queue.is_playing = False
            return

        # أخذ أول أغنية من الـ queue
        song = queue.queue.pop(0)
        queue.current = song
        queue.is_playing = True
        queue.is_paused = False

        # إنشاء source الصوت
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(song['url'], **FFMPEG_OPTIONS),
            volume=queue.volume
        )

        # دالة تُستدعى بعد انتهاء الأغنية
        def after_play(error):
            if error:
                print(f"❌ خطأ في التشغيل: {error}")
            
            # تشغيل الأغنية التالية
            asyncio.run_coroutine_threadsafe(
                self.play_next(guild_id), 
                self.bot.loop
            )

        # تشغيل الأغنية
        queue.voice_client.play(source, after=after_play)

    # أمر /play لتشغيل أغنية
    @app_commands.command(name="play", description="تشغيل أغنية من YouTube")
    @app_commands.describe(query="اسم الأغنية أو الرابط")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        # التحقق من أن المستخدم في voice channel
        if not interaction.user.voice:
            embed = discord.Embed(
                title="❌ يجب الانضمام لروم صوتي",
                description="يجب أن تكون في روم صوتي لاستخدام الأمر ده",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return

        # البحث عن الأغنية
        song = await self.search_song(query)
        
        if song is None:
            embed = discord.Embed(
                title="❌ لم يتم العثور على الأغنية",
                description="لم أتمكن من العثور على الأغنية المطلوبة",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return

        queue = self.get_queue(interaction.guild.id)

        # الانضمام للروم الصوتي إذا لم يكن البوت موجود
        if not interaction.guild.voice_client:
            try:
                queue.voice_client = await interaction.user.voice.channel.connect()
            except Exception as e:
                embed = discord.Embed(
                    title="❌ خطأ في الانضمام",
                    description=f"لم أتمكن من الانضمام للروم الصوتي: {e}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
        else:
            queue.voice_client = interaction.guild.voice_client

        # إذا كان البوت لا يشغل شيء، شغل الأغنية مباشرة
        if not queue.is_playing:
            queue.queue.append(song)
            await self.play_next(interaction.guild.id)
            
            embed = discord.Embed(
                title="🎵 جاري التشغيل",
                description=f"**[{song['title']}]({song['webpage_url']})**\nبواسطة: {song['uploader']}",
                color=discord.Color.green()
            )
            if song['thumbnail']:
                embed.set_thumbnail(url=song['thumbnail'])
            embed.set_footer(text=f"المدة: {self.format_duration(song['duration'])}")
            await interaction.followup.send(embed=embed)
        else:
            # إضافة الأغنية للـ queue
            queue.queue.append(song)
            
            embed = discord.Embed(
                title="✅ تمت الإضافة لقائمة التشغيل",
                description=f"**[{song['title']}]({song['webpage_url']})**\nبواسطة: {song['uploader']}",
                color=discord.Color.blue()
            )
            if song['thumbnail']:
                embed.set_thumbnail(url=song['thumbnail'])
            embed.set_footer(text=f"الموقع في القائمة: #{len(queue.queue)} | المدة: {self.format_duration(song['duration'])}")
            await interaction.followup.send(embed=embed)

    # أمر /pause لإيقاف مؤقت
    @app_commands.command(name="pause", description="إيقاف الأغنية مؤقتاً")
    async def pause(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client or not queue.is_playing:
            embed = discord.Embed(
                title="❌ لا يوجد أغنية قيد التشغيل",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        if queue.is_paused:
            embed = discord.Embed(
                title="⚠️ الأغنية موقوفة بالفعل",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return

        queue.voice_client.pause()
        queue.is_paused = True

        embed = discord.Embed(
            title="⏸️ تم الإيقاف المؤقت",
            description="تم إيقاف الأغنية مؤقتاً",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /resume لاستكمال الأغنية
    @app_commands.command(name="resume", description="استكمال الأغنية")
    async def resume(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client or not queue.is_paused:
            embed = discord.Embed(
                title="❌ لا توجد أغنية موقوفة",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        queue.voice_client.resume()
        queue.is_paused = False

        embed = discord.Embed(
            title="▶️ تم الاستكمال",
            description="جاري استكمال الأغنية",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /skip لتخطي الأغنية
    @app_commands.command(name="skip", description="تخطي الأغنية الحالية")
    async def skip(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client or not queue.is_playing:
            embed = discord.Embed(
                title="❌ لا يوجد أغنية قيد التشغيل",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        queue.voice_client.stop()

        embed = discord.Embed(
            title="⏭️ تم التخطي",
            description="تم تخطي الأغنية الحالية",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /queue لعرض قائمة التشغيل
    @app_commands.command(name="queue", description="عرض قائمة التشغيل")
    async def queue_display(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.current and not queue.queue:
            embed = discord.Embed(
                title="📭 قائمة التشغيل فارغة",
                description="لا توجد أغاني في القائمة",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return

        description = ""

        # الأغنية الحالية
        if queue.current:
            description += f"🎵 **الآن:** [{queue.current['title']}]({queue.current['webpage_url']})\n\n"

        # الأغاني في القائمة
        if queue.queue:
            description += "**📋 قائمة التشغيل:**\n"
            for i, song in enumerate(queue.queue[:10], 1):
                description += f"`{i}.` [{song['title']}]({song['webpage_url']})\n"
            
            if len(queue.queue) > 10:
                description += f"\n... و {len(queue.queue) - 10} أغاني أخرى"

        embed = discord.Embed(
            title="🎶 قائمة التشغيل",
            description=description,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"إجمالي الأغاني: {len(queue.queue) + (1 if queue.current else 0)}")
        
        await interaction.response.send_message(embed=embed)

    # أمر /stop لإيقاف التشغيل والخروج
    @app_commands.command(name="stop", description="إيقاف التشغيل والخروج من الروم")
    async def stop(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client:
            embed = discord.Embed(
                title="❌ البوت مش في روم صوتي",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        # مسح الـ queue
        queue.queue.clear()
        queue.current = None
        queue.is_playing = False
        queue.is_paused = False

        # الخروج من الروم
        await queue.voice_client.disconnect()

        embed = discord.Embed(
            title="👋 تم الخروج",
            description="تم إيقاف التشغيل والخروج من الروم الصوتي",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /volume لتعديل الصوت
    @app_commands.command(name="volume", description="تعديل مستوى الصوت")
    @app_commands.describe(volume="مستوى الصوت من 0 إلى 100")
    async def volume(self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 100]):
        queue = self.get_queue(interaction.guild.id)

        if not queue.voice_client:
            embed = discord.Embed(
                title="❌ البوت مش في روم صوتي",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        # تعديل الصوت (من 0-100 إلى 0.0-1.0)
        queue.volume = volume / 100
        if queue.voice_client.source:
            queue.voice_client.source.volume = queue.volume

        embed = discord.Embed(
            title="🔊 تم تعديل الصوت",
            description=f"مستوى الصوت الآن: **{volume}%**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /nowplaying لعرض الأغنية الحالية
    @app_commands.command(name="nowplaying", description="عرض الأغنية الحالية")
    async def nowplaying(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.current or not queue.is_playing:
            embed = discord.Embed(
                title="❌ لا يوجد أغنية قيد التشغيل",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        song = queue.current
        embed = discord.Embed(
            title="🎵 الأغنية الحالية",
            description=f"**[{song['title']}]({song['webpage_url']})**\nبواسطة: {song['uploader']}",
            color=discord.Color.green()
        )
        if song['thumbnail']:
            embed.set_thumbnail(url=song['thumbnail'])
        
        embed.add_field(name="📊 الصوت", value=f"{int(queue.volume * 100)}%", inline=True)
        embed.add_field(name="⏱️ المدة", value=self.format_duration(song['duration']), inline=True)
        
        await interaction.response.send_message(embed=embed)

    # دالة مساعدة لتنسيق المدة
    def format_duration(self, seconds):
        """تنسيق المدة من ثواني إلى صيغة MM:SS"""
        if not seconds:
            return "0:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

# دالة تحميل الـ Cog للبوت
async def setup(bot):
    await bot.add_cog(Music(bot))