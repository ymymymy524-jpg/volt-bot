import discord
from discord.ext import commands
import json
import os

# مسار ملف الإعدادات
CONFIG_FILE = "commands_config.json"


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
        # قاموس عكسي: الاختصار -> الأمر الأصلي
        self.shortcuts_map = {}
        self.reload_shortcuts()

    def reload_shortcuts(self):
        """إعادة تحميل الاختصارات من الملف"""
        self.config = load_config()
        self.shortcuts_map = {}
        
        for command_name, data in self.config.items():
            if not data.get("enabled", True):
                continue
            
            shortcut = data.get("shortcut", "").strip()
            if shortcut:
                # نحوّل الاختصار لحروف صغيرة للمقارنة
                self.shortcuts_map[shortcut.lower()] = command_name
        
        print(f"✅ تم تحميل {len(self.shortcuts_map)} اختصار")

    @commands.Cog.listener()
    async def on_message(self, message):
        """مراقبة الرسائل للأوامر بدون بادئة"""
        
        # تجاهل رسائل البوتات
        if message.author.bot:
            return
        
        # تجاهل الرسائل الخاصة (DM)
        if not message.guild:
            return
        
        # تجاهل الرسائل الفاضية
        content = message.content.strip()
        if not content:
            return
        
        # تجاهل لو الرسالة بتبدأ بـ prefix عادي (عشان مايتعارضش)
        if content.startswith(("!", "/", ".", ",", "؟")):
            return
        
        # تقسيم الرسالة لكلمات
        words = content.split()
        if not words:
            return
        
        # أول كلمة في الرسالة
        first_word = words[0].lower()
        
        # لو أول كلمة مش اختصار مسجل، تجاهل
        if first_word not in self.shortcuts_map:
            return
        
        # الأمر الأصلي
        command_name = self.shortcuts_map[first_word]
        
        # باقي الرسالة (المعاملات)
        args = words[1:]
        
        # نبني الأمر النصي
        fake_message_content = f"!{command_name}"
        if args:
            fake_message_content += " " + " ".join(args)
        
        # ننفذ الأمر
        try:
            # نعمل نسخة من الرسالة بمحتوى جديد
            message.content = fake_message_content
            await self.bot.process_commands(message)
        except Exception as e:
            print(f"⚠️ خطأ في تنفيذ الأمر {command_name}: {e}")

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

    @commands.command(name="اضف_اختصار", aliases=["add-shortcut"])
    @commands.has_permissions(administrator=True)
    async def add_shortcut(self, ctx, shortcut: str, command: str):
        """إضافة اختصار جديد: !اضف_اختصار شغل play"""
        if command not in self.config:
            self.config[command] = {}
        
        self.config[command]["shortcut"] = shortcut
        self.config[command]["enabled"] = True
        save_config(self.config)
        self.reload_shortcuts()
        
        await ctx.send(f"✅ تم إضافة الاختصار: `{shortcut}` → `/{command}`")

    @commands.command(name="احذف_اختصار", aliases=["remove-shortcut"])
    @commands.has_permissions(administrator=True)
    async def remove_shortcut(self, ctx, shortcut: str):
        """حذف اختصار"""
        if shortcut.lower() not in self.shortcuts_map:
            return await ctx.send(f"❌ الاختصار `{shortcut}` مش موجود")
        
        command = self.shortcuts_map[shortcut.lower()]
        if command in self.config:
            self.config[command]["shortcut"] = ""
            save_config(self.config)
            self.reload_shortcuts()
        
        await ctx.send(f"✅ تم حذف الاختصار: `{shortcut}`")

    @commands.command(name="حدث_الاختصارات", aliases=["reload-shortcuts"])
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx):
        """إعادة تحميل الاختصارات من الملف"""
        self.reload_shortcuts()
        await ctx.send(f"✅ تم إعادة تحميل {len(self.shortcuts_map)} اختصار")


async def setup(bot):
    await bot.add_cog(Shortcuts(bot))