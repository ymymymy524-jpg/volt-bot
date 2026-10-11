import discord
from discord.ext import commands
import json
import os

# مسار ملف التخزين
WELCOME_FILE = "welcome.json"


# دالة لتحميل البيانات من ملف JSON
def load_data():
    if os.path.exists(WELCOME_FILE):
        try:
            with open(WELCOME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


# دالة لحفظ البيانات في ملف JSON
def save_data(data):
    with open(WELCOME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    # ═══════════════════════════════════════
    # 🔧 دوال مساعدة
    # ═══════════════════════════════════════
    def get_guild_data(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "welcome_channel": None,
                "goodbye_channel": None,
                "enabled": True
            }
        return self.data[guild_id]

    def save(self):
        save_data(self.data)

    def create_welcome_embed(self, member: discord.Member):
        embed = discord.Embed(
            title="🎉 عضو جديد انضم للسيرفر!",
            description=(
                f"أهلاً وسهلاً بيك يا {member.mention} في سيرفر **{member.guild.name}**!\n\n"
                f"👤 **الاسم:** {member.display_name}\n"
                f"🆔 **الآيدي:** `{member.id}`\n"
                f"📅 **تاريخ إنشاء الحساب:** <t:{int(member.created_at.timestamp())}:R>\n"
                f"👥 **عدد الأعضاء:** {member.guild.member_count}"
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"العضو رقم {member.guild.member_count} في السيرفر")
        return embed

    def create_goodbye_embed(self, member: discord.Member):
        embed = discord.Embed(
            title="👋 عضو غادر السيرفر",
            description=(
                f"مع السلامة يا **{member.display_name}**!\n\n"
                f"🆔 **الآيدي:** `{member.id}`\n"
                f"👥 **عدد الأعضاء الحالي:** {member.guild.member_count}"
            ),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="نتمنى لك التوفيق في مكان آخر")
        return embed

    # ═══════════════════════════════════════
    # 🔔 Events
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        guild_id = str(member.guild.id)
        guild_data = self.get_guild_data(guild_id)

        if not guild_data.get("enabled", True):
            return

        welcome_channel_id = guild_data.get("welcome_channel")
        if not welcome_channel_id:
            return

        channel = member.guild.get_channel(int(welcome_channel_id))
        if not channel:
            return

        try:
            embed = self.create_welcome_embed(member)
            await channel.send(
                content=f"🎊 **{member.mention}** انضم للسيرفر! ياريت تقرأ القوانين وتتمتع معانا!",
                embed=embed
            )
        except discord.HTTPException as e:
            print(f"❌ خطأ في إرسال رسالة الترحيب: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        guild_data = self.get_guild_data(guild_id)

        if not guild_data.get("enabled", True):
            return

        goodbye_channel_id = guild_data.get("goodbye_channel")
        if not goodbye_channel_id:
            return

        channel = member.guild.get_channel(int(goodbye_channel_id))
        if not channel:
            return

        try:
            embed = self.create_goodbye_embed(member)
            await channel.send(embed=embed)
        except discord.HTTPException as e:
            print(f"❌ خطأ في إرسال رسالة الوداع: {e}")

    # ═══════════════════════════════════════
    # 📨 أوامر الترحيب (Prefix)
    # ═══════════════════════════════════════
    @commands.command(
        name="setwelcome",
        aliases=["sw", "عين-ترحيب"],
        description="👋 تعيين روم الترحيب"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def setwelcome(self, ctx: commands.Context, channel: discord.TextChannel):
        """تعيين روم الترحيب"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["welcome_channel"] = channel.id
        self.save()

        embed = discord.Embed(
            title="✅ تم تعيين روم الترحيب",
            description=f"تم تعيين روم الترحيب إلى {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="setgoodbye",
        aliases=["sg", "عين-وداع"],
        description="👋 تعيين روم الوداع"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def setgoodbye(self, ctx: commands.Context, channel: discord.TextChannel):
        """تعيين روم الوداع"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["goodbye_channel"] = channel.id
        self.save()

        embed = discord.Embed(
            title="✅ تم تعيين روم الوداع",
            description=f"تم تعيين روم الوداع إلى {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="testwelcome",
        aliases=["tw", "تجربة-ترحيب"],
        description="🧪 اختبار رسالة الترحيب"
    )
    @commands.has_permissions(administrator=True)
    async def testwelcome(self, ctx: commands.Context):
        """اختبار رسالة الترحيب"""
        guild_data = self.get_guild_data(ctx.guild.id)
        welcome_channel_id = guild_data.get("welcome_channel")

        if not welcome_channel_id:
            await ctx.send("❌ لم يتم تعيين روم الترحيب! استخدم `!setwelcome` أولاً")
            return

        channel = ctx.guild.get_channel(int(welcome_channel_id))
        if not channel:
            await ctx.send("❌ روم الترحيب المحدد محذوف أو غير موجود")
            return

        try:
            embed = self.create_welcome_embed(ctx.author)
            await channel.send(
                content="🧪 **هذه رسالة تجريبية للترحيب!**",
                embed=embed
            )
            success_embed = discord.Embed(
                title="✅ تم إرسال الرسالة التجريبية",
                description=f"تم إرسال رسالة ترحيب تجريبية إلى {channel.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=success_embed)
        except discord.Forbidden:
            await ctx.send("❌ البوت مفيش عنده صلاحية إرسال رسائل في الروم ده")
        except discord.HTTPException as e:
            await ctx.send(f"❌ حدث خطأ أثناء إرسال الرسالة: {e}")

    @commands.command(
        name="welcome-set-status",
        aliases=["wss", "تشغيل-ترحيب"],
        description="🔄 تفعيل أو إيقاف نظام الترحيب"
    )
    @commands.has_permissions(administrator=True)
    async def welcome_set_status(self, ctx: commands.Context, status: str = None):
        """تفعيل أو إيقاف نظام الترحيب"""
        if not status or status.lower() not in ["on", "off", "تفعيل", "ايقاف"]:
            await ctx.send(
                "❌ اكتب `on` للتفعيل أو `off` للإيقاف\n"
                "**مثال:** `!welcome-set-status on`",
                delete_after=10
            )
            return

        guild_data = self.get_guild_data(ctx.guild.id)
        is_enabled = status.lower() in ["on", "تفعيل"]
        guild_data["enabled"] = is_enabled
        self.save()

        status_text = "مفعّل ✅" if is_enabled else "موقّف ❌"
        embed = discord.Embed(
            title="🔄 تم تحديث حالة الترحيب",
            description=f"نظام الترحيب الآن: **{status_text}**",
            color=discord.Color.green() if is_enabled else discord.Color.red()
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ⚠️ معالجة الأخطاء
    # ═══════════════════════════════════════
    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك صلاحية **Administrator**!", delete_after=8)
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي القناة دي!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص بيانات: `{error.param.name}`", delete_after=8)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات المدخلة!", delete_after=8)
        else:
            print(f"❌ خطأ في أمر {ctx.command}: {error}")


async def setup(bot):
    await bot.add_cog(Welcome(bot))