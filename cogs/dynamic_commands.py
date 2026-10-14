import discord
from discord.ext import commands, tasks
import json
import os

CONFIG_FILE = "commands_config.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


class DynamicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.auto_reload.start()
        print(f"✅ [Dynamic] تم تحميل {len(self.config)} إعداد أمر")

    def cog_unload(self):
        try:
            self.auto_reload.cancel()
        except:
            pass

    def load_config(self):
        self.config = load_config()
        return self.config

    def is_enabled(self, command_name: str) -> bool:
        cmd = self.config.get(command_name, {})
        return cmd.get("enabled", True)

    def reload_now(self) -> int:
        self.load_config()
        enabled_count = sum(
            1 for k, v in self.config.items()
            if v.get("enabled", True)
        )
        print(f"🔄 [Dynamic] Reload — {enabled_count} أمر مفعّل")
        return enabled_count

    @tasks.loop(seconds=30)
    async def auto_reload(self):
        try:
            old_config = self.config.copy()
            self.load_config()
            if old_config != self.config:
                print("🔄 [Dynamic] تم اكتشاف تعديلات")
        except Exception as e:
            print(f"⚠️ auto-reload error: {e}")

    @auto_reload.before_loop
    async def before_auto_reload(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if ctx.command.name in ["اختصارات", "reload-shortcuts", "تحديث-اختصارات"]:
            return
        cmd_name = ctx.command.qualified_name
        if not self.is_enabled(cmd_name):
            await ctx.send(f"❌ الأمر `{ctx.command.name}` معطّل!", delete_after=8)
            raise commands.CheckFailure()


async def setup(bot):
    await bot.add_cog(DynamicCommands(bot))