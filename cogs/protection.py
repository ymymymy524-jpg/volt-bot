import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from config import Colors

# ==========================================
# 🛡️ نظام الحماية (Protection) - Prefix + Slash
# ==========================================

class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.protection_file = "data/protection.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        if not os.path.exists("data"):
            os.makedirs("data")

    def _load_protection(self):
        if os.path.exists(self.protection_file):
            with open(self.protection_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_protection(self, data):
        with open(self.protection_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_guild_settings(self, guild_id):
        data = self._load_protection()
        if str(guild_id) not in data:
            data[str(guild_id)] = {
                "auto": {"enabled": False},
                "spam": {"enabled": False, "limit": 5, "seconds": 3},
                "link": {"enabled": False, "type": "all"},
                "join": {"enabled": False, "min_age": 7},
                "hacked": {"enabled": False},
                "bans": {"enabled": False},
                "kicks": {"enabled": False},
                "channels": {"enabled": False},
                "roles": {"enabled": False},
                "bots": {"enabled": False, "action": "kick"}
            }
            self._save_protection(data)
        return data[str(guild_id)]

    def _toggle_status(self, guild_id, key, **extra):
        data = self._load_protection()
        if guild_id not in data:
            data[guild_id] = {}
        data[guild_id][key] = {"enabled": extra.pop("enabled"), **extra}
        self._save_protection(data)

    def _parse_status(self, status: str):
        status_lower = status.lower().strip()
        if status_lower in ("on", "enable", "true", "1", "تفعيل", "شغل", "فعل"):
            return True
        if status_lower in ("off", "disable", "false", "0", "تعطيل", "اقفل", "اطفي"):
            return False
        return None

    # ═══════════════════════════════════════
    # 🛡️ !protection / /protection (Group)
    # ═══════════════════════════════════════
    @commands.hybrid_group(
        name="protection",
        aliases=["protect", "حماية", "بروتكشن"],
        description="🛡️ أوامر حماية السيرفر",
        invoke_without_command=True
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def protection(self, ctx: commands.Context):
        """عرض المساعدة لأوامر الحماية"""
        embed = discord.Embed(
            title="🛡️ أوامر الحماية",
            description=(
                "**Slash:**\n"
                "`/protection auto on/off` - الحماية التلقائية\n"
                "`/protection spam on/off [limit] [seconds]` - حماية السبام\n"
                "`/protection link on/off [type]` - حماية الروابط\n"
                "`/protection join on/off [min_age]` - حماية الانضمام\n"
                "`/protection hacked on/off` - حماية المخترقة\n"
                "`/protection bans on/off` - حماية الحظر الجماعي\n"
                "`/protection kicks on/off` - حماية الطرد الجماعي\n"
                "`/protection channels on/off` - حماية القنوات\n"
                "`/protection roles on/off` - حماية الرتب\n"
                "`/protection bots on/off [action]` - حماية البوتات\n"
                "`/protection status` - عرض حالة الحماية\n\n"
                "**Prefix:** نفس الأوامر بـ `!protection`"
            ),
            color=Colors.INFO
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🤖 auto
    # ═══════════════════════════════════════
    @protection.command(name="auto", aliases=["تلقائي"], description="🤖 تفعيل/تعطيل الحماية التلقائية")
    @app_commands.describe(status="on للتفعيل أو off للتعطيل")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="تعطيل ❌", value="off")
    ])
    async def protection_auto(self, ctx: commands.Context, status: str):
        """تفعيل/تعطيل الحماية التلقائية"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` للتفعيل أو `off` للتعطيل")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "auto", enabled=enabled)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="🤖 الحماية التلقائية",
            description=f"تم {status_text} الحماية التلقائية الشاملة",
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🚫 spam
    # ═══════════════════════════════════════
    @protection.command(name="spam", aliases=["سبام"], description="🚫 حماية من السبام")
    @app_commands.describe(status="on/off", limit="الحد الأقصى للرسائل", seconds="الفترة الزمنية بالثواني")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="تعطيل ❌", value="off")
    ])
    async def protection_spam(self, ctx: commands.Context, status: str, limit: int = 5, seconds: int = 3):
        """حماية السبام"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        if limit < 1 or seconds < 1:
            await ctx.send("❌ الحد والفترة لازم يكونوا أكبر من 0")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "spam", enabled=enabled, limit=limit, seconds=seconds)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="🚫 حماية السبام",
            description=(
                f"حماية السبام: {status_text}\n\n**الإعدادات:**\n"
                f"• الحد الأقصى: `{limit}` رسائل\n"
                f"• الفترة الزمنية: `{seconds}` ثواني"
            ),
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔗 link
    # ═══════════════════════════════════════
    @protection.command(name="link", aliases=["links", "روابط"], description="🔗 حماية من الروابط")
    @app_commands.describe(status="on/off", link_type="نوع الروابط")
    @app_commands.choices(
        status=[
            app_commands.Choice(name="تفعيل ✅", value="on"),
            app_commands.Choice(name="تعطيل ❌", value="off")
        ],
        link_type=[
            app_commands.Choice(name="جميع الروابط", value="all"),
            app_commands.Choice(name="روابط الديسكورد فقط", value="discord"),
            app_commands.Choice(name="الروابط الخارجية فقط", value="external")
        ]
    )
    async def protection_link(self, ctx: commands.Context, status: str, link_type: str = "all"):
        """حماية الروابط"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        valid_types = ["all", "discord", "external"]
        if link_type not in valid_types:
            await ctx.send("❌ نوع الروابط لازم يكون `all` أو `discord` أو `external`")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "link", enabled=enabled, type=link_type)

        type_text = {
            "all": "جميع الروابط",
            "discord": "روابط الديسكورد فقط",
            "external": "الروابط الخارجية فقط"
        }.get(link_type, link_type)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="🔗 حماية الروابط",
            description=f"حماية الروابط: {status_text}\n\n**النوع:** {type_text}",
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🚪 join
    # ═══════════════════════════════════════
    @protection.command(name="join", aliases=["انضمام"], description="🚪 حماية من الحسابات الجديدة")
    @app_commands.describe(status="on/off", min_age="الحد الأدنى لعمر الحساب بالأيام")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="تعطيل ❌", value="off")
    ])
    async def protection_join(self, ctx: commands.Context, status: str, min_age: int = 7):
        """حماية الانضمام"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        if min_age < 0:
            await ctx.send("❌ الحد الأدنى لعمر الحساب لازم يكون 0 أو أكثر")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "join", enabled=enabled, min_age=min_age)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="🚪 حماية الانضمام",
            description=f"حماية الحسابات الجديدة: {status_text}\n\n**الحد الأدنى:** `{min_age}` يوم",
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔐 hacked
    # ═══════════════════════════════════════
    @protection.command(name="hacked", aliases=["مخترقة"], description="🔐 حماية من الحسابات المخترقة")
    @app_commands.describe(status="on/off")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="تعطيل ❌", value="off")
    ])
    async def protection_hacked(self, ctx: commands.Context, status: str):
        """حماية المخترقة"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "hacked", enabled=enabled)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="🔐 حماية الحسابات المخترقة",
            description=(
                f"حماية الحسابات المخترقة: {status_text}\n\n"
                "• كشف السلوك المشبوه\n"
                "• إرسال رسائل جماعية\n"
                "• تغييرات سريعة في البروفايل"
            ),
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔨 bans
    # ═══════════════════════════════════════
    @protection.command(name="bans", aliases=["حظر-جماعي"], description="🔨 حماية من الحظر الجماعي")
    @app_commands.describe(status="on/off")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="تعطيل ❌", value="off")
    ])
    async def protection_bans(self, ctx: commands.Context, status: str):
        """حماية الحظر الجماعي"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "bans", enabled=enabled)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="🔨 حماية الحظر الجماعي",
            description=(
                f"حماية الحظر الجماعي: {status_text}\n\n"
                "• كشف محاولات الحظر الجماعي\n"
                "• تقييد صلاحيات الحظر تلقائياً\n"
                "• إرسال تنبيهات للإدارة"
            ),
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👢 kicks
    # ═══════════════════════════════════════
    @protection.command(name="kicks", aliases=["طرد-جماعي"], description="👢 حماية من الطرد الجماعي")
    @app_commands.describe(status="on/off")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="تعطيل ❌", value="off")
    ])
    async def protection_kicks(self, ctx: commands.Context, status: str):
        """حماية الطرد الجماعي"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "kicks", enabled=enabled)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="👢 حماية الطرد الجماعي",
            description=(
                f"حماية الطرد الجماعي: {status_text}\n\n"
                "• كشف محاولات الطرد الجماعي\n"
                "• تقييد صلاحيات الطرد تلقائياً\n"
                "• إرسال تنبيهات للإدارة"
            ),
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📺 channels
    # ═══════════════════════════════════════
    @protection.command(name="channels", aliases=["قنوات"], description="📺 حماية من حذف/إنشاء القنوات")
    @app_commands.describe(status="on/off")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="تعطيل ❌", value="off")
    ])
    async def protection_channels(self, ctx: commands.Context, status: str):
        """حماية القنوات"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "channels", enabled=enabled)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="📺 حماية القنوات",
            description=(
                f"حماية القنوات: {status_text}\n\n"
                "• منع حذف القنوات الجماعي\n"
                "• منع إنشاء قنوات عشوائية\n"
                "• تقييد صلاحيات إدارة القنوات"
            ),
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎭 roles
    # ═══════════════════════════════════════
    @protection.command(name="roles", aliases=["رتب"], description="🎭 حماية من تعديل الرتب")
    @app_commands.describe(status="on/off")
    @app_commands.choices(status=[
        app_commands.Choice(name="تفعيل ✅", value="on"),
        app_commands.Choice(name="تعطيل ❌", value="off")
    ])
    async def protection_roles(self, ctx: commands.Context, status: str):
        """حماية الرتب"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "roles", enabled=enabled)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="🎭 حماية الرتب",
            description=(
                f"حماية الرتب: {status_text}\n\n"
                "• منع حذف الرتب الجماعي\n"
                "• منع تعديل صلاحيات الرتب\n"
                "• تقييد صلاحيات إدارة الرتب"
            ),
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🤖 bots
    # ═══════════════════════════════════════
    @protection.command(name="bots", aliases=["بوتات"], description="🤖 حماية من إضافة البوتات")
    @app_commands.describe(status="on/off", action="الإجراء عند إضافة بوت")
    @app_commands.choices(
        status=[
            app_commands.Choice(name="تفعيل ✅", value="on"),
            app_commands.Choice(name="تعطيل ❌", value="off")
        ],
        action=[
            app_commands.Choice(name="طرد البوت", value="kick"),
            app_commands.Choice(name="حظر البوت", value="ban"),
            app_commands.Choice(name="تنبيه فقط", value="notify")
        ]
    )
    async def protection_bots(self, ctx: commands.Context, status: str, action: str = "kick"):
        """حماية البوتات"""
        enabled = self._parse_status(status)
        if enabled is None:
            await ctx.send("❌ اكتب `on` أو `off`")
            return

        valid_actions = ["kick", "ban", "notify"]
        if action not in valid_actions:
            await ctx.send("❌ الإجراء لازم يكون `kick` أو `ban` أو `notify`")
            return

        guild_id = str(ctx.guild.id)
        self._toggle_status(guild_id, "bots", enabled=enabled, action=action)

        action_text = {
            "kick": "طرد البوت",
            "ban": "حظر البوت",
            "notify": "إرسال تنبيه فقط"
        }.get(action, action)

        status_text = "✅ مفعّلة" if enabled else "❌ معطّلة"
        embed = discord.Embed(
            title="🤖 حماية البوتات",
            description=f"حماية البوتات: {status_text}\n\n**الإجراء:** {action_text}",
            color=Colors.SUCCESS if enabled else Colors.ERROR
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📊 status
    # ═══════════════════════════════════════
    @protection.command(name="status", aliases=["حالة", "عرض"], description="📊 عرض حالة جميع أنظمة الحماية")
    async def protection_status(self, ctx: commands.Context):
        """عرض حالة الحماية"""
        settings = self._get_guild_settings(ctx.guild.id)

        embed = discord.Embed(
            title="🛡️ حالة أنظمة الحماية",
            description="نظرة عامة على جميع أنظمة الحماية المفعّلة",
            color=Colors.INFO
        )

        status_list = []
        for key, value in settings.items():
            if isinstance(value, dict) and "enabled" in value:
                enabled = "✅" if value["enabled"] else "❌"
                name_map = {
                    "auto": "🤖 الحماية التلقائية",
                    "spam": "🚫 حماية السبام",
                    "link": "🔗 حماية الروابط",
                    "join": "🚪 حماية الانضمام",
                    "hacked": "🔐 حماية الحسابات المخترقة",
                    "bans": "🔨 حماية الحظر الجماعي",
                    "kicks": "👢 حماية الطرد الجماعي",
                    "channels": "📺 حماية القنوات",
                    "roles": "🎭 حماية الرتب",
                    "bots": "🤖 حماية البوتات"
                }
                name = name_map.get(key, key)
                status_list.append(f"{enabled} **{name}**")

        embed.description += "\n\n" + "\n".join(status_list) if status_list else "لا توجد إعدادات"

        if settings.get("spam", {}).get("enabled"):
            embed.add_field(
                name="🚫 تفاصيل حماية السبام",
                value=f"الحد: `{settings['spam']['limit']}` رسائل / `{settings['spam']['seconds']}` ثواني",
                inline=False
            )

        if settings.get("join", {}).get("enabled"):
            embed.add_field(
                name="🚪 تفاصيل حماية الانضمام",
                value=f"الحد الأدنى لعمر الحساب: `{settings['join']['min_age']}` يوم",
                inline=False
            )

        embed.set_footer(text=f"طلب بواسطة: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك صلاحية **Administrator**!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"❌ ناقص بيانات: `{error.param.name}`\n"
                "استخدم `/protection` أو `!protection` لعرض المساعدة",
                delete_after=10
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات المدخلة!", delete_after=8)
        else:
            print(f"❌ خطأ في أمر {ctx.command}: {error}")


async def setup(bot):
    await bot.add_cog(Protection(bot))