import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import aiohttp

SETTINGS_FILE = "settings.json"


def load_data():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_data(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_guild_data(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "auto_messages": [],
                "auto_replies": [],
                "automod_rules": [],
                "autorole": None,
                "level_up_msg": None,
                "log_channel": None,
                "disabled_commands": [],
                "self_roles": [],
                "premium_end": None
            }
        return self.data[guild_id]

    def save(self):
        save_data(self.data)

    # ═══════════════════════════════════════
    # 🚀 !setup / /setup
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="setup",
        aliases=["اعداد", "تهيئة"],
        description="🚀 إعداد البوت في السيرفر (تفاعلي)"
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def setup_wizard(self, ctx: commands.Context):
        """إعداد تفاعلي للبوت"""
        embed = discord.Embed(
            title="🚀 معالج إعداد Volt System",
            description=(
                "**مرحباً بك في معالج الإعداد!**\n\n"
                "هيتم إعداد البوت على **4 مراحل**:\n\n"
                "🛡️ **المرحلة 1:** تفعيل الحماية الأساسية\n"
                "🎭 **المرحلة 2:** تعيين الرتبة التلقائية\n"
                "👋 **المرحلة 3:** تحديد روم الترحيب\n"
                "📋 **المرحلة 4:** تحديد روم اللوجات\n\n"
                "اضغط **ابدأ** للبدء."
            ),
            color=0x8b5cf6
        )
        await ctx.send(embed=embed, view=SetupStartView(self))

    async def do_setup_protection(self, interaction: discord.Interaction):
        """تفعيل الحماية الأساسية"""
        try:
            protection_cog = self.bot.get_cog("Protection")
            if not protection_cog:
                return await interaction.response.edit_message(
                    content="❌ cog الحماية غير محمّل", embed=None, view=None
                )

            # شكل البيانات الصح
            protection_cog._toggle_status(str(interaction.guild.id), "auto", enabled=True)
            protection_cog._toggle_status(str(interaction.guild.id), "spam", enabled=True, limit=5, seconds=3)
            protection_cog._toggle_status(str(interaction.guild.id), "link", enabled=True, type="all")
            protection_cog._toggle_status(str(interaction.guild.id), "join", enabled=True, min_age=7)
            protection_cog._toggle_status(str(interaction.guild.id), "hacked", enabled=True)
            protection_cog._toggle_status(str(interaction.guild.id), "bans", enabled=True)
            protection_cog._toggle_status(str(interaction.guild.id), "kicks", enabled=True)
            protection_cog._toggle_status(str(interaction.guild.id), "channels", enabled=True)
            protection_cog._toggle_status(str(interaction.guild.id), "roles", enabled=True)
            protection_cog._toggle_status(str(interaction.guild.id), "bots", enabled=True, action="kick")

            embed = discord.Embed(
                title="✅ المرحلة 1/4 — تم تفعيل الحماية",
                description=(
                    "تم تفعيل الأنظمة دي:\n\n"
                    "🛡️ **Antilink** — منع الروابط\n"
                    "🚫 **Antispam** — منع السبام\n"
                    "🚪 **Anti-join** — طرد الحسابات الجديدة\n"
                    "💀 **Anti-hacked** — حماية الحسابات المخترقة\n"
                    "🔨 **Anti-bans** — حماية من الحظر\n"
                    "👢 **Anti-kicks** — حماية من الطرد\n"
                    "📢 **Anti-channels** — حماية الرومات\n"
                    "🎭 **Anti-roles** — حماية الرتب\n"
                    "🤖 **Anti-bots** — طرد البوتات\n\n"
                    "**المرحلة الجاية:** اختار الرتبة التلقائية 👇"
                ),
                color=0x2ECC71
            )
            await interaction.response.edit_message(embed=embed, view=SetupAutoroleView(self))
        except Exception as e:
            await interaction.response.edit_message(
                content=f"❌ خطأ: {e}", embed=None, view=None
            )

    async def do_setup_autorole(self, interaction: discord.Interaction, role: discord.Role):
        """تعيين الرتبة التلقائية"""
        try:
            guild_data = self.get_guild_data(interaction.guild.id)
            guild_data["autorole"] = role.id
            self.save()

            embed = discord.Embed(
                title="✅ المرحلة 2/4 — تم تعيين الرتبة التلقائية",
                description=f"الرتبة: {role.mention}\n\n**المرحلة الجاية:** اختار روم الترحيب 👇",
                color=0x2ECC71
            )
            await interaction.response.edit_message(embed=embed, view=SetupWelcomeView(self))
        except Exception as e:
            await interaction.response.edit_message(
                content=f"❌ خطأ: {e}", embed=None, view=None
            )

    async def do_setup_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """تعيين روم الترحيب"""
        try:
            welcome_cog = self.bot.get_cog("Welcome")
            if welcome_cog:
                data = welcome_cog.get_guild_data(interaction.guild.id)
                data["welcome_channel"] = channel.id
                data["goodbye_channel"] = channel.id
                welcome_cog.save()

            embed = discord.Embed(
                title="✅ المرحلة 3/4 — تم تعيين روم الترحيب",
                description=f"الروم: {channel.mention}\n\n**المرحلة الجاية:** اختار روم اللوجات 👇",
                color=0x2ECC71
            )
            await interaction.response.edit_message(embed=embed, view=SetupLogView(self))
        except Exception as e:
            await interaction.response.edit_message(
                content=f"❌ خطأ: {e}", embed=None, view=None
            )

    async def do_setup_log(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """تعيين روم اللوجات"""
        try:
            guild_data = self.get_guild_data(interaction.guild.id)
            guild_data["log_channel"] = channel.id
            self.save()

            embed = discord.Embed(
                title="🎉 اكتمل الإعداد!",
                description=(
                    "**تم إعداد البوت بنجاح** ✅\n\n"
                    "🛡️ الحماية: **مفعّلة**\n"
                    "🎭 الرتبة التلقائية: **تم تعيينها**\n"
                    "👋 روم الترحيب: **تم تعيينه**\n"
                    "📋 روم اللوجات: **تم تعيينه**\n\n"
                    "**ابدأ استخدام البوت بـ `/help` أو `!help`** 🚀"
                ),
                color=0x2ECC71
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await interaction.response.edit_message(
                content=f"❌ خطأ: {e}", embed=None, view=None
            )

    # ═══════════════════════════════════════
    # 🎨 !add-emoji / /add-emoji
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="add-emoji",
        aliases=["ae", "اضف-ايموجي"],
        description="🎨 إضافة إيموجي للسيرفر"
    )
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @app_commands.default_permissions(manage_emojis=True)
    @app_commands.describe(name="اسم الإيموجي", url="رابط الصورة")
    async def add_emoji(self, ctx: commands.Context, name: str, url: str):
        """إضافة إيموجي"""
        if ctx.interaction:
            await ctx.defer()
        else:
            msg = await ctx.send("⏳ جاري إضافة الإيموجي...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await ctx.send("❌ رابط غير صالح")
                        return
                    image_bytes = await resp.read()
            emoji = await ctx.guild.create_custom_emoji(name=name, image=image_bytes)
            embed = discord.Embed(
                title="✅ تم إضافة الإيموجي",
                description=f"تم إضافة {emoji} بنجاح!",
                color=0x2ECC71
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")

    # ═══════════════════════════════════════
    # 📨 !auto-message / /auto-message (Group)
    # ═══════════════════════════════════════
    @commands.hybrid_group(
        name="auto-message",
        aliases=["am", "رسالة-تلقائية"],
        description="📨 إدارة الرسائل التلقائية",
        invoke_without_command=True
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def auto_message(self, ctx: commands.Context):
        """عرض المساعدة"""
        embed = discord.Embed(
            title="📨 أوامر الرسائل التلقائية",
            description=(
                "**Slash:**\n"
                "`/auto-message add #روم 60 الرسالة` - إضافة\n"
                "`/auto-message delete 1` - حذف بالرقم\n"
                "`/auto-message list` - عرض الكل\n\n"
                "**Prefix:**\n"
                "`!auto-message add #روم 60 الرسالة`"
            ),
            color=0x3498DB
        )
        await ctx.send(embed=embed)

    @auto_message.command(name="add", aliases=["+", "اضف"], description="إضافة رسالة تلقائية")
    @app_commands.describe(channel="الروم", interval="الفاصل الزمني بالثواني (60-86400)", message="الرسالة")
    async def auto_message_add(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        interval: int,
        *,
        message: str
    ):
        """إضافة رسالة تلقائية"""
        if interval < 60 or interval > 86400:
            await ctx.send("❌ الفاصل الزمني لازم يكون بين **60** و **86400** ثانية!")
            return

        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["auto_messages"].append({
            "channel_id": channel.id,
            "message": message,
            "interval": interval
        })
        self.save()
        await ctx.send(f"✅ تم إضافة رسالة تلقائية في {channel.mention} كل {interval} ثانية")

    @auto_message.command(name="delete", aliases=["del", "احذف"], description="حذف رسالة تلقائية")
    @app_commands.describe(index="رقم الرسالة")
    async def auto_message_delete(self, ctx: commands.Context, index: int):
        """حذف رسالة تلقائية"""
        guild_data = self.get_guild_data(ctx.guild.id)
        messages = guild_data["auto_messages"]
        if index < 1 or index > len(messages):
            await ctx.send("❌ رقم غير صحيح")
            return
        messages.pop(index - 1)
        self.save()
        await ctx.send(f"✅ تم حذف الرسالة رقم {index}")

    @auto_message.command(name="list", aliases=["ls", "عرض"], description="عرض الرسائل التلقائية")
    async def auto_message_list(self, ctx: commands.Context):
        """عرض الرسائل التلقائية"""
        guild_data = self.get_guild_data(ctx.guild.id)
        messages = guild_data["auto_messages"]
        if not messages:
            await ctx.send("📭 لا توجد رسائل تلقائية")
            return
        desc = ""
        for i, msg in enumerate(messages, 1):
            ch = ctx.guild.get_channel(msg["channel_id"])
            ch_name = ch.mention if ch else "محذوف"
            desc += f"**{i}.** {ch_name} - كل {msg['interval']}ث\n"
        embed = discord.Embed(title="📋 الرسائل التلقائية", description=desc, color=0x3498DB)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💬 !auto-reply / /auto-reply (Group)
    # ═══════════════════════════════════════
    @commands.hybrid_group(
        name="auto-reply",
        aliases=["ar", "رد-تلقائي"],
        description="💬 إدارة الردود التلقائية",
        invoke_without_command=True
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def auto_reply(self, ctx: commands.Context):
        """عرض المساعدة"""
        embed = discord.Embed(
            title="💬 أوامر الردود التلقائية",
            description=(
                "**Slash:**\n"
                "`/auto-reply add trigger response` - إضافة رد\n"
                "`/auto-reply delete trigger` - حذف رد\n"
                "`/auto-reply show` - عرض الكل\n\n"
                "**Prefix:**\n"
                "`!auto-reply add trigger response`"
            ),
            color=0x3498DB
        )
        await ctx.send(embed=embed)

    @auto_reply.command(name="add", aliases=["+", "اضف"], description="إضافة رد تلقائي")
    @app_commands.describe(trigger="الكلمة المفتاحية", response="الرد")
    async def auto_reply_add(self, ctx: commands.Context, trigger: str, *, response: str):
        """إضافة رد تلقائي"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["auto_replies"].append({
            "trigger": trigger.lower(),
            "response": response
        })
        self.save()
        await ctx.send(f"✅ تم إضافة الرد: `{trigger}` → {response}")

    @auto_reply.command(name="delete", aliases=["del", "احذف"], description="حذف رد تلقائي")
    @app_commands.describe(trigger="الكلمة المفتاحية")
    async def auto_reply_delete(self, ctx: commands.Context, *, trigger: str):
        """حذف رد تلقائي"""
        guild_data = self.get_guild_data(ctx.guild.id)
        initial = len(guild_data["auto_replies"])
        guild_data["auto_replies"] = [
            r for r in guild_data["auto_replies"] if r["trigger"] != trigger.lower()
        ]
        if len(guild_data["auto_replies"]) == initial:
            await ctx.send("❌ لم يتم العثور")
            return
        self.save()
        await ctx.send("✅ تم الحذف")

    @auto_reply.command(name="show", aliases=["عرض"], description="عرض الردود التلقائية")
    async def auto_reply_show(self, ctx: commands.Context):
        """عرض الردود التلقائية"""
        guild_data = self.get_guild_data(ctx.guild.id)
        replies = guild_data["auto_replies"]
        if not replies:
            await ctx.send("📭 لا توجد ردود")
            return
        desc = "\n".join(f"`{r['trigger']}` → {r['response'][:50]}" for r in replies[:20])
        embed = discord.Embed(title="📋 الردود التلقائية", description=desc, color=0x3498DB)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🛡️ !automod / /automod (Group)
    # ═══════════════════════════════════════
    @commands.hybrid_group(
        name="automod",
        aliases=["ام-مود", "كلمات-ممنوعة"],
        description="🛡️ إدارة الكلمات الممنوعة",
        invoke_without_command=True
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def automod(self, ctx: commands.Context):
        """عرض المساعدة"""
        embed = discord.Embed(
            title="🛡️ أوامر AutoMod",
            description=(
                "**Slash:**\n"
                "`/automod create اسم-القاعدة كلمة1,كلمة2` - إنشاء قاعدة\n"
                "`/automod delete اسم-القاعدة` - حذف قاعدة"
            ),
            color=0x3498DB
        )
        await ctx.send(embed=embed)

    @automod.command(name="create", aliases=["+", "انشئ"], description="إنشاء قاعدة")
    @app_commands.describe(name="اسم القاعدة", trigger="الكلمات المفتاحية مفصولة بفاصلة")
    async def automod_create(self, ctx: commands.Context, name: str, *, trigger: str):
        """إنشاء قاعدة AutoMod"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["automod_rules"].append({
            "name": name,
            "triggers": [t.strip().lower() for t in trigger.split(",")]
        })
        self.save()
        await ctx.send(f"✅ تم إنشاء قاعدة `{name}`")

    @automod.command(name="delete", aliases=["del", "احذف"], description="حذف قاعدة")
    @app_commands.describe(name="اسم القاعدة")
    async def automod_delete(self, ctx: commands.Context, *, name: str):
        """حذف قاعدة AutoMod"""
        guild_data = self.get_guild_data(ctx.guild.id)
        initial = len(guild_data["automod_rules"])
        guild_data["automod_rules"] = [
            r for r in guild_data["automod_rules"] if r["name"].lower() != name.lower()
        ]
        if len(guild_data["automod_rules"]) == initial:
            await ctx.send("❌ لم يتم العثور")
            return
        self.save()
        await ctx.send("✅ تم الحذف")

    # ═══════════════════════════════════════
    # 🎭 !autorole / /autorole
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="autorole",
        aliases=["ار-رول", "رتبة-تلقائية"],
        description="🎭 تعيين رتبة تلقائية"
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(role="الرتبة التلقائية")
    async def autorole(self, ctx: commands.Context, role: discord.Role):
        """تعيين رتبة تلقائية"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["autorole"] = role.id
        self.save()
        await ctx.send(f"✅ تم تعيين {role.mention} كرتبة تلقائية")

    # ═══════════════════════════════════════
    # 📋 !log / /log (Group)
    # ═══════════════════════════════════════
    @commands.hybrid_group(
        name="log",
        aliases=["لوج", "سجل"],
        description="📋 إدارة السجلات",
        invoke_without_command=True
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def log(self, ctx: commands.Context):
        """عرض المساعدة"""
        embed = discord.Embed(
            title="📋 أوامر السجلات",
            description=(
                "`/log set #روم` - تعيين روم السجلات\n"
                "`/log stop` - إيقاف السجلات"
            ),
            color=0x3498DB
        )
        await ctx.send(embed=embed)

    @log.command(name="set", aliases=["عين"], description="تعيين روم السجلات")
    @app_commands.describe(channel="الروم")
    async def log_set(self, ctx: commands.Context, channel: discord.TextChannel):
        """تعيين روم السجلات"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["log_channel"] = channel.id
        self.save()
        await ctx.send(f"✅ تم تعيين {channel.mention}")

    @log.command(name="stop", aliases=["ايقاف", "وقف"], description="إيقاف السجلات")
    async def log_stop(self, ctx: commands.Context):
        """إيقاف السجلات"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["log_channel"] = None
        self.save()
        await ctx.send("✅ تم إيقاف السجلات")

    # ═══════════════════════════════════════
    # 👤 !perms / /perms
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="perms",
        aliases=["صلاحيات", "permissions"],
        description="👤 عرض صلاحيات العضو"
    )
    @app_commands.describe(member="العضو (اختياري)")
    async def perms(self, ctx: commands.Context, member: discord.Member = None):
        """عرض صلاحيات العضو"""
        target = member or ctx.author
        perms = [f"✅ {p.replace('_', ' ').title()}" for p, v in target.guild_permissions if v][:20]
        embed = discord.Embed(
            title=f"🔐 صلاحيات {target.display_name}",
            description="\n".join(perms) or "لا توجد",
            color=0x3498DB
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ⚙️ !settings / /settings
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="settings",
        aliases=["set", "الاعدادات", "اعدادات"],
        description="⚙️ عرض إعدادات السيرفر"
    )
    async def settings_cmd(self, ctx: commands.Context):
        """عرض إعدادات السيرفر"""
        guild_data = self.get_guild_data(ctx.guild.id)
        embed = discord.Embed(title="⚙️ إعدادات السيرفر", color=0x3498DB)
        embed.add_field(name="📝 الرسائل التلقائية", value=f"{len(guild_data['auto_messages'])}", inline=True)
        embed.add_field(name="💬 الردود", value=f"{len(guild_data['auto_replies'])}", inline=True)
        embed.add_field(name="🛡️ AutoMod", value=f"{len(guild_data['automod_rules'])}", inline=True)
        embed.add_field(name="🎭 Autorole", value="✅" if guild_data.get("autorole") else "❌", inline=True)
        embed.add_field(name="📋 Logs", value="✅" if guild_data.get("log_channel") else "❌", inline=True)
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات المطلوبة!", delete_after=8)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت مفيش عنده الصلاحيات المطلوبة!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص بيانات: `{error.param.name}`", delete_after=8)
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي القناة!", delete_after=8)
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ مش لاقي الرتبة!", delete_after=8)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو!", delete_after=8)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!", delete_after=8)
        else:
            print(f"❌ خطأ في أمر {ctx.command}: {error}")


# ═══════════════════════════════════════
# 🎛️ Views للمعالج
# ═══════════════════════════════════════
class SetupStartView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="ابدأ الإعداد", emoji="🚀", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛡️ المرحلة 1/4 — الحماية",
            description="هيتم تفعيل **كل** أنظمة الحماية للسيرفر.\n\nهل أنت موافق؟",
            color=0x8b5cf6
        )
        await interaction.response.edit_message(embed=embed, view=SetupConfirmView(self.cog))

    @discord.ui.button(label="إلغاء", emoji="✖️", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ تم إلغاء الإعداد", embed=None, view=None)


class SetupConfirmView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="تفعيل الحماية", emoji="🛡️", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.do_setup_protection(interaction)

    @discord.ui.button(label="رجوع", emoji="↩️", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🚀 معالج الإعداد",
            description="اضغط **ابدأ** للبدء.",
            color=0x8b5cf6
        )
        await interaction.response.edit_message(embed=embed, view=SetupStartView(self.cog))


class SetupAutoroleView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="🎭 اختر الرتبة التلقائية...",
        min_values=1,
        max_values=1
    )
    async def select_role(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        role = select.values[0]
        await self.cog.do_setup_autorole(interaction, role)


class SetupWelcomeView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="👋 اختر روم الترحيب...",
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1
    )
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        real_channel = interaction.guild.get_channel(channel.id)
        if real_channel:
            await self.cog.do_setup_welcome(interaction, real_channel)


class SetupLogView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="📋 اختر روم اللوجات...",
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1
    )
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        real_channel = interaction.guild.get_channel(channel.id)
        if real_channel:
            await self.cog.do_setup_log(interaction, real_channel)


async def setup(bot):
    await bot.add_cog(Settings(bot))