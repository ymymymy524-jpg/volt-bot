import discord
from discord.ext import commands
import config
import asyncio
import os

from api.server import run_api

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
        print("📦 جاري تحميل الـ Cogs...")
        for ext in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(ext)
                print(f"  ✅ {ext}")
            except Exception as e:
                print(f"  ❌ {ext}: {e}")

        print("")

        # مزامنة الأوامر
        try:
            if config.TEST_GUILD_ID:
                guild = discord.Object(id=config.TEST_GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"✅ تم مزامنة الأوامر مع السيرفر: {config.TEST_GUILD_ID}")
            else:
                await self.tree.sync()
                print("✅ تم مزامنة الأوامر عالمياً")
        except Exception as e:
            print(f"⚠️ فشل مزامنة الأوامر: {e}")

    async def on_ready(self):
        """لما البوت يشتغل"""
        print("=" * 60)
        print(f"🤖 البوت شغال: {self.user}")
        print(f"🆔 الآيدي: {self.user.id}")
        print(f"📡 متصل بـ {len(self.guilds)} سيرفر")
        print(f"👥 المستخدمين: {sum(g.member_count or 0 for g in self.guilds)}")
        print("=" * 60)

        # حالة البوت
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="!help | /help"
            )
        )


# ═══════════════════════════════════════
# ⚠️ معالج الأخطاء العام
# ═══════════════════════════════════════
async def on_command_error_handler(bot, ctx, error):
    """معالج أخطاء موحد"""
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ معندكش الصلاحيات الكافية!", delete_after=8)
        return

    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ البوت معندوش الصلاحيات الكافية!", delete_after=8)
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ ناقص بيانات: `{error.param.name}`", delete_after=8)
        return

    if isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ مش لاقي العضو ده!", delete_after=8)
        return

    if isinstance(error, commands.ChannelNotFound):
        await ctx.send("❌ مش لاقي القناة دي!", delete_after=8)
        return

    if isinstance(error, commands.RoleNotFound):
        await ctx.send("❌ مش لاقي الرتبة دي!", delete_after=8)
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ تأكد من البيانات المدخلة!", delete_after=8)
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏱️ استنى {error.retry_after:.1f} ثانية!", delete_after=5)
        return

    print(f"❌ خطأ في الأمر {ctx.command}: {error}")
    import traceback
    traceback.print_exc()


# ═══════════════════════════════════════
# 🎬 Main
# ═══════════════════════════════════════
async def main():
    bot = MyBot()
    
    # ربط معالج الأخطاء
    bot.on_command_error = lambda ctx, error: on_command_error_handler(bot, ctx, error)
    
    # معالج رسائل موحد للاختصارات
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        await bot.process_commands(message)
    
    # شغل البوت والـ API مع بعض
    API_PORT = int(os.getenv("PORT", 8080))
    
    try:
        async with bot:
            await asyncio.gather(
                bot.start(config.TOKEN),
                run_api(bot, port=API_PORT)
            )
    except discord.LoginFailure:
        print("❌ فشل تسجيل الدخول: تأكد من التوكن في .env")
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف البوت")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف البوت")