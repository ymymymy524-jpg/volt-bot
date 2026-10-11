import discord
from discord.ext import commands, tasks
import json
import os

# ═══════════════════════════════════════
# 📁 إعدادات
# ═══════════════════════════════════════
CONFIG_FILE = "commands_config.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Shortcuts(commands.Cog):
    """نظام الأوامر بدون بادئة + API للتحديث الفوري"""

    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.shortcuts_map = {}
        self.reload_shortcuts()
        self.auto_reload.start()

    def cog_unload(self):
        try:
            self.auto_reload.cancel()
        except:
            pass

    # ═══════════════════════════════════════
    # 🔄 Reload
    # ═══════════════════════════════════════
    def reload_shortcuts(self):
        self.config = load_config()
        self.shortcuts_map = {}

        for command_name, data in self.config.items():
            if not data.get("enabled", True):
                continue
            shortcut = data.get("shortcut", "").strip().lower()
            if shortcut:
                self.shortcuts_map[shortcut] = command_name

        print(f"✅ [Shortcuts] تم تحميل {len(self.shortcuts_map)} اختصار")
        return len(self.shortcuts_map)

    @tasks.loop(seconds=60)
    async def auto_reload(self):
        try:
            self.reload_shortcuts()
        except Exception as e:
            print(f"⚠️ خطأ في auto-reload: {e}")

    @auto_reload.before_loop
    async def before_auto_reload(self):
        await self.bot.wait_until_ready()

    # ═══════════════════════════════════════
    # 🎯 دوال للـ API
    # ═══════════════════════════════════════
    def get_all_shortcuts(self):
        return {
            "shortcuts": self.config,
            "map": self.shortcuts_map,
            "count": len(self.shortcuts_map)
        }

    def update_shortcut(self, command_name: str, shortcut: str, enabled: bool = True):
        shortcut = shortcut.strip().lower()

        for cmd, data in self.config.items():
            if cmd != command_name and data.get("shortcut", "").lower() == shortcut:
                raise ValueError(f"الاختصار `{shortcut}` مستخدم بالفعل مع `/{cmd}`")

        self.config[command_name] = {
            "enabled": enabled,
            "shortcut": shortcut
        }
        save_config(self.config)
        self.reload_shortcuts()
        return True

    def bulk_update(self, shortcuts_dict: dict):
        shortcuts_seen = {}
        for cmd, data in shortcuts_dict.items():
            if not data.get("enabled", True):
                continue
            shortcut = data.get("shortcut", "").strip().lower()
            if not shortcut:
                continue
            if shortcut in shortcuts_seen:
                raise ValueError(
                    f"الاختصار `{shortcut}` مستخدم مرتين: `/{shortcuts_seen[shortcut]}` و `/{cmd}`"
                )
            shortcuts_seen[shortcut] = cmd

        self.config = shortcuts_dict
        save_config(self.config)
        count = self.reload_shortcuts()
        print(f"✅ [API] تم تحديث {count} اختصار دفعة واحدة")
        return count

    def delete_shortcut(self, command_name: str):
        if command_name in self.config:
            del self.config[command_name]
            save_config(self.config)
            self.reload_shortcuts()
            return True
        return False

    # ═══════════════════════════════════════
    # 📨 معالجة الرسائل — المسؤول الوحيد عن process_commands
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        if not content:
            return

        # لو الرسالة بتبدأ بـ prefix → معالجة عادية (process_commands)
        if content.startswith(("!", "/", ".", ",")):
            await self.bot.process_commands(message)
            return

        # لو اختصار
        words = content.split()
        first_word = words[0].lower()

        if first_word in self.shortcuts_map:
            command_name = self.shortcuts_map[first_word]
            args_text = " ".join(words[1:]) if len(words) > 1 else ""

            command = self._find_command(command_name)
            if command is None:
                print(f"⚠️ الأمر {command_name} مش موجود")
                return

            try:
                ctx = await self.bot.get_context(message)
                if args_text:
                    await command.__call__(ctx, args_text)
                else:
                    await command.__call__(ctx)
            except Exception as e:
                print(f"⚠️ خطأ في تنفيذ {command_name}: {e}")

    def _find_command(self, command_name: str):
        command = self.bot.get_command(command_name)
        if command:
            return command

        if " " in command_name:
            parts = command_name.split()
            parent = self.bot.get_command(parts[0])
            if parent and hasattr(parent, 'all_commands'):
                return parent.all_commands.get(parts[-1])
        return None

    # ═══════════════════════════════════════
    # 🛠️ أوامر إدارة الاختصارات (Discord)
    # ═══════════════════════════════════════
    @commands.command(name="اختصارات", aliases=["shortcuts"])
    @commands.has_permissions(administrator=True)
    async def list_shortcuts(self, ctx: commands.Context):
        if not self.shortcuts_map:
            await ctx.send("📭 مفيش اختصارات مسجلة")
            return

        shortcuts = list(self.shortcuts_map.items())
        chunks = [shortcuts[i:i + 25] for i in range(0, len(shortcuts), 25)]

        for page_num, chunk in enumerate(chunks, 1):
            desc = "\n".join(f"`{s}` → `/{c}`" for s, c in chunk)
            embed = discord.Embed(
                title=f"📋 الاختصارات ({page_num}/{len(chunks)})",
                description=desc,
                color=0x9B59B6
            )
            embed.set_footer(text=f"إجمالي: {len(shortcuts)}")
            await ctx.send(embed=embed)

    @commands.command(name="تحديث-اختصارات", aliases=["reload-shortcuts"])
    @commands.has_permissions(administrator=True)
    async def reload_cmd(self, ctx: commands.Context):
        count = self.reload_shortcuts()
        await ctx.send(f"✅ تم إعادة تحميل **{count}** اختصار")


async def setup(bot):
    await bot.add_cog(Shortcuts(bot))