from discord import app_commands
from discord.ext import commands
import waterlink
from config import Colors

# ═══════════════════════════════════════
# 🔧 إعدادات Lavalink — Lavalink مجاني
# ═══════════════════════════════════════
LAVALINK_HOST = "lavalinkv4.serenetia.com"
LAVALINK_PORT = 443
LAVALINK_PASSWORD = "https://dsc.gg/ajidevserver"
LAVALINK_SECURE = True


class Music(commands.Cog):
    """🎵 نظام الموسيقى — Lavalink + Waterlink"""

    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.ready = False

    @commands.Cog.listener()
    async def on_ready(self):
        """الاتصال بـ Lavalink"""
        if self.client is not None:
            return

        try:
            self.client = waterlink.WaterlinkClient(bot=self.bot)

            await self.client.add_node(
                host=LAVALINK_HOST,
                port=LAVALINK_PORT,
                password=LAVALINK_PASSWORD,
                secure=LAVALINK_SECURE,
            )

            self.ready = True
            print("✅ [Music] Lavalink متصل")
        except Exception as e:
            print(f"❌ [Music] فشل الاتصال بـ Lavalink: {e}")
            import traceback
            traceback.print_exc()

    def _get_player(self, guild_id: int):
        """جيب الـ player"""
        return self.client.get_player(guild_id) if self.client else None

    # ═══════════════════════════════════════
    # 🎵 !play / /play
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="play",
        aliases=["شغل", "شغ"],
        description="🎵 تشغيل أغنية أو إضافتها للقائمة"
    )
    @app_commands.describe(query="اسم الأغنية أو الرابط")
    async def play(self, ctx: commands.Context, *, query: str = None):
        """تشغيل أغنية"""
        if not self.ready:
            await ctx.send("❌ نظام الموسيقى مش جاهز دلوقتي، استنى شوية")
            return

        if not query:
            await ctx.send("❌ اكتب اسم الأغنية! مثال: `/play despacito`")
            return

        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي!")
            return

        if ctx.interaction:
            await ctx.defer()

        try:
            # الاتصال بالروم الصوتي
            player = await self.client.connect(ctx.guild.id, ctx.author.voice.channel.id)

            # بحث
            result = await self.client.search(query)

            if not result or not result.tracks:
                await ctx.send("❌ لم يتم العثور على الأغنية")
                return

            track = result.tracks[0]
            await player.enqueue(track.with_requester(ctx.author.id))

            embed = discord.Embed(
                title="✅ تمت الإضافة للقائمة",
                description=f"**[{track.title}]({track.uri})**\nبواسطة: {track.author}",
                color=0x1DB954
            )
            if track.artwork_url:
                embed.set_thumbnail(url=track.artwork_url)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ حصل خطأ: {str(e)[:200]}")
            print(f"❌ [Music] play error: {e}")
            import traceback
            traceback.print_exc()

    # ═══════════════════════════════════════
    # ⏭️ !skip / /skip
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="skip",
        aliases=["تخطي", "سكيب"],
        description="⏭️ تخطي الأغنية الحالية"
    )
    async def skip(self, ctx: commands.Context):
        """تخطي الأغنية"""
        player = self._get_player(ctx.guild.id)
        if not player or not player.current:
            await ctx.send("❌ مفيش حاجة شغالة")
            return
        await player.skip()
        await ctx.send("⏭️ تم التخطي")

    # ═══════════════════════════════════════
    # ⏹️ !stop / /stop
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="stop",
        aliases=["ايقاف", "وقف"],
        description="⏹️ إيقاف التشغيل ومسح القائمة"
    )
    async def stop(self, ctx: commands.Context):
        """إيقاف التشغيل"""
        player = self._get_player(ctx.guild.id)
        if not player:
            await ctx.send("❌ البوت مش في روم صوتي")
            return
        await player.stop()
        await ctx.send("⏹️ تم الإيقاف")

    # ═══════════════════════════════════════
    # ⏸️ !pause / /pause
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="pause",
        aliases=["ايقاف-مؤقت"],
        description="⏸️ إيقاف مؤقت"
    )
    async def pause(self, ctx: commands.Context):
        """إيقاف مؤقت"""
        player = self._get_player(ctx.guild.id)
        if not player or not player.current:
            await ctx.send("❌ مفيش حاجة شغالة")
            return
        await player.pause()
        await ctx.send("⏸️ تم الإيقاف المؤقت")

    # ═══════════════════════════════════════
    # ▶️ !resume / /resume
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="resume",
        aliases=["استكمال", "كمل"],
        description="▶️ استكمال التشغيل"
    )
    async def resume(self, ctx: commands.Context):
        """استكمال التشغيل"""
        player = self._get_player(ctx.guild.id)
        if not player:
            await ctx.send("❌ مفيش حاجة موقوفة")
            return
        await player.resume()
        await ctx.send("▶️ تم الاستكمال")

    # ═══════════════════════════════════════
    # 📋 !queue / /queue
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="queue",
        aliases=["قائمة", "القائمة"],
        description="📋 عرض قائمة التشغيل"
    )
    async def queue_cmd(self, ctx: commands.Context):
        """عرض القائمة"""
        player = self._get_player(ctx.guild.id)
        if not player or (not player.current and not player.queue):
            await ctx.send("📭 القائمة فاضية")
            return

        desc = ""
        if player.current:
            desc += f"🎵 **الآن:** {player.current.title}\n\n"

        for i, track in enumerate(list(player.queue)[:10], 1):
            desc += f"`{i}.` {track.title}\n"

        embed = discord.Embed(title="🎶 قائمة التشغيل", description=desc, color=0x9B59B6)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎵 !nowplaying / /nowplaying
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="nowplaying",
        aliases=["الحالية", "الان"],
        description="🎵 عرض الأغنية الحالية"
    )
    async def nowplaying(self, ctx: commands.Context):
        """الأغنية الحالية"""
        player = self._get_player(ctx.guild.id)
        if not player or not player.current:
            await ctx.send("❌ مفيش حاجة شغالة")
            return
        track = player.current
        embed = discord.Embed(
            title="🎵 الأغنية الحالية",
            description=f"**{track.title}**\nبواسطة: {track.author}",
            color=0x1DB954
        )
        if track.artwork_url:
            embed.set_thumbnail(url=track.artwork_url)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔊 !volume / /volume
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="volume",
        aliases=["صوت", "الصوت"],
        description="🔊 تعديل مستوى الصوت (0-100)"
    )
    @app_commands.describe(volume="مستوى الصوت من 0 إلى 100")
    async def volume(self, ctx: commands.Context, volume: int = None):
        """تعديل الصوت"""
        player = self._get_player(ctx.guild.id)
        if not player:
            await ctx.send("❌ البوت مش في روم")
            return

        if volume is None:
            await ctx.send(f"🔊 مستوى الصوت الحالي: **{player.volume}%**")
            return

        if volume < 0 or volume > 100:
            await ctx.send("❌ الصوت من **0** لـ **100**")
            return

        await player.set_volume(volume)
        await ctx.send(f"🔊 الصوت: **{volume}%**")

    # ═══════════════════════════════════════
    # 🔀 !shuffle / /shuffle
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="shuffle",
        aliases=["خلط", "عشوائي"],
        description="🔀 خلط قائمة التشغيل"
    )
    async def shuffle(self, ctx: commands.Context):
        """خلط القائمة"""
        player = self._get_player(ctx.guild.id)
        if not player or len(player.queue) < 2:
            await ctx.send("❌ القائمة مش كفاية للخلط")
            return
        await player.shuffle()
        await ctx.send("🔀 تم خلط القائمة")

    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص بيانات: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات المدخلة!")
        else:
            print(f"❌ [Music] error: {error}")


async def setup(bot):
    await bot.add_cog(Music(bot))