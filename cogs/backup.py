import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import shutil
import zipfile
import io
from datetime import datetime
from config import Colors

BACKUP_DIR = "backups"
DATA_FILES = [
    "bitcoin.json",
    "levels.json",
    "games.json",
    "invites.json",
    "tickets.json",
    "welcome.json",
    "settings.json",
    "automation.json",
    "warnings.json",
    "commands_config.json"
]


class Backup(commands.Cog):
    """💾 نظام النسخ الاحتياطي"""

    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        self.last_backup_info = {}  # {guild_id: {name, size, time, sent}}
        self.daily_backup.start()

    def cog_unload(self):
        self.daily_backup.cancel()

    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for f in DATA_FILES:
                if os.path.exists(f):
                    zipf.write(f, f)
            # metadata
            meta = {
                "created_at": datetime.now().isoformat(),
                "bot_version": "2.0",
                "files": [f for f in DATA_FILES if os.path.exists(f)]
            }
            zipf.writestr("metadata.json", json.dumps(meta, ensure_ascii=False, indent=2))
        size = os.path.getsize(backup_path)
        # احتفظ بآخر 14 نسخة بس
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_")])
        while len(backups) > 14:
            old = backups.pop(0)
            try:
                os.remove(os.path.join(BACKUP_DIR, old))
            except:
                pass
        return backup_name, backup_path, size

    def restore_backup(self, zip_data):
        """استعادة نسخة"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zipf:
                # احتفظ بنسخة أمان
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_dir = os.path.join(BACKUP_DIR, f"safety_{timestamp}")
                os.makedirs(safety_dir, exist_ok=True)
                for f in DATA_FILES:
                    if os.path.exists(f):
                        shutil.copy(f, os.path.join(safety_dir, f))
                # استخرج
                files_restored = 0
                for name in zipf.namelist():
                    if name in DATA_FILES:
                        zipf.extract(name, ".")
                        files_restored += 1
                # اقرأ metadata
                info = {}
                if "metadata.json" in zipf.namelist():
                    info = json.loads(zipf.read("metadata.json").decode("utf-8"))
                return files_restored, info
        except Exception as e:
            raise Exception(f"فشل الاستعادة: {e}")

    # ═══════════════════════════════════════
    # 💾 backup
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="backup", aliases=["باكب", "نسخة_احتياطية"], description="💾 إنشاء نسخة احتياطية")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def backup(self, ctx: commands.Context):
        msg = await ctx.send("⏳ جاري إنشاء النسخة...")
        try:
            name, path, size = self.create_backup()
        except Exception as e:
            await msg.edit(content=f"❌ فشل النسخ: `{e}`")
            return
        size_kb = size / 1024
        embed = discord.Embed(
            title="✅ تم إنشاء النسخة",
            description=f"**الملف:** `{name}`\n**الحجم:** `{size_kb:.1f} KB`",
            color=Colors.SUCCESS
        )
        sent = False
        # ارسل للروم المحدد
        settings_data = {}
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings_data = json.load(f)
            except:
                pass
        gd = settings_data.get(str(ctx.guild.id), {})
        log_channel_id = gd.get("log_channel")
        if log_channel_id:
            ch = ctx.guild.get_channel(int(log_channel_id))
            if ch:
                try:
                    await ch.send(file=discord.File(path))
                    sent = True
                except:
                    pass
        if not sent:
            try:
                await ctx.send(file=discord.File(path))
                sent = True
            except:
                pass
        embed.set_footer(text=f"تم الإرسال: {'✅' if sent else 'محلي فقط'}")
        await msg.edit(content=None, embed=embed)

    # ═══════════════════════════════════════
    # 📺 backupchannel
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="backupchannel", aliases=["باكب_روم", "روم_النسخ"], description="📺 روم النسخ اليومي")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="الروم أو 'حذف'")
    async def backupchannel(self, ctx: commands.Context, channel: str):
        # نستخدم settings.json
        settings_data = {}
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings_data = json.load(f)
            except:
                pass
        gid = str(ctx.guild.id)
        settings_data.setdefault(gid, {})
        if channel.lower() in ["حذف", "الغاء"]:
            settings_data[gid]["log_channel"] = None
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=4)
            await ctx.send("✅ تم إلغاء روم النسخ")
            return
        ch = None
        if ctx.message.channel_mentions:
            ch = ctx.message.channel_mentions[0]
        elif channel.isdigit():
            ch = ctx.guild.get_channel(int(channel))
        if not ch or not isinstance(ch, discord.TextChannel):
            await ctx.send("❌ منشن روم كتابي أو `حذف`")
            return
        settings_data[gid]["log_channel"] = ch.id
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(settings_data, f, ensure_ascii=False, indent=4)
        await ctx.send(f"✅ روم النسخ: {ch.mention}")

    # ═══════════════════════════════════════
    # 🔁 backupdaily
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="backupdaily", aliases=["باكب_يومي", "نسخ_يومي"], description="🔁 تشغيل/إيقاف النسخ اليومي")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def backupdaily(self, ctx: commands.Context):
        settings_data = {}
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings_data = json.load(f)
            except:
                pass
        gid = str(ctx.guild.id)
        settings_data.setdefault(gid, {})
        current = settings_data[gid].get("backup_daily", False)
        settings_data[gid]["backup_daily"] = not current
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(settings_data, f, ensure_ascii=False, indent=4)
        if settings_data[gid]["backup_daily"]:
            await ctx.send("✅ تم تشغيل النسخ الاحتياطي اليومي 🟢")
        else:
            await ctx.send("❌ تم إيقاف النسخ الاحتياطي اليومي 🔴")

    # ═══════════════════════════════════════
    # 📊 backupstatus
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="backupstatus", aliases=["باكب_حالة", "حالة_النسخ"], description="📊 حالة النسخ")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def backupstatus(self, ctx: commands.Context):
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_")])
        total_size = sum(os.path.getsize(os.path.join(BACKUP_DIR, b)) for b in backups)
        last = backups[-1] if backups else "لا يوجد"
        last_size = 0
        if backups:
            last_size = os.path.getsize(os.path.join(BACKUP_DIR, backups[-1])) / 1024
        settings_data = {}
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings_data = json.load(f)
            except:
                pass
        gd = settings_data.get(str(ctx.guild.id), {})
        daily = gd.get("backup_daily", False)
        ch_id = gd.get("log_channel")
        embed = discord.Embed(title="💾 حالة النسخ الاحتياطي", color=Colors.SUCCESS if daily else Colors.WARNING)
        embed.add_field(name="🔁 النسخ اليومي", value="🟢 مفعل" if daily else "🔴 متوقف", inline=True)
        embed.add_field(name="📺 روم النسخ", value=f"<#{ch_id}>" if ch_id else "`غير محدد`", inline=True)
        embed.add_field(name="📦 عدد النسخ", value=f"{len(backups)} / 14", inline=True)
        embed.add_field(name="🕐 آخر نسخة", value=last, inline=False)
        embed.add_field(name="📊 الحجم الكلي", value=f"{total_size/1024:.1f} KB", inline=True)
        embed.add_field(name="📄 حجم آخر نسخة", value=f"{last_size:.1f} KB", inline=True)
        embed.set_footer(text="آخر 14 نسخة محفوظة محلياً")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ♻️ restore
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="restore", aliases=["استعادة", "استرجاع"], description="♻️ استعادة من نسخة")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def restore(self, ctx: commands.Context):
        attachment = None
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
        if not attachment or not attachment.filename.endswith(".zip"):
            await ctx.send("❌ أرفق ملف النسخة (`.zip`) مع الأمر!")
            return
        if attachment.size > 50 * 1024 * 1024:
            await ctx.send("❌ الملف كبير جداً (الحد 50 MB)!")
            return
        # تأكيد
        embed = discord.Embed(
            title="⚠️ تأكيد الاستعادة",
            description=f"**هيتم استبدال كل البيانات الحالية** بمحتوى الملف `{attachment.filename}`\n\nاكتب `تأكيد` خلال 30 ثانية.",
            color=Colors.WARNING
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.strip() == "تأكيد"

        try:
            await self.bot.wait_for("message", check=check, timeout=30)
        except:
            await ctx.send("⏰ انتهى الوقت — تم الإلغاء.")
            return
        try:
            async with ctx.typing():
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status != 200:
                            await ctx.send("❌ فشل تحميل الملف!")
                            return
                        data = await resp.read()
                files, info = self.restore_backup(data)
            embed = discord.Embed(
                title="✅ تمت الاستعادة",
                description=f"**الملفات:** `{files}`\n**التاريخ:** `{info.get('created_at', 'غير معروف')}`",
                color=Colors.SUCCESS
            )
            embed.set_footer(text="تم حفظ نسخة أمان قبل الاستعادة")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ فشل الاستعادة: `{e}`")

    # ═══════════════════════════════════════
    # 🔁 المهمة اليومية
    # ═══════════════════════════════════════
    @tasks.loop(hours=24)
    async def daily_backup(self):
        try:
            name, path, size = self.create_backup()
            print(f"✅ [Backup] نسخة يومية: {name} ({size/1024:.1f} KB)")
            # ارسل للرومات المفعّلة
            settings_data = {}
            if os.path.exists("settings.json"):
                try:
                    with open("settings.json", "r", encoding="utf-8") as f:
                        settings_data = json.load(f)
                except:
                    pass
            for gid, gd in settings_data.items():
                if not gd.get("backup_daily") or not gd.get("log_channel"):
                    continue
                guild = self.bot.get_guild(int(gid))
                if not guild:
                    continue
                ch = guild.get_channel(int(gd["log_channel"]))
                if not ch:
                    continue
                try:
                    await ch.send(
                        content="💾 **نسخة احتياطية يومية**",
                        file=discord.File(path)
                    )
                except:
                    pass
        except Exception as e:
            print(f"❌ [Backup] فشل النسخ اليومي: {e}")

    @daily_backup.before_loop
    async def before_daily(self):
        await self.bot.wait_until_ready()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي القناة!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Backup(bot))