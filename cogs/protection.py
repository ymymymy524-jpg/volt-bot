import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from config import Colors

# ==========================================
# 🛡️ نظام الحماية (Protection System)
# ==========================================

class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.protection_file = "data/protection.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """التأكد من وجود مجلد data"""
        if not os.path.exists("data"):
            os.makedirs("data")

    def _load_protection(self):
        """تحميل بيانات الحماية"""
        if os.path.exists(self.protection_file):
            with open(self.protection_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_protection(self, data):
        """حفظ بيانات الحماية"""
        with open(self.protection_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_guild_settings(self, guild_id):
        """الحصول على إعدادات الحماية لسيرفر معين"""
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

    # ==========================================
    # 🛡️ مجموعة أوامر الحماية
    # ==========================================
    protection_group = app_commands.Group(
        name="protection",
        description="🛡️ أوامر حماية السيرفر",
        default_permissions=discord.Permissions(administrator=True)
    )

    @protection_group.command(name="auto", description="🤖 تفعيل/تعطيل الحماية التلقائية الشاملة")
    @app_commands.describe(status="تفعيل أو تعطيل")
    async def protection_auto(self, interaction: discord.Interaction, status: bool):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["auto"] = {"enabled": status}
        self._save_protection(data)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="🤖 الحماية التلقائية",
            description=f"تم {status_text} الحماية التلقائية الشاملة",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_group.command(name="spam", description="🚫 حماية من السبام")
    @app_commands.describe(
        status="تفعيل أو تعطيل",
        limit="عدد الرسائل المسموح بها",
        seconds="الفترة الزمنية بالثواني"
    )
    async def protection_spam(self, interaction: discord.Interaction, status: bool, limit: int = 5, seconds: int = 3):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["spam"] = {
            "enabled": status,
            "limit": limit,
            "seconds": seconds
        }
        self._save_protection(data)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="🚫 حماية السبام",
            description=f"حماية السبام: {status_text}\n\n**الإعدادات:**\n"
                        f"• الحد الأقصى: `{limit}` رسائل\n"
                        f"• الفترة الزمنية: `{seconds}` ثواني",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_group.command(name="link", description="🔗 حماية من الروابط")
    @app_commands.describe(
        status="تفعيل أو تعطيل",
        link_type="نوع الروابط المحظورة"
    )
    async def protection_link(self, interaction: discord.Interaction, status: bool, link_type: str = "all"):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["link"] = {
            "enabled": status,
            "type": link_type
        }
        self._save_protection(data)
        
        type_text = {
            "all": "جميع الروابط",
            "discord": "روابط الديسكورد فقط",
            "external": "الروابط الخارجية فقط"
        }.get(link_type, link_type)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="🔗 حماية الروابط",
            description=f"حماية الروابط: {status_text}\n\n**النوع:** {type_text}",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @link_type_autocomplete := protection_link.autocomplete("link_type")
    async def link_type_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name="جميع الروابط", value="all"),
            app_commands.Choice(name="روابط الديسكورد فقط", value="discord"),
            app_commands.Choice(name="الروابط الخارجية فقط", value="external")
        ]

    @protection_group.command(name="join", description="🚪 حماية من انضمام الحسابات الجديدة")
    @app_commands.describe(
        status="تفعيل أو تعطيل",
        min_age="الحد الأدنى لعمر الحساب بالأيام"
    )
    async def protection_join(self, interaction: discord.Interaction, status: bool, min_age: int = 7):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["join"] = {
            "enabled": status,
            "min_age": min_age
        }
        self._save_protection(data)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="🚪 حماية الانضمام",
            description=f"حماية الحسابات الجديدة: {status_text}\n\n**الحد الأدنى لعمر الحساب:** `{min_age}` يوم",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_group.command(name="hacked", description="🔐 حماية من الحسابات المخترقة")
    @app_commands.describe(status="تفعيل أو تعطيل")
    async def protection_hacked(self, interaction: discord.Interaction, status: bool):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["hacked"] = {"enabled": status}
        self._save_protection(data)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="🔐 حماية الحسابات المخترقة",
            description=f"حماية الحسابات المخترقة: {status_text}\n\n"
                        "• كشف السلوك المشبوه\n"
                        "• إرسال رسائل جماعية\n"
                        "• تغييرات سريعة في البروفايل",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_group.command(name="bans", description="🔨 حماية من الحظر الجماعي")
    @app_commands.describe(status="تفعيل أو تعطيل")
    async def protection_bans(self, interaction: discord.Interaction, status: bool):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["bans"] = {"enabled": status}
        self._save_protection(data)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="🔨 حماية الحظر الجماعي",
            description=f"حماية الحظر الجماعي: {status_text}\n\n"
                        "• كشف محاولات الحظر الجماعي\n"
                        "• تقييد صلاحيات الحظر تلقائياً\n"
                        "• إرسال تنبيهات للإدارة",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_group.command(name="kicks", description="👢 حماية من الطرد الجماعي")
    @app_commands.describe(status="تفعيل أو تعطيل")
    async def protection_kicks(self, interaction: discord.Interaction, status: bool):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["kicks"] = {"enabled": status}
        self._save_protection(data)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="👢 حماية الطرد الجماعي",
            description=f"حماية الطرد الجماعي: {status_text}\n\n"
                        "• كشف محاولات الطرد الجماعي\n"
                        "• تقييد صلاحيات الطرد تلقائياً\n"
                        "• إرسال تنبيهات للإدارة",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_group.command(name="channels", description="📺 حماية من حذف/إنشاء القنوات")
    @app_commands.describe(status="تفعيل أو تعطيل")
    async def protection_channels(self, interaction: discord.Interaction, status: bool):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["channels"] = {"enabled": status}
        self._save_protection(data)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="📺 حماية القنوات",
            description=f"حماية القنوات: {status_text}\n\n"
                        "• منع حذف القنوات الجماعي\n"
                        "• منع إنشاء قنوات عشوائية\n"
                        "• تقييد صلاحيات إدارة القنوات",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_group.command(name="roles", description="🎭 حماية من تعديل الرتب")
    @app_commands.describe(status="تفعيل أو تعطيل")
    async def protection_roles(self, interaction: discord.Interaction, status: bool):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["roles"] = {"enabled": status}
        self._save_protection(data)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="🎭 حماية الرتب",
            description=f"حماية الرتب: {status_text}\n\n"
                        "• منع حذف الرتب الجماعي\n"
                        "• منع تعديل صلاحيات الرتب\n"
                        "• تقييد صلاحيات إدارة الرتب",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_group.command(name="bots", description="🤖 حماية من إضافة البوتات")
    @app_commands.describe(
        status="تفعيل أو تعطيل",
        action="الإجراء المتخذ عند إضافة بوت"
    )
    async def protection_bots(self, interaction: discord.Interaction, status: bool, action: str = "kick"):
        data = self._load_protection()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in data:
            data[guild_id] = {}
        
        data[guild_id]["bots"] = {
            "enabled": status,
            "action": action
        }
        self._save_protection(data)
        
        action_text = {
            "kick": "طرد البوت",
            "ban": "حظر البوت",
            "notify": "إرسال تنبيه فقط"
        }.get(action, action)
        
        status_text = "✅ مفعّلة" if status else "❌ معطّلة"
        embed = discord.Embed(
            title="🤖 حماية البوتات",
            description=f"حماية البوتات: {status_text}\n\n**الإجراء:** {action_text}",
            color=Colors.SUCCESS if status else Colors.ERROR
        )
        await interaction.response.send_message(embed=embed)

    @protection_bots.autocomplete("action")
    async def bots_action_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name="طرد البوت", value="kick"),
            app_commands.Choice(name="حظر البوت", value="ban"),
            app_commands.Choice(name="إرسال تنبيه فقط", value="notify")
        ]

    # ==========================================
    # 📊 أمر عرض إعدادات الحماية
    # ==========================================
    @protection_group.command(name="status", description="📊 عرض حالة جميع أنظمة الحماية")
    async def protection_status(self, interaction: discord.Interaction):
        settings = self._get_guild_settings(interaction.guild.id)
        
        embed = discord.Embed(
            title="🛡️ حالة أنظمة الحماية",
            description="نظرة عامة على جميع أنظمة الحماية المفعّلة",
            color=Colors.INFO
        )
        
        # إنشاء قائمة بالإعدادات
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
        
        # إضافة تفاصيل إضافية
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
        
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Protection(bot))