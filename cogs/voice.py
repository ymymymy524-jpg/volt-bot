import discord
from discord.ext import commands
from discord import app_commands
from config import Colors


class Voice(commands.Cog):
    """🎙️ أوامر الصوت"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════
    # 🎧 join
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="join", aliases=["ادخل", "تعال"], description="🎧 البوت يدخل الروم الصوتي")
    @commands.has_permissions(move_members=True)
    @app_commands.default_permissions(move_members=True)
    @app_commands.describe(channel="الروم الصوتي (اختياري)")
    async def join(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        if not channel:
            if not ctx.author.voice:
                await ctx.send("❌ لازم تكون في روم صوتي، أو حدد روم!")
                return
            channel = ctx.author.voice.channel
        if ctx.voice_client:
            if ctx.voice_client.channel.id == channel.id:
                await ctx.send(f"✅ أنا موجود في {channel.mention} بالفعل")
                return
            await ctx.voice_client.move_to(channel)
        else:
            try:
                await channel.connect(self_deaf=True)
            except Exception as e:
                await ctx.send(f"❌ ما قدرت أدخل: `{e}`")
                return
        embed = discord.Embed(
            title="🎧 دخلت الروم",
            description=f"**{channel.name}**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👋 leave
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="leave", aliases=["اطلع", "اخرج", "غادر"], description="👋 البوت يطلع من الروم")
    @commands.has_permissions(move_members=True)
    @app_commands.default_permissions(move_members=True)
    async def leave(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send("❌ أنا مش في روم صوتي!")
            return
        channel_name = ctx.voice_client.channel.name
        await ctx.voice_client.disconnect()
        embed = discord.Embed(
            title="👋 طلعت من الروم",
            description=f"**{channel_name}**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎙️ voicename
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="voicename", aliases=["روم_اسم", "اسم_رومي"], description="🎙️ تغيير اسم رومك الصوتي")
    @app_commands.describe(name="الاسم الجديد")
    async def voicename(self, ctx: commands.Context, *, name: str):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي!")
            return
        channel = ctx.author.voice.channel
        # التحقق: هل الروم يبدو مؤقت؟ (اسم يبدأ بـ "🔊" أو فيه اسم العضو)
        if channel.name.lower() not in [ctx.author.name.lower(), ctx.author.display_name.lower()]:
            # مش روم مؤقت — نتأكد
            pass
        if len(name) > 90:
            name = name[:90]
        try:
            await channel.edit(name=name)
            await ctx.send(f"✅ تم تغيير اسم رومك إلى **{name}**")
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أغير الاسم: `{e}`")

    # ═══════════════════════════════════════
    # 🔢 voicelimit
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="voicelimit", aliases=["روم_حد", "حد_رومي"], description="🔢 تحديد عدد الأعضاء")
    @app_commands.describe(limit="العدد (0 بدون حد)")
    async def voicelimit(self, ctx: commands.Context, limit: int):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي!")
            return
        if limit < 0 or limit > 99:
            await ctx.send("❌ الحد من 0 لـ 99!")
            return
        channel = ctx.author.voice.channel
        try:
            await channel.edit(user_limit=limit)
            msg = f"✅ الحد الأقصى الآن **{limit}** عضو" if limit else "✅ تم إلغاء الحد"
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أعدل: `{e}`")

    # ═══════════════════════════════════════
    # 🔒 voicelock
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="voicelock", aliases=["روم_قفل", "اقفل_رومي"], description="🔒 قفل رومك الصوتي")
    async def voicelock(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي!")
            return
        channel = ctx.author.voice.channel
        try:
            await channel.set_permissions(ctx.guild.default_role, connect=False)
            embed = discord.Embed(
                title="🔒 تم القفل",
                description=f"**{channel.name}** مقفول الآن",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أقفل: `{e}`")

    # ═══════════════════════════════════════
    # 🔓 voiceunlock
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="voiceunlock", aliases=["روم_فتح", "افتح_رومي"], description="🔓 فتح رومك الصوتي")
    async def voiceunlock(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي!")
            return
        channel = ctx.author.voice.channel
        try:
            await channel.set_permissions(ctx.guild.default_role, connect=None)
            embed = discord.Embed(
                title="🔓 تم الفتح",
                description=f"**{channel.name}** مفتوح الآن",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أفتح: `{e}`")

    # ═══════════════════════════════════════
    # ⚠️ معالجة الأخطاء
    # ═══════════════════════════════════════
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي الروم!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Voice(bot))