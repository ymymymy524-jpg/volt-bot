import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import unicodedata
import traceback

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


def normalize_text(text: str) -> str:
    if not text:
        return text
    text = unicodedata.normalize('NFC', text)
    return text.strip().lower()


class Shortcuts(commands.Cog):
    """نظام الأوامر بدون بادئة + API"""

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
            shortcut = data.get("shortcut", "").strip()
            if shortcut:
                key = normalize_text(shortcut)
                self.shortcuts_map[key] = command_name

        print(f"✅ [Shortcuts] تم تحميل {len(self.shortcuts_map)} اختصار")
        return len(self.shortcuts_map)

    @tasks.loop(seconds=60)
    async def auto_reload(self):
        try:
            self.reload_shortcuts()
        except Exception as e:
            print(f"⚠️ auto-reload error: {e}")

    @auto_reload.before_loop
    async def before_auto_reload(self):
        await self.bot.wait_until_ready()

    # ═══════════════════════════════════════
    # 🎯 API
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
            if cmd != command_name and normalize_text(data.get("shortcut", "")) == normalize_text(shortcut):
                raise ValueError(f"الاختصار `{shortcut}` مستخدم مع `/{cmd}`")

        self.config[command_name] = {"enabled": enabled, "shortcut": shortcut}
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
            key = normalize_text(shortcut)
            if key in shortcuts_seen:
                raise ValueError(f"الاختصار `{shortcut}` مستخدم مرتين")
            shortcuts_seen[key] = cmd

        self.config = shortcuts_dict
        save_config(self.config)
        count = self.reload_shortcuts()
        print(f"✅ [API] تم تحديث {count} اختصار")
        
        # ⭐ reload للـ DynamicCommands
        dynamic = self.bot.get_cog("DynamicCommands")
        if dynamic:
            dynamic.reload_now()
            print("🔄 [Shortcuts] تم تحديث DynamicCommands")
        
        return count

    def delete_shortcut(self, command_name: str):
        if command_name in self.config:
            del self.config[command_name]
            save_config(self.config)
            self.reload_shortcuts()
            return True
        return False

    # ═══════════════════════════════════════
    # 📨 on_message
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        if not content:
            return

        # تجاهل prefix
        if content.startswith(("!", "/", ".", ",")):
            return

        words = content.split()
        if not words:
            return

        first_word = words[0]
        key = normalize_text(first_word)

        if key not in self.shortcuts_map:
            return

        command_name = self.shortcuts_map[key]
        args = words[1:] if len(words) > 1 else []

        print(f"🔍 [Shortcuts] '{key}' → '{command_name}' | args = {args}")

        try:
            ctx = await self.bot.get_context(message)

            # ⭐ بناء الأمر من الأجزاء (يدعم subcommands)
            command = None
            parts = command_name.split()

            # 1️⃣ لو الأمر بسيط (كلمة واحدة)
            if len(parts) == 1:
                command = self.bot.get_command(parts[0])

            # 2️⃣ لو الأمر مركّب (warn add, badmin set...)
            else:
                # جرّب get_command بالكامل الأول
                command = self.bot.get_command(command_name)

                # لو مش موجود، دور على subcommand
                if command is None:
                    parent = self.bot.get_command(parts[0])
                    if parent:
                        for i in range(1, len(parts)):
                            if hasattr(parent, 'all_commands'):
                                sub = parent.all_commands.get(parts[i])
                                if sub:
                                    parent = sub
                                    command = parent
                                else:
                                    break

            # 3️⃣ لو لسه مش موجود، دوّر في كل الأوامر
            if command is None:
                for cmd in self.bot.walk_commands():
                    if cmd.name == command_name or command_name in cmd.aliases:
                        command = cmd
                        break
                    if cmd.qualified_name == command_name:
                        command = cmd
                        break

            if command is None:
                print(f"❌ الأمر {command_name} مش موجود")
                await message.channel.send(
                    f"❌ الأمر `{command_name}` مش موجود!",
                    delete_after=8
                )
                return

            # ⭐ لو الأمر من subcommand، محتاج نبعت الـ subcommand كـ arg
            if " " in command_name and command.parent:
                sub_name = command.name
                if sub_name not in args:
                    args = [sub_name] + args

            # ⚡ نستخدم invoke
            await ctx.invoke(command, *args)

        except commands.MissingRequiredArgument as e:
            await message.channel.send(f"❌ ناقص بيانات: `{e.param.name}`", delete_after=8)
        except commands.MemberNotFound:
            await message.channel.send("❌ مش لاقي العضو ده!", delete_after=8)
        except commands.RoleNotFound:
            await message.channel.send("❌ مش لاقي الرتبة دي!", delete_after=8)
        except commands.ChannelNotFound:
            await message.channel.send("❌ مش لاقي القناة دي!", delete_after=8)
        except commands.BadArgument:
            await message.channel.send("❌ تأكد من البيانات!", delete_after=8)
        except commands.MissingPermissions:
            await message.channel.send("❌ مفيش عندك الصلاحيات!", delete_after=8)
        except commands.BotMissingPermissions:
            await message.channel.send("❌ البوت مفيش عنده الصلاحيات!", delete_after=8)
        except commands.CheckFailure:
            # أمر معطّل — DynamicCommands بيعرض الرسالة
            pass
        except Exception as e:
            print(f"⚠️ خطأ في {command_name}: {e}")
            traceback.print_exc()

    # ═══════════════════════════════════════
    # 🛠️ أوامر إدارة الاختصارات
    # ═══════════════════════════════════════
    @commands.command(name="اختصارات", aliases=["shortcuts"])
    @commands.has_permissions(administrator=True)
    async def list_shortcuts(self, ctx: commands.Context):
        if not self.shortcuts_map:
            await ctx.send("📭 مفيش اختصارات")
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