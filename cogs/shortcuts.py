import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import unicodedata

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


def normalize_arabic(text: str) -> str:
    """تطبيع النص العربي (NFC + إزالة التشكيل)"""
    if not text:
        return text
    # NFC normalization
    text = unicodedata.normalize('NFC', text)
    return text.strip().lower()


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

        # 1️⃣ من commands_config.json (اللي بتيجي من الـ Dashboard)
        for command_name, data in self.config.items():
            if not data.get("enabled", True):
                continue
            shortcut = data.get("shortcut", "").strip()
            if shortcut:
                key = normalize_arabic(shortcut)
                self.shortcuts_map[key] = command_name

        # 2️⃣ من aliases بتاعت الأوامر نفسها (في الكود)
        try:
            for cmd in self.bot.walk_commands():
                cmd_name = cmd.name
                if " " not in cmd_name:
                    self.shortcuts_map.setdefault(normalize_arabic(cmd_name), cmd_name)
                for alias in cmd.aliases:
                    if alias:
                        self.shortcuts_map.setdefault(normalize_arabic(alias), cmd_name)
        except Exception as e:
            print(f"⚠️ [Shortcuts] فشل تحميل aliases: {e}")

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
        await asyncio.sleep(3)
        self.reload_shortcuts()

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
        shortcut = shortcut.strip()
        for cmd, data in self.config.items():
            if cmd != command_name and normalize_arabic(data.get("shortcut", "")) == normalize_arabic(shortcut):
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
            shortcut = data.get("shortcut", "").strip()
            if not shortcut:
                continue
            key = normalize_arabic(shortcut)
            if key in shortcuts_seen:
                raise ValueError(
                    f"الاختصار `{shortcut}` مستخدم مرتين: `/{shortcuts_seen[key]}` و `/{cmd}`"
                )
            shortcuts_seen[key] = cmd

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
    # 📨 معالجة الرسائل
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        if not content:
            return

        # لو الرسالة بتبدأ بـ prefix → نسيبها لـ bot.py
        if content.startswith(("!", "/", ".", ",")):
            return

        words = content.split()
        first_word = words[0]

        # 🔍 تشخيص
        print(f"🔍 [DEBUG] أول كلمة = '{first_word}'")
        print(f"🔍 [DEBUG] repr = {repr(first_word)}")
        print(f"🔍 [DEBUG] normalized = '{normalize_arabic(first_word)}'")
        print(f"🔍 [DEBUG] in map? {normalize_arabic(first_word) in self.shortcuts_map}")

        # لو اختصار
        key = normalize_arabic(first_word)
        if key in self.shortcuts_map:
            command_name = self.shortcuts_map[key]
            args_text = " ".join(words[1:]) if len(words) > 1 else ""

            print(f"🔍 [DEBUG] الأمر = {command_name}")

            command = self._find_command(command_name)
            if command is None:
                print(f"❌ الأمر {command_name} مش موجود")
                return

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
    # 🔍 _find_command
    # ═══════════════════════════════════════
    def _find_command(self, command_name: str):
        # 1️⃣ get_command مباشرة
        command = self.bot.get_command(command_name)
        if command:
            return command

        # 2️⃣ alias
        for cmd in self.bot.walk_commands():
            if cmd.name == command_name:
                return cmd
            for alias in cmd.aliases:
                if alias == command_name:
                    return cmd

        # 3️⃣ sub-commands
        if " " in command_name:
            parts = command_name.split()
            parent = self.bot.get_command(parts[0])
            if parent and hasattr(parent, 'all_commands'):
                return parent.all_commands.get(parts[-1])

        return None

    # ═══════════════════════════════════════
    # 🛠️ أوامر إدارة الاختصارات
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
            desc = "\n".join(f"`{s}` → `{c}`" for s, c in chunk)
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