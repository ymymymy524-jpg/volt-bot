import os
import sys
import discord
from discord.ext import commands
from config import TOKEN, TEST_GUILD_ID

# تعريف النوايا (Intents) المطلوبة للبوت للعمل بشكل كامل
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",  # بادئة غير مستخدمة فعلياً لأننا نستخدم Slash Commands فقط، لكنها مطلوبة للتهيئة
            intents=intents,
            help_command=None  # تعطيل أمر المساعدة الافتراضي لاستخدام نظام المساعدة المخصص
        )

    async def setup_hook(self):
        """دالة يتم استدعاؤها عند بدء تشغيل البوت لتحميل الـ Cogs ومزامنة الأوامر"""
        # قائمة الـ Cogs المراد تحميلها (13 ملف كما هو مطلوب)
        cogs_list = [
            "cogs.general",
            "cogs.moderation",
            "cogs.levels",
            "cogs.welcome",
            "cogs.protection",
            "cogs.music",
            "cogs.invites",
            "cogs.tickets",
            "cogs.games",
            "cogs.economy",
            "cogs.ai",
            "cogs.settings",
            "cogs.help"
        ]

        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ تم تحميل الـ Cog بنجاح: {cog}")
            except Exception as e:
                print(f"❌ فشل في تحميل الـ Cog: {cog} | الخطأ: {e}")

        # مزامنة شجرة الأوامر مع سيرفر الاختبار (لتسريع تحديث الأوامر أثناء التطوير)
        if TEST_GUILD_ID:
            guild = discord.Object(id=TEST_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ تم مزامنة الأوامر مع سيرفر الاختبار (ID: {TEST_GUILD_ID})")
        else:
            await self.tree.sync()
            print("✅ تم مزامنة الأوامر عالمياً (Global Sync)")

    async def on_ready(self):
        """دالة يتم استدعاؤها عندما يكون البوت متصلاً وجاهزاً للعمل"""
        print("=" * 60)
        print(f"✅ تم تسجيل الدخول بنجاح كـ: {self.user.name}#{self.user.discriminator}")
        print(f"🆔 معرف البوت (ID): {self.user.id}")
        print(f"🌐 البوت متصل حالياً بـ {len(self.guilds)} سيرفر")
        print("=" * 60)

# إنشاء نسخة من البوت
bot = MyBot()

# تشغيل البوت باستخدام التوكن الموجود في ملف config
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ فشل تسجيل الدخول: تأكد من صحة التوكن في ملف config.py أو .env")
    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع أثناء التشغيل: {e}")