import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import aiohttp

# ═══════════════════════════════════════
# 📁 إعدادات
# ═══════════════════════════════════════
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
    # 🚀 أمر /setup التفاعلي
    # ═══════════════════════════════════════
    @app_commands.command(name="setup", description="🚀 إعداد البوت في السيرفر (تفاعلي)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_wizard(self, interaction: discord.Interaction):
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
        await interaction.response.send_message(
            embed=embed,
            view=SetupStartView(self),
            ephemeral=True
        )

    # ═══════════════════════════════════════
    # 🛠️ خطوات المعالج
    # ═══════════════════════════════════════
    async def do_setup_protection(self, interaction: discord.Interaction):
        """تفعيل الحماية الأساسية"""
        try:
            protection_cog = self.bot.get_cog("Protection")
            
            if not protection_cog:
                return await interaction.response.edit_message(
                    content="❌ cog الحماية غير محمّل", embed=None, view=None
                )
            
            # نفعّل كل أنظمة الحماية
            protection_cog.data[str(interaction.guild.id)] = {
                "auto": True,
                "spam": {"enabled": True, "limit": 5, "seconds": 3},
                "link": {"enabled": True, "type": "all"},
                "join": {"enabled": True, "min_age": 7},
                "hacked": True,
                "bans": True,
                "kicks": True,
                "channels": True,
                "roles": True,
                "bots": {"enabled": True, "action": "kick"},
                "log_channel": None,
                "whitelist": [],
                "blacklist": []
            }
            protection_cog.save()
            
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
                content=f"❌ خطأ: {e}",
                embed=None,
                view=None
            )

    async def do_setup_autorole(self, interaction: discord.Interaction, role: discord.Role):
        """تعيين الرتبة التلقائية"""
        try:
            guild_data = self.get_guild_data(interaction.guild.id)
            guild_data["autorole"] = role.id
            self.save()
            
            embed = discord.Embed(
                title="✅ المرحلة 2/4 — تم تعيين الرتبة التلقائية",
                description=(
                    f"الرتبة: {role.mention}\n\n"
                    "**المرحلة الجاية:** اختار روم الترحيب 👇"
                ),
                color=0x2ECC71
            )
            await interaction.response.edit_message(embed=embed, view=SetupWelcomeView(self))
        except Exception as e:
            await interaction.response.edit_message(
                content=f"❌ خطأ: {e}",
                embed=None,
                view=None
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
                description=(
                    f"الروم: {channel.mention}\n"
                    f"(هيتم استخدامه للترحيب والوداع)\n\n"
                    "**المرحلة الجاية:** اختار روم اللوجات 👇"
                ),
                color=0x2ECC71
            )
            await interaction.response.edit_message(embed=embed, view=SetupLogView(self))
        except Exception as e:
            await interaction.response.edit_message(
                content=f"❌ خطأ: {e}",
                embed=None,
                view=None
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
                    "**الإعدادات النهائية:**\n"
                    "🛡️ الحماية: **مفعّلة**\n"
                    "🎭 الرتبة التلقائية: **تم تعيينها**\n"
                    "👋 روم الترحيب: **تم تعيينه**\n"
                    "📋 روم اللوجات: **تم تعيينه**\n\n"
                    "**ابدأ استخدام البوت بـ `/help`** 🚀"
                ),
                color=0x2ECC71
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await interaction.response.edit_message(
                content=f"❌ خطأ: {e}",
                embed=None,
                view=None
            )

    # ═══════════════════════════════════════
    # 🎨 أوامر قديمة (احتفظنا بيها)
    # ═══════════════════════════════════════
    @app_commands.command(name="add-emoji", description="إضافة إيموجي للسيرفر")
    @app_commands.describe(name="اسم الإيموجي", url="رابط الصورة")
    @app_commands.checks.has_permissions(manage_emojis=True)
    async def add_emoji(self, interaction: discord.Interaction, name: str, url: str):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ رابط غير صالح")
                    image_bytes = await resp.read()
            emoji = await interaction.guild.create_custom_emoji(name=name, image=image_bytes)
            embed = discord.Embed(title="✅ تم إضافة الإيموجي", description=f"تم إضافة {emoji} بنجاح!", color=0x2ECC71)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {str(e)}")

    # ═══════════════════════════════════════
    # 📨 الرسائل التلقائية
    # ═══════════════════════════════════════
    auto_message = app_commands.Group(
        name="auto-message",
        description="إدارة الرسائل التلقائية",
        default_permissions=discord.Permissions(administrator=True)
    )

    @auto_message.command(name="add", description="إضافة رسالة تلقائية")
    async def auto_message_add(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str, interval: app_commands.Range[int, 60, 86400]):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["auto_messages"].append({"channel_id": channel.id, "message": message, "interval": interval})
        self.save()
        await interaction.response.send_message(f"✅ تم إضافة رسالة تلقائية في {channel.mention} كل {interval} ثانية")

    @auto_message.command(name="delete", description="حذف رسالة تلقائية")
    async def auto_message_delete(self, interaction: discord.Interaction, index: app_commands.Range[int, 1]):
        guild_data = self.get_guild_data(interaction.guild.id)
        messages = guild_data["auto_messages"]
        if index > len(messages):
            return await interaction.response.send_message("❌ رقم غير صحيح", ephemeral=True)
        messages.pop(index - 1)
        self.save()
        await interaction.response.send_message(f"✅ تم حذف الرسالة رقم {index}")

    @auto_message.command(name="list", description="عرض الرسائل التلقائية")
    async def auto_message_list(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        messages = guild_data["auto_messages"]
        if not messages:
            return await interaction.response.send_message("📭 لا توجد رسائل تلقائية")
        desc = ""
        for i, msg in enumerate(messages, 1):
            ch = interaction.guild.get_channel(msg["channel_id"])
            ch_name = ch.mention if ch else "محذوف"
            desc += f"**{i}.** {ch_name} - كل {msg['interval']}ث\n"
        embed = discord.Embed(title="📋 الرسائل التلقائية", description=desc, color=0x3498DB)
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # 💬 الردود التلقائية
    # ═══════════════════════════════════════
    auto_reply = app_commands.Group(
        name="auto-reply",
        description="إدارة الردود التلقائية",
        default_permissions=discord.Permissions(administrator=True)
    )

    @auto_reply.command(name="add", description="إضافة رد تلقائي")
    async def auto_reply_add(self, interaction: discord.Interaction, trigger: str, response: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["auto_replies"].append({"trigger": trigger.lower(), "response": response})
        self.save()
        await interaction.response.send_message(f"✅ تم إضافة الرد: `{trigger}` → {response}")

    @auto_reply.command(name="delete", description="حذف رد تلقائي")
    async def auto_reply_delete(self, interaction: discord.Interaction, trigger: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        initial = len(guild_data["auto_replies"])
        guild_data["auto_replies"] = [r for r in guild_data["auto_replies"] if r["trigger"] != trigger.lower()]
        if len(guild_data["auto_replies"]) == initial:
            return await interaction.response.send_message("❌ لم يتم العثور", ephemeral=True)
        self.save()
        await interaction.response.send_message("✅ تم الحذف")

    @auto_reply.command(name="show", description="عرض الردود التلقائية")
    async def auto_reply_show(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        replies = guild_data["auto_replies"]
        if not replies:
            return await interaction.response.send_message("📭 لا توجد ردود")
        desc = "\n".join(f"`{r['trigger']}` → {r['response'][:50]}" for r in replies[:20])
        embed = discord.Embed(title="📋 الردود التلقائية", description=desc, color=0x3498DB)
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # 🛡️ AutoMod
    # ═══════════════════════════════════════
    automod = app_commands.Group(
        name="automod",
        description="إدارة الكلمات الممنوعة",
        default_permissions=discord.Permissions(administrator=True)
    )

    @automod.command(name="create", description="إنشاء قاعدة")
    async def automod_create(self, interaction: discord.Interaction, name: str, trigger: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["automod_rules"].append({
            "name": name,
            "triggers": [t.strip().lower() for t in trigger.split(",")]
        })
        self.save()
        await interaction.response.send_message(f"✅ تم إنشاء قاعدة `{name}`")

    @automod.command(name="delete", description="حذف قاعدة")
    async def automod_delete(self, interaction: discord.Interaction, name: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        initial = len(guild_data["automod_rules"])
        guild_data["automod_rules"] = [r for r in guild_data["automod_rules"] if r["name"].lower() != name.lower()]
        if len(guild_data["automod_rules"]) == initial:
            return await interaction.response.send_message("❌ لم يتم العثور", ephemeral=True)
        self.save()
        await interaction.response.send_message("✅ تم الحذف")

    # ═══════════════════════════════════════
    # 🎭 Autorole
    # ═══════════════════════════════════════
    @app_commands.command(name="autorole", description="تعيين رتبة تلقائية")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole(self, interaction: discord.Interaction, role: discord.Role):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["autorole"] = role.id
        self.save()
        await interaction.response.send_message(f"✅ تم تعيين {role.mention} كرتبة تلقائية")

    # ═══════════════════════════════════════
    # 📋 Logs
    # ═══════════════════════════════════════
    log = app_commands.Group(
        name="log",
        description="إدارة السجلات",
        default_permissions=discord.Permissions(administrator=True)
    )

    @log.command(name="set", description="تعيين روم السجلات")
    async def log_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["log_channel"] = channel.id
        self.save()
        await interaction.response.send_message(f"✅ تم تعيين {channel.mention}")

    @log.command(name="stop", description="إيقاف السجلات")
    async def log_stop(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["log_channel"] = None
        self.save()
        await interaction.response.send_message("✅ تم إيقاف السجلات")

    # ═══════════════════════════════════════
    # 👤 /perms
    # ═══════════════════════════════════════
    @app_commands.command(name="perms", description="عرض صلاحيات العضو")
    async def perms(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        perms = [f"✅ {p.replace('_', ' ').title()}" for p, v in target.guild_permissions if v][:20]
        embed = discord.Embed(title=f"🔐 صلاحيات {target.display_name}", description="\n".join(perms) or "لا توجد", color=0x3498DB)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # ⚙️ /settings
    # ═══════════════════════════════════════
    @app_commands.command(name="settings", description="عرض إعدادات السيرفر")
    async def settings_cmd(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        embed = discord.Embed(title="⚙️ إعدادات السيرفر", color=0x3498DB)
        embed.add_field(name="📝 الرسائل التلقائية", value=f"{len(guild_data['auto_messages'])}", inline=True)
        embed.add_field(name="💬 الردود", value=f"{len(guild_data['auto_replies'])}", inline=True)
        embed.add_field(name="🛡️ AutoMod", value=f"{len(guild_data['automod_rules'])}", inline=True)
        await interaction.response.send_message(embed=embed)


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
        embed = discord.Embed(title="🚀 معالج الإعداد", description="اضغط **ابدأ** للبدء.", color=0x8b5cf6)
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