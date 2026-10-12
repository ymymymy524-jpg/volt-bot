import discord
from discord import app_commands
from discord.ext import commands
from config import Colors

# ==========================================
# ❓ نظام المساعدة (Help System) - Prefix + Slash
# ==========================================

class HelpSelect(discord.ui.Select):
    def __init__(self):
        self.sections = {
            "general": {
                "emoji": "🛠️",
                "title": "🛠️ الأوامر العامة",
                "description": "أوامر المعلومات الأساسية والصور الشخصية",
                "commands": [
                    "`!ping` / `/ping` (`!p`, `!بنق`) - عرض سرعة استجابة البوت",
                    "`!avatar` / `/avatar` (`!av`, `!صورة`) - عرض صورة العضو",
                    "`!banner` / `/banner` (`!bn`) - عرض بانر العضو",
                    "`!user` / `/user` (`!u`, `!معلومات`) - عرض معلومات عضو",
                    "`!server` / `/server` (`!sv`) - عرض معلومات السيرفر",
                    "`!volt` / `/volt` (`!v`) - عرض رصيد Bitcoin"
                ]
            },
            "moderation": {
                "emoji": "👑",
                "title": "👑 الإدارة",
                "description": "أوامر إدارة الأعضاء والقنوات والرتب",
                "commands": [
                    "`!ban` / `/ban` (`!b`, `!حظر`) - حظر عضو",
                    "`!kick` / `/kick` (`!k`, `!طرد`) - طرد عضو",
                    "`!unban` / `/unban` (`!ub`) - فك الحظر",
                    "`!ban-all` / `/ban-all` - حظر شامل",
                    "`!warn add/list/clear` / `/warn` - الإنذارات",
                    "`!mute` / `/mute` (`!m`, `!كتم`) - كتم عضو",
                    "`!unmute` / `/unmute` (`!um`) - فك الكتم",
                    "`!timeout` / `/timeout` (`!to`) - توقيت عضو",
                    "`!clear` / `/clear` (`!c`, `!مسح`) - مسح الرسائل",
                    "`!slowmode` / `/slowmode` (`!sm`) - الوضع البطيء",
                    "`!lock` / `/lock` (`!l`, `!قفل`) - قفل القناة",
                    "`!unlock` / `/unlock` (`!ul`, `!فتح`) - فتح القناة",
                    "`!nick` / `/nick` (`!n`) - تغيير اللقب",
                    "`!move` / `/move` - نقل عضو",
                    "`!hide` / `/hide` - إخفاء القناة",
                    "`!unhide` / `/unhide` - إظهار القناة",
                    "`!voicemute` / `/voicemute` - كتم صوت",
                    "`!voicedeafen` / `/voicedeafen` - منع السماع"
                ]
            },
            "protection": {
                "emoji": "🛡️",
                "title": "🛡️ الحماية",
                "description": "أنظمة حماية السيرفر من السبام والاختراق",
                "commands": [
                    "`!protection auto on/off` / `/protection auto` - الحماية التلقائية",
                    "`!protection spam on/off` / `/protection spam` - حماية السبام",
                    "`!protection link on/off` / `/protection link` - حماية الروابط",
                    "`!protection join on/off` / `/protection join` - حماية الانضمام",
                    "`!protection hacked on/off` / `/protection hacked` - حماية المخترقة",
                    "`!protection bans on/off` / `/protection bans` - حماية الحظر الجماعي",
                    "`!protection kicks on/off` / `/protection kicks` - حماية الطرد الجماعي",
                    "`!protection channels on/off` / `/protection channels` - حماية القنوات",
                    "`!protection roles on/off` / `/protection roles` - حماية الرتب",
                    "`!protection bots on/off` / `/protection bots` - حماية البوتات",
                    "`!protection status` / `/protection status` - عرض الحالة"
                ]
            },
            "levels": {
                "emoji": "📊",
                "title": "📊 المستويات",
                "description": "نظام الخبرة والمستويات",
                "commands": [
                    "`!rank` / `/rank` (`!r`, `!مستوى`) - عرض مستوى العضو",
                    "`!top` / `/top` (`!t`, `!توب`) - لوحة المتصدرين",
                    "`!setlevel` / `/setlevel` (`!sl`) - تعيين مستوى (للإدارة)",
                    "`!resetlevel` / `/resetlevel` (`!rl`) - تصفير المستوى (للإدارة)"
                ]
            },
            "welcome": {
                "emoji": "👋",
                "title": "👋 الترحيب",
                "description": "إعداد رسائل الترحيب والمغادرة",
                "commands": [
                    "`!setwelcome` / `/setwelcome` (`!sw`) - تعيين قناة الترحيب",
                    "`!setgoodbye` / `/setgoodbye` (`!sg`) - تعيين قناة المغادرة",
                    "`!testwelcome` / `/testwelcome` (`!tw`) - اختبار رسالة الترحيب",
                    "`!welcome-set-status` / `/welcome-set-status` - تفعيل/تعطيل"
                ]
            },
            "music": {
                "emoji": "🎵",
                "title": "🎵 الموسيقى",
                "description": "تشغيل وإدارة الموسيقى",
                "commands": [
                    "`!play` / `/play` (`!p`) - تشغيل أغنية",
                    "`!pause` / `/pause` - إيقاف مؤقت",
                    "`!resume` / `/resume` (`!res`) - استئناف",
                    "`!skip` / `/skip` (`!s`) - تخطي الأغنية",
                    "`!stop` / `/stop` (`!st`) - إيقاف التشغيل",
                    "`!queue` / `/queue` (`!q`) - قائمة التشغيل",
                    "`!volume` / `/volume` (`!vol`) - مستوى الصوت",
                    "`!nowplaying` / `/nowplaying` (`!np`) - الأغنية الحالية",
                    "`!shuffle` / `/shuffle` (`!sh`) - خلط القائمة"
                ]
            },
            "invites": {
                "emoji": "📨",
                "title": "📨 الدعوات",
                "description": "تتبع دعوات الأعضاء",
                "commands": [
                    "`!invites` / `/invites` (`!inv`, `!دعوات`) - عرض دعواتك",
                    "`!inviter` / `/inviter` - مين دعاك؟",
                    "`!invitetop` / `/invitetop` (`!itop`) - أفضل الداعين",
                    "`!resetinvites` / `/resetinvites` (`!rinv`) - تصفير الدعوات"
                ]
            },
            "tickets": {
                "emoji": "🎫",
                "title": "🎫 التذاكر",
                "description": "نظام فتح وإدارة التذاكر",
                "commands": [
                    "`!ticket` / `/ticket` (`!t`, `!تذكرة`) - فتح تذكرة",
                    "`!close` / `/close` (`!cl`) - إغلاق التذكرة",
                    "`!add` / `/add` - إضافة عضو للتذكرة",
                    "`!remove` / `/remove` (`!rm`) - إزالة عضو",
                    "`!setticket` / `/setticket` - إعداد التذاكر"
                ]
            },
            "games": {
                "emoji": "🎮",
                "title": "🎮 الألعاب",
                "description": "ألعاب تفاعلية مع نظام Fizzy",
                "commands": [
                    "`!bomb` / `/bomb` - القنبلة",
                    "`!button` / `/button` - زر الحظ",
                    "`!chairs` / `/chairs` - الكراسي",
                    "`!colors` / `/colors` - الألوان",
                    "`!faster` / `/faster` - السرعة",
                    "`!flags` / `/flags` - الأعلام",
                    "`!mafia` / `/mafia` - المافيا",
                    "`!roulette` / `/roulette` - الروليت",
                    "`!fizzy` / `/fizzy` (`!fz`) - رصيد Fizzy",
                    "`!fizzytop` / `/fizzytop` (`!fzt`) - توب Fizzy"
                ]
            },
            "economy": {
                "emoji": "💎",
                "title": "💎 الاقتصاد",
                "description": "نظام Bitcoin والمتجر",
                "commands": [
                    "`!balance` / `/balance` (`!bal`, `!b`, `!رصيد`) - الرصيد",
                    "`!daily` / `/daily` (`!d`, `!يومي`) - المكافأة اليومية",
                    "`!work` / `/work` (`!w`, `!عمل`) - العمل",
                    "`!transfer` / `/transfer` (`!tr`) - تحويل",
                    "`!top` / `/top` (`!btop`) - الأثرياء",
                    "`!history` / `/history` (`!bh`) - السجل",
                    "`!shop` / `/shop` (`!متجر`) - المتجر",
                    "`!buy` / `/buy` - شراء",
                    "`!badmin add/remove/set/reset` - إدارة"
                ]
            },
            "ai": {
                "emoji": "🤖",
                "title": "🤖 الذكاء الاصطناعي",
                "description": "أوامر مدعومة بـ Google Gemini",
                "commands": [
                    "`!ask` / `/ask` (`!اسأل`) - طرح سؤال",
                    "`!imagine` / `/imagine` (`!تخيل`) - توليد وصف",
                    "`!translate` / `/translate` (`!ترجم`) - ترجمة",
                    "`!summarize` / `/summarize` (`!لخص`) - تلخيص",
                    "`!code` / `/code` (`!كود`) - مساعدة في الكود",
                    "`!story` / `/story` (`!قصة`) - كتابة قصة",
                    "`!analyze` / `/analyze` (`!حلل`) - تحليل"
                ]
            },
            "settings": {
                "emoji": "⚙️",
                "title": "⚙️ الإعدادات",
                "description": "إعدادات السيرفر المتقدمة",
                "commands": [
                    "`!setup` / `/setup` - الإعداد الأولي",
                    "`!add-emoji` / `/add-emoji` (`!ae`) - إضافة إيموجي",
                    "`!auto-message add/delete/list` - رسائل تلقائية",
                    "`!auto-reply add/delete/show` - ردود تلقائية",
                    "`!automod create/delete` - AutoMod",
                    "`!autorole` / `/autorole` - رتبة تلقائية",
                    "`!log set/stop` - السجلات",
                    "`!perms` / `/perms` (`!p`) - الصلاحيات",
                    "`!settings` / `/settings` (`!set`) - الإعدادات"
                ]
            }
        }

        options = [
            discord.SelectOption(
                label=data["title"].split(" ", 1)[1],
                value=key,
                emoji=data["emoji"],
                description=data["description"][:100]
            )
            for key, data in self.sections.items()
        ]

        super().__init__(
            placeholder="📂 اختر قسماً لعرض أوامره...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        section = self.sections[selected_key]

        embed = discord.Embed(
            title=section["title"],
            description=section["description"] + "\n\n**الأوامر المتاحة:**\n" + "\n".join(section["commands"]),
            color=Colors.INFO
        )
        embed.set_footer(text="استخدم /help أو !help للعودة للقائمة الرئيسية")
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpSelect())

    @discord.ui.button(label="🏠 القائمة الرئيسية", style=discord.ButtonStyle.secondary)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🤖 قائمة مساعدة البوت الشاملة",
            description=(
                "مرحباً بك! اختر قسماً من القائمة المنسدلة أدناه لعرض الأوامر التفصيلية الخاصة به.\n\n"
                "💡 **ملاحظة:** كل الأوامر تشتغل بـ `/` (Slash) و `!` (Prefix).\n"
                "🔹 الاختصارات (بين قوسين) تشتغل بـ Prefix فقط.\n"
                "⚠️ بعض الأوامر تتطلب صلاحيات إدارية محددة."
            ),
            color=Colors.GOLD
        )
        embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
        embed.set_footer(text="/help | !help | !h | !مساعدة")
        await interaction.response.edit_message(embed=embed, view=self)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_main_embed(self, user: discord.User = None) -> discord.Embed:
        """إنشاء الإيمبد الرئيسي لقائمة المساعدة"""
        embed = discord.Embed(
            title="🤖 قائمة مساعدة البوت الشاملة",
            description=(
                "مرحباً بك! اختر قسماً من القائمة المنسدلة أدناه لعرض الأوامر التفصيلية الخاصة به.\n\n"
                "💡 **ملاحظة:** كل الأوامر تشتغل بـ `/` (Slash) و `!` (Prefix).\n"
                "🔹 الاختصارات (بين قوسين) تشتغل بـ Prefix فقط.\n"
                "⚠️ بعض الأوامر تتطلب صلاحيات إدارية محددة."
            ),
            color=Colors.GOLD
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="/help | !help | !h | !مساعدة")
        if user:
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        return embed

    # ==========================================
    # 🔹 !help / /help
    # ==========================================
    @commands.hybrid_command(
        name="help",
        aliases=["h", "مساعدة", "اوامر", "الاوامر", "commands"],
        description="❓ عرض قائمة الأوامر والمساعدة"
    )
    async def help_prefix(self, ctx: commands.Context):
        """عرض قائمة المساعدة الرئيسية"""
        embed = self.get_main_embed(ctx.author)
        view = HelpView()
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Help(bot))