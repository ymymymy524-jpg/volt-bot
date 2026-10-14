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
    "cogs.fun",
    "cogs.utility",
    "cogs.voice",
    "cogs.admin",
    "cogs.automation",
    "cogs.backup",
    "cogs.shortcuts",
    "cogs.dynamic_commands",
    "cogs.broadcast",
]


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
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
                import traceback
                traceback.print_exc()

        print("")
        await asyncio.sleep(2)

        print(f"📊 عدد الأوامر: {len(list(self.commands))}")

        # مزامنة Global
        try:
            synced_global = await self.tree.sync()
            print(f"✅ تم مزامنة {len(synced_global)} أمر عالمياً")
        except Exception as e:
            print(f"⚠️ فشل المزامنة العالمية: {e}")
            import traceback
            traceback.print_exc()

        # مزامنة Guild
        if config.TEST_GUILD_ID:
            try:
                guild = discord.Object(id=config.TEST_GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                synced_guild = await self.tree.sync(guild=guild)
                print(f"✅ تم مزامنة {len(synced_guild)} أمر مع السيرفر: {config.TEST_GUILD_ID}")
            except Exception as e:
                print(f"⚠️ فشل مزامنة السيرفر: {e}")
                import traceback
                traceback.print_exc()

    async def on_ready(self):
        print("=" * 60)
        print(f"🤖 البوت شغال: {self.user}")
        print(f"🆔 الآيدي: {self.user.id}")
        print(f"📡 متصل بـ {len(self.guilds)} سيرفر")
        print(f"👥 المستخدمين: {sum(g.member_count or 0 for g in self.guilds)}")
        print("=" * 60)

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="!help | /help"
            )
        )


async def on_command_error_handler(bot, ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ معندكش الصلاحيات الكافية!")
        return
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ البوت معندوش الصلاحيات الكافية!")
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ ناقص بيانات: `{error.param.name}`")
        return
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ مش لاقي العضو ده!")
        return
    if isinstance(error, commands.ChannelNotFound):
        await ctx.send("❌ مش لاقي القناة دي!")
        return
    if isinstance(error, commands.RoleNotFound):
        await ctx.send("❌ مش لاقي الرتبة دي!")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ تأكد من البيانات المدخلة!")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏱️ استنى {error.retry_after:.1f} ثانية!")
        return
    print(f"❌ خطأ في الأمر {ctx.command}: {error}")
    import traceback
    traceback.print_exc()


async def main():
    bot = MyBot()

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx, error):
        await on_command_error_handler(bot, ctx, error)

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