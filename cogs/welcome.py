import discord
from discord import app_commands
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

    # دالة لجلب بيانات السيرفر (وإنشائها لو مش موجودة)
    def get_guild_data(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "welcome_channel": None,
                "goodbye_channel": None,
                "enabled": True
            }
        return self.data[guild_id]

    # دالة مساعدة لحفظ البيانات
    def save(self):
        save_data(self.data)

    # دالة لإنشاء Embed الترحيب
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

    # دالة لإنشاء Embed الوداع
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

    # حدث انضمام عضو للسيرفر
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

    # حدث مغادرة عضو للسيرفر
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

    # أمر /setwelcome لتحديد روم الترحيب
    @app_commands.command(name="setwelcome", description="تحديد روم الترحيب في السيرفر")
    @app_commands.describe(channel="الروم اللي عايز ترسل فيه رسالة الترحيب")
    @app_commands.checks.has_permissions(administrator=True)
    async def setwelcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["welcome_channel"] = channel.id
        self.save()

        embed = discord.Embed(
            title="✅ تم تعيين روم الترحيب",
            description=f"تم تعيين روم الترحيب إلى {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /setgoodbye لتحديد روم الوداع
    @app_commands.command(name="setgoodbye", description="تحديد روم الوداع في السيرفر")
    @app_commands.describe(channel="الروم اللي عايز ترسل فيه رسالة الوداع")
    @app_commands.checks.has_permissions(administrator=True)
    async def setgoodbye(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["goodbye_channel"] = channel.id
        self.save()

        embed = discord.Embed(
            title="✅ تم تعيين روم الوداع",
            description=f"تم تعيين روم الوداع إلى {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /testwelcome لتجربة رسالة الترحيب
    @app_commands.command(name="testwelcome", description="تجربة رسالة الترحيب")
    @app_commands.checks.has_permissions(administrator=True)
    async def testwelcome(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild_data = self.get_guild_data(interaction.guild.id)
        welcome_channel_id = guild_data.get("welcome_channel")

        if not welcome_channel_id:
            embed = discord.Embed(
                title="❌ لم يتم تعيين روم الترحيب",
                description="استخدم `/setwelcome` أولاً لتحديد روم الترحيب",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        channel = interaction.guild.get_channel(int(welcome_channel_id))
        if not channel:
            embed = discord.Embed(
                title="❌ الروم غير موجود",
                description="روم الترحيب المحدد محذوف أو غير موجود",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            embed = self.create_welcome_embed(interaction.user)
            await channel.send(
                content="🧪 **هذه رسالة تجريبية للترحيب!**",
                embed=embed
            )
            success_embed = discord.Embed(
                title="✅ تم إرسال الرسالة التجريبية",
                description=f"تم إرسال رسالة ترحيب تجريبية إلى {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ لا توجد صلاحيات",
                description="البوت مفيش عنده صلاحية إرسال رسائل في الروم ده",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except discord.HTTPException as e:
            error_embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء إرسال الرسالة: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    # أمر /welcome-set-status لتفعيل/إيقاف الترحيب
    @app_commands.command(name="welcome-set-status", description="تفعيل أو إيقاف نظام الترحيب")
    @app_commands.describe(status="الحالة الجديدة (on/off)")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="إيقاف ❌", value="off")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_set_status(self, interaction: discord.Interaction, status: app_commands.Choice[str]):
        guild_data = self.get_guild_data(interaction.guild.id)
        
        is_enabled = status.value == "on"
        guild_data["enabled"] = is_enabled
        self.save()

        status_text = "مفعّل ✅" if is_enabled else "موقّف ❌"
        embed = discord.Embed(
            title="🔄 تم تحديث حالة الترحيب",
            description=f"نظام الترحيب الآن: **{status_text}**",
            color=discord.Color.green() if is_enabled else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    # معالجة أخطاء الصلاحيات للأوامر الإدارية
    @setwelcome.error
    @setgoodbye.error
    @testwelcome.error
    @welcome_set_status.error
    async def on_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ مفيش عندك صلاحية Administrator!"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

# دالة تحميل الـ Cog للبوت
async def setup(bot):
    await bot.add_cog(Welcome(bot))