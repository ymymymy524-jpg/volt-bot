import discord
from discord.ext import commands
import config

# ═══════════════════════════════════════
# ⚙️ Intents
# ═══════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True

# ═══════════════════════════════════════
# 📋 الـ Cogs
# ═══════════════════════════════════════
INITIAL_EXTENSIONS = [
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
    "cogs.help",
    "cogs.shortcuts",   # ← الأوامر بدون بادئة
]


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",  # ← مهم للأوامر النصية
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        """تحميل الـ Cogs + مزامنة الأوامر"""
        for ext in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(ext)
                print(f"✅ تم تحميل: {ext}")
            except Exception as e:
                print(f"❌ فشل تحميل {ext}: {e}")

        # مزامنة الأوامر
        if config.TEST_GUILD_ID:
            guild = discord.Object(id=config.TEST_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ تم مزامنة الأوامر مع السيرفر: {config.TEST_GUILD_ID}")
        else:
            await self.tree.sync()
            print("✅ تم مزامنة الأوامر عالمياً")

    async def on_ready(self):
        """لما البوت يشتغل"""
        print("=" * 60)
        print(f"🤖 البوت شغال: {self.user}")
        print(f"🆔 الآيدي: {self.user.id}")
        print(f"📡 متصل بـ {len(self.guilds)} سيرفر")
        print("=" * 60)
        
        # حالة البوت
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="/help"
            )
        )


# ═══════════════════════════════════════
# 🚀 تشغيل البوت
# ═══════════════════════════════════════
if __name__ == "__main__":
    bot = MyBot()
    try:
        bot.run(config.TOKEN)
    except discord.LoginFailure:
        print("❌ فشل تسجيل الدخول: تأكد من التوكن في .env")
    except Exception as e:
        print(f"❌ خطأ: {e}")