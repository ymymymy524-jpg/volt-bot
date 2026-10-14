import discord
from discord.ext import commands
from discord import app_commands
import edge_tts
import asyncio
import os
import tempfile
from config import Colors

# الأصوات المتاحة
VOICES = {
    "ar": "ar-EG-SalmaNeural",      # عربي (مصر) - أنثى
    "ar-male": "ar-EG-ShakirNeural", # عربي (مصر) - ذكر
    "ar-sa": "ar-SA-ZariyahNeural",  # عربي (سعودي) - أنثى
    "ar-sa-male": "ar-SA-HamedNeural", # عربي (سعودي) - ذكر
    "en": "en-US-AriaNeural",        # إنجليزي - أنثى
    "en-male": "en-US-GuyNeural",    # إنجليزي - ذكر
}

# الصوت الافتراضي
DEFAULT_VOICE = "ar-male"


class TTS(commands.Cog):
    """🔊 أوامر تحويل النص لصوت"""

    def __init__(self, bot):
        self.bot = bot
        self.voice_settings = {}  # {guild_id: voice_name}

    def get_voice(self, guild_id):
        return self.voice_settings.get(guild_id, DEFAULT_VOICE)

    async def generate_audio(self, text, voice):
        """تحويل النص لملف صوتي"""
        try:
            communicate = edge_tts.Communicate(text, voice)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            await communicate.save(temp_file.name)
            return temp_file.name
        except Exception as e:
            print(f"❌ خطأ TTS: {e}")
            return None

    async def play_audio(self, ctx, audio_path):
        """تشغيل الملف الصوتي"""
        try:
            # لو البوت مش في روم صوتي
            if not ctx.voice_client:
                if not ctx.author.voice:
                    await ctx.send("❌ لازم تكون في روم صوتي!")
                    return False
                await ctx.author.voice.channel.connect()
            # لو في روم تاني
            elif ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.voice_client.move_to(ctx.author.voice.channel)

            # تشغيل الصوت
            source = discord.FFmpegPCMAudio(audio_path)
            ctx.voice_client.play(source)
            return True
        except Exception as e:
            await ctx.send(f"❌ خطأ في التشغيل: `{e}`")
            return False

    # ═══════════════════════════════════════
    # 🔊 !speak
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="speak",
        aliases=["قول", "تكلم", "انطق"],
        description="🔊 البوت يقول النص في الروم الصوتي"
    )
    @app_commands.describe(text="النص اللي عايز البوت يقوله")
    async def speak(self, ctx: commands.Context, *, text: str):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي الأول!")
            return

        if len(text) > 500:
            await ctx.send("❌ النص طويل أوي! (الحد 500 حرف)")
            return

        msg = await ctx.send("⏳ جاري تحويل النص لصوت...")

        voice = self.get_voice(ctx.guild.id)
        audio_path = await self.generate_audio(text, voice)

        if not audio_path:
            await msg.edit(content="❌ فشل تحويل النص لصوت!")
            return

        # اتأكد إن الروم الصوتي
        try:
            success = await self.play_audio(ctx, audio_path)
            if success:
                await msg.edit(content=f"🔊 **جاري التشغيل...**\n> {text}")
            # امسح الملف بعد ما يخلص
            await asyncio.sleep(1)
            try:
                # استنى لحد ما الصوت يخلص
                while ctx.voice_client and ctx.voice_client.is_playing():
                    await asyncio.sleep(0.5)
                os.remove(audio_path)
            except:
                pass
        except Exception as e:
            await msg.edit(content=f"❌ خطأ: `{e}`")

    # ═══════════════════════════════════════
    # 🔊 !voices — عرض الأصوات
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="voices",
        aliases=["اصوات", "الأصوات"],
        description="🔊 عرض الأصوات المتاحة"
    )
    async def voices(self, ctx: commands.Context):
        embed = discord.Embed(title="🎙️ الأصوات المتاحة", color=Colors.INFO)
        for key, val in VOICES.items():
            embed.add_field(name=f"`{key}`", value=val, inline=False)
        embed.set_footer(text="استخدم !setvoice <اسم الصوت> لتغيير الصوت")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔄 !setvoice — تغيير الصوت
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="setvoice",
        aliases=["غير_الصوت", "عين_الصوت"],
        description="🔄 تغيير صوت البوت"
    )
    @app_commands.describe(voice="اسم الصوت (من !voices)")
    async def setvoice(self, ctx: commands.Context, voice: str):
        if voice not in VOICES:
            await ctx.send(f"❌ الصوت `{voice}` مش موجود!\nاستخدم `!voices` لعرض الأصوات.")
            return
        self.voice_settings[ctx.guild.id] = voice
        await ctx.send(f"✅ تم تغيير الصوت إلى `{voice}`")

    # ═══════════════════════════════════════
    # 🛑 !stoptts — إيقاف الصوت
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="stoptts",
        aliases=["ايقاف_الصوت"],
        description="🛑 إيقاف الصوت الحالي"
    )
    async def stoptts(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("🛑 تم الإيقاف")
        else:
            await ctx.send("❌ مفيش حاجة شغالة!")

    # ═══════════════════════════════════════
    # 👋 !leavetts — خروج من الروم
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="leavetts",
        aliases=["اطلع_من_الروم"],
        description="👋 البوت يطلع من الروم الصوتي"
    )
    async def leavetts(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 طلعت من الروم")
        else:
            await ctx.send("❌ أنا مش في روم!")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(TTS(bot))