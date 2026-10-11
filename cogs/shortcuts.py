import discord
from discord.ext import commands, tasks
import json
import os

# ═══════════════════════════════════════
# 📁 إعدادات
# ═══════════════════════════════════════
CONFIG_FILE = "commands_config.json"

# ⚠️ Flask API ملغي مؤقتاً (Railway مش بيدعم multi-port)
# BOT_API_PORT = int(os.getenv("PORT", 5001))
# BOT_API_SECRET = os.getenv("BOT_API_SECRET", "default_secret_123")


def load_config():
    """تحميل إعدادات الأوامر"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(data):
    """حفظ إعدادات الأوامر"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Shortcuts(commands.Cog):
    """نظام الأوامر بدون بادئة"""

    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.shortcuts_map = {}
        
        # تحميل الاختصارات
        self.reload_shortcuts()
        
        # بدء الـ auto-reload loop
        self.auto_reload.start()

    def cog_unload(self):
        """إيقاف الـ loop عند إغلاق الـ Cog"""
        try:
            self.auto_reload.cancel()
        except:
            pass

    # ═══════════════════════════════════════
    # 🔄 إعادة تحميل الاختصارات
    # ═══════════════════════════════════════
    def reload_shortcuts(self):
        """إعادة تحميل الاختصارات من الملف"""
        self.config = load_config()
        self.shortcuts_map = {}

        for command_name, data in self.config.items():
            if not data.get("enabled", True):
                continue
            shortcut = data.get("shortcut", "").strip()
            if shortcut:
                self.shortcuts_map[shortcut.lower()] = command_name

        print(f"✅ تم تحميل {len(self.shortcuts_map)} اختصار")

    @tasks.loop(seconds=60)
    async def auto_reload(self):
        """إعادة تحميل دورية كل 60 ثانية"""
        try:
            self.reload_shortcuts()
        except Exception as e:
            print(f"⚠️ خطأ في auto-reload: {e}")

    @auto_reload.before_loop
    async def before_auto_reload(self):
        """انتظر لحد ما البوت يجهز"""
        await self.bot.wait_until_ready()

    # ═══════════════════════════════════════
    # 📨 معالجة الرسائل
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message):
        """مراقبة الرسائل للأوامر بدون بادئة"""

        # تجاهل رسائل البوتات
        if message.author.bot:
            return

        # تجاهل الرسائل الخاصة
        if not message.guild:
            return

        # تجاهل الرسائل الفاضية
        content = message.content.strip()
        if not content:
            return

        # تجاهل لو بتبدأ بـ prefix عادي
        if content.startswith(("!", "/", ".", ",", "؟")):
            return

        # تقسيم الرسالة
        words = content.split()
        if not words:
            return

        # أول كلمة
        first_word = words[0].lower()

        # لو مش اختصار
        if first_word not in self.shortcuts_map:
            return

        # الأمر الأصلي
        command_name = self.shortcuts_map[first_word]

        # باقي الرسالة
        args_text = " ".join(words[1:]) if len(words) > 1 else ""

        # ندوّر على الأمر
        command = self.bot.get_command(command_name)

        if command is None:
            print(f"⚠️ الأمر {command_name} مش موجود")
            return

        # ننفذ الأمر
        try:
            ctx = await self.bot.get_context(message)
            if args_text:
                await command.__call__(ctx, args_text)
            else:
                await command.__call__(ctx)
        except Exception as e:
            print(f"⚠️ خطأ في تنفيذ {command_name}: {e}")
            import traceback
            traceback.print_exc()

    # ═══════════════════════════════════════
    # 🛠️ أوامر إدارة الاختصارات
    # ═══════════════════════════════════════
    @commands.command(name="اختصارات", aliases=["shortcuts"])
    @commands.has_permissions(administrator=True)
    async def list_shortcuts(self, ctx):
        """عرض قائمة الاختصارات"""
        if not self.shortcuts_map:
            return await ctx.send("📭 مفيش اختصارات مسجلة حالياً")

        desc = ""
        for shortcut, command in list(self.shortcuts_map.items())[:30]:
            desc += f"`{shortcut}` → `/{command}`\n"

        embed = discord.Embed(
            title="📋 الاختصارات المسجلة",
            description=desc,
            color=0x9B59B6
        )
        embed.set_footer(text=f"إجمالي: {len(self.shortcuts_map)} اختصار")
        await ctx.send(embed=embed)

    @commands.command(name="حدث_الاختصارات", aliases=["reload-shortcuts"])
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx):
        """إعادة تحميل الاختصارات"""
        self.reload_shortcuts()
        await ctx.send(f"✅ تم إعادة تحميل {len(self.shortcuts_map)} اختصار")


async def setup(bot):
    await bot.add_cog(Shortcuts(bot))