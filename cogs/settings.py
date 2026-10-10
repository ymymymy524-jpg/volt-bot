import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import aiohttp

# مسار ملف التخزين
SETTINGS_FILE = "settings.json"

# دالة لتحميل البيانات من ملف JSON
def load_data():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# دالة لحفظ البيانات في ملف JSON
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

    # =================== أمر /add-emoji ===================
    @app_commands.command(name="add-emoji", description="إضافة إيموجي للسيرفر")
    @app_commands.describe(name="اسم الإيموجي", url="رابط الصورة (PNG/JPG/GIF)")
    @app_commands.checks.has_permissions(manage_emojis=True)
    async def add_emoji(self, interaction: discord.Interaction, name: str, url: str):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ رابط غير صالح")
                        return
                    image_bytes = await resp.read()
            emoji = await interaction.guild.create_custom_emoji(name=name, image=image_bytes)
            embed = discord.Embed(title="✅ تم إضافة الإيموجي", description=f"تم إضافة {emoji} بنجاح!", color=discord.Color.green())
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {str(e)}")

    # =================== مجموعة /auto-message ===================
    auto_message = app_commands.Group(name="auto-message", description="إدارة الرسائل التلقائية", default_permissions=discord.Permissions(administrator=True))

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
            await interaction.response.send_message("❌ رقم غير صحيح", ephemeral=True)
            return
        messages.pop(index - 1)
        self.save()
        await interaction.response.send_message(f"✅ تم حذف الرسالة رقم {index}")

    @auto_message.command(name="edit", description="تعديل رسالة تلقائية")
    async def auto_message_edit(self, interaction: discord.Interaction, index: app_commands.Range[int, 1], message: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        messages = guild_data["auto_messages"]
        if index > len(messages):
            await interaction.response.send_message("❌ رقم غير صحيح", ephemeral=True)
            return
        messages[index - 1]["message"] = message
        self.save()
        await interaction.response.send_message(f"✅ تم تعديل الرسالة رقم {index}")

    @auto_message.command(name="list", description="عرض الرسائل التلقائية")
    async def auto_message_list(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        messages = guild_data["auto_messages"]
        if not messages:
            await interaction.response.send_message("📭 لا توجد رسائل تلقائية")
            return
        desc = ""
        for i, msg in enumerate(messages, 1):
            ch = interaction.guild.get_channel(msg["channel_id"])
            ch_name = ch.mention if ch else "محذوف"
            desc += f"**{i}.** {ch_name} - كل {msg['interval']}ث\n"
        embed = discord.Embed(title="📋 الرسائل التلقائية", description=desc, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    # =================== مجموعة /auto-reply ===================
    auto_reply = app_commands.Group(name="auto-reply", description="إدارة الردود التلقائية", default_permissions=discord.Permissions(administrator=True))

    @auto_reply.command(name="add", description="إضافة رد تلقائي")
    async def auto_reply_add(self, interaction: discord.Interaction, trigger: str, response: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["auto_replies"].append({"trigger": trigger.lower(), "response": response})
        self.save()
        await interaction.response.send_message(f"✅ تم إضافة الرد: `{trigger}` → {response}")

    @auto_reply.command(name="edit", description="تعديل رد تلقائي")
    async def auto_reply_edit(self, interaction: discord.Interaction, trigger: str, response: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        for reply in guild_data["auto_replies"]:
            if reply["trigger"] == trigger.lower():
                reply["response"] = response
                self.save()
                await interaction.response.send_message("✅ تم التعديل")
                return
        await interaction.response.send_message("❌ لم يتم العثور على الرد", ephemeral=True)

    @auto_reply.command(name="delete", description="حذف رد تلقائي")
    async def auto_reply_delete(self, interaction: discord.Interaction, trigger: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        initial = len(guild_data["auto_replies"])
        guild_data["auto_replies"] = [r for r in guild_data["auto_replies"] if r["trigger"] != trigger.lower()]
        if len(guild_data["auto_replies"]) == initial:
            await interaction.response.send_message("❌ لم يتم العثور", ephemeral=True)
            return
        self.save()
        await interaction.response.send_message("✅ تم الحذف")

    @auto_reply.command(name="show", description="عرض الردود التلقائية")
    async def auto_reply_show(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        replies = guild_data["auto_replies"]
        if not replies:
            await interaction.response.send_message("📭 لا توجد ردود")
            return
        desc = "\n".join(f"`{r['trigger']}` → {r['response'][:50]}" for r in replies[:20])
        embed = discord.Embed(title="📋 الردود التلقائية", description=desc, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    # =================== مجموعة /automod ===================
    automod = app_commands.Group(name="automod", description="إدارة قواعد AutoMod", default_permissions=discord.Permissions(administrator=True))

    @automod.command(name="create", description="إنشاء قاعدة AutoMod")
    @app_commands.choices(action=[
        app_commands.Choice(name="⏸️ Timeout", value="timeout"),
        app_commands.Choice(name="🗑️ حذف", value="delete"),
        app_commands.Choice(name="⚠️ تحذير", value="warn")
    ])
    async def automod_create(self, interaction: discord.Interaction, name: str, trigger: str, action: app_commands.Choice[str]):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["automod_rules"].append({"name": name, "triggers": [t.strip().lower() for t in trigger.split(",")], "action": action.value})
        self.save()
        await interaction.response.send_message(f"✅ تم إنشاء قاعدة `{name}`")

    @automod.command(name="edit", description="تعديل قاعدة")
    async def automod_edit(self, interaction: discord.Interaction, name: str, trigger: str = None):
        guild_data = self.get_guild_data(interaction.guild.id)
        for rule in guild_data["automod_rules"]:
            if rule["name"].lower() == name.lower():
                if trigger:
                    rule["triggers"] = [t.strip().lower() for t in trigger.split(",")]
                self.save()
                await interaction.response.send_message("✅ تم التعديل")
                return
        await interaction.response.send_message("❌ لم يتم العثور", ephemeral=True)

    @automod.command(name="delete", description="حذف قاعدة")
    async def automod_delete(self, interaction: discord.Interaction, name: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        initial = len(guild_data["automod_rules"])
        guild_data["automod_rules"] = [r for r in guild_data["automod_rules"] if r["name"].lower() != name.lower()]
        if len(guild_data["automod_rules"]) == initial:
            await interaction.response.send_message("❌ لم يتم العثور", ephemeral=True)
            return
        self.save()
        await interaction.response.send_message("✅ تم الحذف")

    # =================== أمر /autorole ===================
    @app_commands.command(name="autorole", description="تعيين رول تلقائي للأعضاء الجدد")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole(self, interaction: discord.Interaction, role: discord.Role):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["autorole"] = role.id
        self.save()
        await interaction.response.send_message(f"✅ تم تعيين {role.mention} كرول تلقائي")

    # =================== مجموعة /change-log ===================
    change_log = app_commands.Group(name="change-log", description="سجل التغييرات", default_permissions=discord.Permissions(administrator=True))

    @change_log.command(name="view", description="عرض السجل")
    async def change_log_view(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📜 سجل التغييرات", description="سجل التغييرات الأخيرة", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @change_log.command(name="summary", description="ملخص التغييرات")
    async def change_log_summary(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        summary = f"📊 الرسائل التلقائية: {len(guild_data['auto_messages'])}\n💬 الردود: {len(guild_data['auto_replies'])}\n🛡️ AutoMod: {len(guild_data['automod_rules'])}"
        embed = discord.Embed(title="📊 ملخص الإعدادات", description=summary, color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    # =================== مجموعة /command-disable ===================
    command_disable = app_commands.Group(name="command-disable", description="إدارة تعطيل الأوامر", default_permissions=discord.Permissions(administrator=True))

    @command_disable.command(name="list", description="عرض الأوامر المعطلة")
    async def command_disable_list(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        disabled = guild_data["disabled_commands"]
        if not disabled:
            await interaction.response.send_message("✅ لا توجد أوامر معطلة")
            return
        await interaction.response.send_message(f"🚫 الأوامر المعطلة: {', '.join(disabled)}")

    @command_disable.command(name="enable", description="تفعيل أمر")
    async def command_disable_enable(self, interaction: discord.Interaction, command: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        if command not in guild_data["disabled_commands"]:
            await interaction.response.send_message("❌ الأمر غير معطل", ephemeral=True)
            return
        guild_data["disabled_commands"].remove(command)
        self.save()
        await interaction.response.send_message(f"✅ تم تفعيل `/{command}`")

    # =================== أمر /level-up-msg ===================
    @app_commands.command(name="level-up-msg", description="تعيين رسالة الترقية")
    @app_commands.checks.has_permissions(administrator=True)
    async def level_up_msg(self, interaction: discord.Interaction, message: str):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["level_up_msg"] = message
        self.save()
        await interaction.response.send_message(f"✅ تم تعيين رسالة الترقية")

    # =================== مجموعة /level ===================
    level = app_commands.Group(name="level", description="إدارة المستويات", default_permissions=discord.Permissions(administrator=True))

    @level.command(name="status", description="عرض حالة نظام المستويات")
    async def level_status(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📊 حالة نظام المستويات", color=discord.Color.blue())
        embed.add_field(name="✅ الحالة", value="مفعّل")
        embed.add_field(name="📈 XP لكل رسالة", value="5-15")
        await interaction.response.send_message(embed=embed)

    @level.command(name="reset", description="إعادة تعيين المستويات")
    async def level_reset(self, interaction: discord.Interaction):
        levels_cog = self.bot.get_cog("Levels")
        if levels_cog:
            gid = str(interaction.guild.id)
            if gid in levels_cog.data:
                levels_cog.data[gid] = {}
                levels_cog.save()
        await interaction.response.send_message("✅ تم إعادة تعيين كل المستويات")

    @level.command(name="xp-adjust", description="تعديل XP")
    async def level_xp_adjust(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        levels_cog = self.bot.get_cog("Levels")
        if levels_cog:
            gid, uid = str(interaction.guild.id), str(member.id)
            data = levels_cog.get_user_data(gid, uid)
            data["xp"] = max(0, data["xp"] + amount)
            levels_cog.save()
        await interaction.response.send_message(f"✅ تم تعديل XP لـ {member.mention}")

    @level.command(name="xp-edit", description="تعيين XP")
    async def level_xp_edit(self, interaction: discord.Interaction, member: discord.Member, xp: app_commands.Range[int, 0]):
        levels_cog = self.bot.get_cog("Levels")
        if levels_cog:
            gid, uid = str(interaction.guild.id), str(member.id)
            data = levels_cog.get_user_data(gid, uid)
            data["xp"] = xp
            levels_cog.save()
        await interaction.response.send_message(f"✅ تم تعيين XP")

    @level.command(name="reward", description="مكافأة رول")
    async def level_reward(self, interaction: discord.Interaction, level_num: int, role: discord.Role):
        await interaction.response.send_message(f"✅ المستوى {level_num} → {role.mention}")

    # =================== مجموعة /log ===================
    log = app_commands.Group(name="log", description="سجلات السيرفر", default_permissions=discord.Permissions(administrator=True))

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

    @log.command(name="auto-set", description="إعداد السجلات تلقائياً")
    async def log_auto_set(self, interaction: discord.Interaction):
        try:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            ch = await interaction.guild.create_text_channel(name="logs", overwrites=overwrites)
            guild_data = self.get_guild_data(interaction.guild.id)
            guild_data["log_channel"] = ch.id
            self.save()
            await interaction.response.send_message(f"✅ تم إنشاء {ch.mention}")
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

    # =================== أمر /perms ===================
    @app_commands.command(name="perms", description="عرض صلاحيات العضو")
    async def perms(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        perms = [f"✅ {p.replace('_', ' ').title()}" for p, v in target.guild_permissions if v][:20]
        embed = discord.Embed(title=f"🔐 صلاحيات {target.display_name}", description="\n".join(perms) or "لا توجد", color=discord.Color.blue())
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # =================== أمر /role-icon ===================
    @app_commands.command(name="role-icon", description="تعيين أيقونة للرول")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_icon(self, interaction: discord.Interaction, role: discord.Role, emoji: str):
        try:
            await role.edit(display_icon=emoji)
            await interaction.response.send_message(f"✅ تم تعيين {emoji} لـ {role.mention}")
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

    # =================== أمر /role-info ===================
    @app_commands.command(name="role-info", description="معلومات الرول")
    async def role_info(self, interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(title=f"ℹ️ {role.name}", color=role.color)
        embed.add_field(name="🆔", value=f"`{role.id}`", inline=True)
        embed.add_field(name="🎨", value=f"{role.color}", inline=True)
        embed.add_field(name="👥", value=f"{len(role.members)}", inline=True)
        await interaction.response.send_message(embed=embed)

    # =================== أمر /role-move ===================
    @app_commands.command(name="role-move", description="نقل رول لموقع جديد")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_move(self, interaction: discord.Interaction, role: discord.Role, position: app_commands.Range[int, 1]):
        try:
            await role.edit(position=position)
            await interaction.response.send_message(f"✅ تم نقل {role.mention}")
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

    # =================== مجموعة /self-roles ===================
    self_roles = app_commands.Group(name="self-roles", description="الرولات الذاتية", default_permissions=discord.Permissions(administrator=True))

    @self_roles.command(name="create", description="إنشاء رسالة الرولات الذاتية")
    async def self_roles_create(self, interaction: discord.Interaction, roles: str):
        role_ids = [int(r.strip()) for r in roles.split(",") if r.strip().isdigit()]
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["self_roles"] = role_ids
        self.save()
        view = discord.ui.View(timeout=None)
        for rid in role_ids:
            role = interaction.guild.get_role(rid)
            if role:
                btn = discord.ui.Button(label=role.name, style=discord.ButtonStyle.primary, custom_id=f"selfrole_{rid}")
                view.add_item(btn)
        embed = discord.Embed(title="🎭 اختر رولاتك", description="اضغط على الأزرار", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed, view=view)

    @self_roles.command(name="delete", description="حذف الرولات الذاتية")
    async def self_roles_delete(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["self_roles"] = []
        self.save()
        await interaction.response.send_message("✅ تم الحذف")

    # =================== مجموعة /embed ===================
    embed_cmd = app_commands.Group(name="embed", description="إدارة Embeds", default_permissions=discord.Permissions(administrator=True))

    @embed_cmd.command(name="create", description="إنشاء Embed")
    async def embed_create(self, interaction: discord.Interaction, title: str, description: str, color: str = "#5865F2"):
        try:
            embed_color = discord.Color(int(color.lstrip('#'), 16))
        except:
            embed_color = discord.Color.blue()
        embed = discord.Embed(title=title, description=description, color=embed_color)
        await interaction.response.send_message(embed=embed)

    @embed_cmd.command(name="delete", description="حذف Embed")
    async def embed_delete(self, interaction: discord.Interaction, message_id: str):
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
            await msg.delete()
            await interaction.response.send_message("✅ تم الحذف", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

    @embed_cmd.command(name="log", description="سجل الـ Embeds")
    async def embed_log(self, interaction: discord.Interaction):
        await interaction.response.send_message("📜 سجل الـ Embeds", ephemeral=True)

    # =================== أمر /settings ===================
    @app_commands.command(name="settings", description="عرض إعدادات السيرفر")
    async def settings(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        embed = discord.Embed(title="⚙️ إعدادات السيرفر", color=discord.Color.blue())
        embed.add_field(name="📝 الرسائل التلقائية", value=f"{len(guild_data['auto_messages'])}", inline=True)
        embed.add_field(name="💬 الردود", value=f"{len(guild_data['auto_replies'])}", inline=True)
        embed.add_field(name="🛡️ AutoMod", value=f"{len(guild_data['automod_rules'])}", inline=True)
        await interaction.response.send_message(embed=embed)

    # =================== أمر /setup ===================
    @app_commands.command(name="setup", description="إعداد البوت في السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            welcome_ch = await interaction.guild.create_text_channel(name="welcome", topic="روم الترحيب")
            log_ch = await interaction.guild.create_text_channel(name="logs", topic="روم السجلات")
            guild_data = self.get_guild_data(interaction.guild.id)
            guild_data["log_channel"] = log_ch.id
            welcome_cog = self.bot.get_cog("Welcome")
            if welcome_cog:
                wd = welcome_cog.get_guild_data(interaction.guild.id)
                wd["welcome_channel"] = welcome_ch.id
                wd["goodbye_channel"] = welcome_ch.id
                welcome_cog.save()
            self.save()
            embed = discord.Embed(title="✅ تم الإعداد", description=f"{welcome_ch.mention}\n{log_ch.mention}", color=discord.Color.green())
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}")

    # =================== أمر /shorts ===================
    @app_commands.command(name="shorts", description="أوامر مختصرة")
    async def shorts(self, interaction: discord.Interaction):
        embed = discord.Embed(title="⚡ الأوامر المختصرة", color=discord.Color.blue())
        embed.add_field(name="/rank", value="مستواك", inline=True)
        embed.add_field(name="/top", value="أفضل 10", inline=True)
        embed.add_field(name="/balance", value="رصيدك", inline=True)
        embed.add_field(name="/daily", value="المكافأة اليومية", inline=True)
        embed.add_field(name="/work", value="العمل", inline=True)
        embed.add_field(name="/game", value="الألعاب", inline=True)
        await interaction.response.send_message(embed=embed)

    # =================== أمر /end-premium ===================
    @app_commands.command(name="end-premium", description="إنهاء البريميوم")
    @app_commands.checks.has_permissions(administrator=True)
    async def end_premium(self, interaction: discord.Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["premium_end"] = None
        self.save()
        await interaction.response.send_message("✅ تم إنهاء البريميوم")

    # =================== معالجة الأخطاء ===================
    @add_emoji.error
    @autorole.error
    @level_up_msg.error
    @role_icon.error
    @role_move.error
    @setup.error
    @end_premium.error
    async def on_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ مفيش عندك صلاحية Administrator!"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

# دالة تحميل الـ Cog
async def setup(bot):
    await bot.add_cog(Settings(bot))