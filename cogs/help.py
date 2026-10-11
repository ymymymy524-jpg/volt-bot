import discord
from discord.ext import commands
from config import Colors

# ==========================================
# ❓ نظام المساعدة (Help System) - Prefix !
# ==========================================

class HelpSelect(discord.ui.Select):
    def __init__(self):
        # تعريف الأقسام الـ 12 المطلوبة
        self.sections = {
            "general": {
                "emoji": "🛠️",
                "title": "🛠️ الأوامر العامة",
                "description": "أوامر المعلومات الأساسية والصور الشخصية",
                "commands": [
                    "`!ping` (`!p`) - عرض سرعة استجابة البوت",
                    "`!avatar` (`!av`, `!صورة`) - عرض صورة العضو أو السيرفر",
                    "`!banner` (`!bn`) - عرض بانر العضو أو السيرفر",
                    "`!user` (`!u`, `!معلومات`) - عرض معلومات تفصيلية عن عضو",
                    "`!server` (`!sv`) - عرض معلومات وإحصائيات السيرفر",
                    "`!daily` (`!d`, `!يومي`) - استلام الرصيد اليومي",
                    "`!rank` (`!r`, `!مستوى`) - عرض مستوى العضو وتقدمه",
                    "`!top` (`!t`, `!توب`) - عرض أفضل 10 أعضاء في المستويات",
                    "`!volt` (`!v`) - عرض أو تعديل رصيد Bitcoin"
                ]
            },
            "moderation": {
                "emoji": "👑",
                "title": "👑 الإدارة",
                "description": "أوامر إدارة الأعضاء والقنوات والرتب",
                "commands": [
                    "`!ban` (`!b`, `!حظر`) - حظر عضو",
                    "`!kick` (`!k`, `!طرد`) - طرد عضو",
                    "`!unban` (`!ub`) - فك الحظر",
                    "`!ban-all` - حظر شامل",
                    "`!warn` (`!w`, `!انذار`) - إنذار عضو",
                    "`!warnings` (`!ws`) - عرض إنذارات عضو",
                    "`!mute` (`!m`, `!كتم`) - كتم عضو",
                    "`!unmute` (`!um`) - فك الكتم",
                    "`!timeout` (`!to`) - توقيت عضو",
                    "`!clear` (`!c`, `!مسح`) - مسح الرسائل",
                    "`!slowmode` (`!sm`) - الوضع البطيء",
                    "`!lock` (`!l`, `!قفل`) - قفل القناة",
                    "`!unlock` (`!ul`, `!فتح`) - فتح القناة",
                    "`!nick` (`!n`) - تغيير اللقب",
                    "`!role` (`!rl`) - إدارة الرتب",
                    "`!role-all` - إعطاء رتبة للجميع"
                ]
            },
            "protection": {
                "emoji": "🛡️",
                "title": "🛡️ الحماية",
                "description": "أنظمة حماية السيرفر من السبام والاختراق",
                "commands": [
                    "`!protection auto` (`!حماية auto`) - تفعيل/تعطيل الحماية",
                    "`!protection spam` - حماية من السبام",
                    "`!protection link` - حماية من روابط التشهير",
                    "`!protection join` - حماية من الحسابات الجديدة",
                    "`!protection hacked` - حماية من الاختراق",
                    "`!protection bans, kicks, channels, roles, bots`"
                ]
            },
            "levels": {
                "emoji": "📊",
                "title": "📊 المستويات",
                "description": "نظام الخبرة والمستويات وتخصيص المكافآت",
                "commands": [
                    "`!rank` (`!r`, `!مستوى`) - عرض مستوى العضو",
                    "`!top` (`!t`, `!توب`) - عرض لوحة المتصدرين",
                    "`!setlevel` (`!sl`) - تعيين مستوى (للإدارة)",
                    "`!resetlevel` (`!rl`) - تصفير المستوى (للإدارة)"
                ]
            },
            "welcome": {
                "emoji": "👋",
                "title": "👋 الترحيب",
                "description": "إعداد رسائل الترحيب والمغادرة",
                "commands": [
                    "`!setwelcome` (`!sw`) - تعيين قناة ورسالة الترحيب",
                    "`!setgoodbye` (`!sg`) - تعيين قناة ورسالة المغادرة",
                    "`!testwelcome` (`!tw`) - اختبار رسالة الترحيب",
                    "`!welcome-set-status` (`!wss`) - تفعيل/تعطيل الترحيب"
                ]
            },
            "music": {
                "emoji": "🎵",
                "title": "🎵 الموسيقى",
                "description": "تشغيل وإدارة الموسيقى في القنوات الصوتية",
                "commands": [
                    "`!play` (`!p`) - تشغيل أغنية أو إضافة للقائمة",
                    "`!pause` - إيقاف مؤقت",
                    "`!resume` (`!res`) - استئناف",
                    "`!skip` (`!s`) - تخطي الأغنية",
                    "`!stop` (`!st`) - إيقاف التشغيل",
                    "`!queue` (`!q`) - قائمة التشغيل",
                    "`!volume` (`!vol`) - مستوى الصوت",
                    "`!nowplaying` (`!np`) - الأغنية الحالية"
                ]
            },
            "invites": {
                "emoji": "📨",
                "title": "📨 الدعوات",
                "description": "تتبع دعوات الأعضاء وإحصائياتها",
                "commands": [
                    "`!invites` (`!inv`, `!دعوات`) - عرض عدد دعواتك",
                    "`!inviter` - معرفة من قام بدعوتك",
                    "`!invitetop` (`!itop`) - أفضل الأعضاء في الدعوات",
                    "`!resetinvites` (`!rinv`) - تصفير دعوات عضو"
                ]
            },
            "tickets": {
                "emoji": "🎫",
                "title": "🎫 التذاكر",
                "description": "نظام فتح وإدارة تذاكر الدعم الفني",
                "commands": [
                    "`!ticket` (`!t`, `!تذكرة`) - فتح تذكرة دعم",
                    "`!close` (`!cl`) - إغلاق التذكرة الحالية",
                    "`!add` - إضافة عضو للتذكرة",
                    "`!remove` (`!rm`) - إزالة عضو من التذكرة",
                    "`!setticket` - إعداد نظام التذاكر"
                ]
            },
            "games": {
                "emoji": "🎮",
                "title": "🎮 الألعاب",
                "description": "ألعاب تفاعلية جماعية وسريعة مع نظام Fizzy",
                "commands": [
                    "`!game bomb` (`!bomb`) - لعبة القنبلة",
                    "`!game button` (`!button`) - لعبة الأزرار",
                    "`!game chairs` - لعبة الكراسي",
                    "`!game colors` (`!colors`) - لعبة الألوان",
                    "`!game faster` (`!faster`) - لعبة السرعة",
                    "`!game flags` (`!flags`) - لعبة الأعلام",
                    "`!game mafia` (`!mafia`) - لعبة المافيا",
                    "`!game roulette` (`!roulette`) - الروليت",
                    "`!fizzy` (`!fz`) - رصيد Fizzy",
                    "`!fizzytop` (`!fzt`) - أفضل 10 لاعبين Fizzy"
                ]
            },
            "economy": {
                "emoji": "💎",
                "title": "💎 الاقتصاد",
                "description": "نظام Bitcoin، العمل، التحويل، والمتجر",
                "commands": [
                    "`!balance` (`!bal`, `!b`, `!رصيد`) - عرض الرصيد",
                    "`!daily` (`!d`, `!يومي`) - الرصيد اليومي",
                    "`!work` (`!w`, `!عمل`) - العمل لكسب Bitcoin",
                    "`!transfer` (`!tr`) - تحويل الرصيد",
                    "`!bitcoin-top` (`!btop`) - أفضل الأثرياء",
                    "`!bitcoin-history` (`!bh`) - سجل المعاملات",
                    "`!bitcoin-shop` (`!shop`, `!متجر`) - المتجر",
                    "`!buy` - شراء من المتجر",
                    "`!bitcoin-admin` (`!badmin`) - إدارة الاقتصاد"
                ]
            },
            "ai": {
                "emoji": "🤖",
                "title": "🤖 الذكاء الاصطناعي",
                "description": "أوامر مدعومة بـ Google Gemini AI",
                "commands": [
                    "`!ai ask` (`!ai سؤال`) - طرح سؤال للـ AI",
                    "`!ai imagine` (`!ai تخيل`) - توليد وصف أو فكرة",
                    "`!ai translate` (`!ai ترجم`) - ترجمة النصوص",
                    "`!ai summarize` (`!ai لخص`) - تلخيص النصوص",
                    "`!ai code` - مساعدة في الكود",
                    "`!ai story` - كتابة قصة",
                    "`!ai analyze` - تحليل نص"
                ]
            },
            "settings": {
                "emoji": "⚙️",
                "title": "⚙️ الإعدادات",
                "description": "إعدادات السيرفر المتقدمة والتخصيص",
                "commands": [
                    "`!add-emoji` (`!ae`) - إضافة إيموجي",
                    "`!auto-message` (`!am`) - رسائل تلقائية",
                    "`!auto-reply` (`!ar`) - ردود تلقائية",
                    "`!automod` - الإشراف التلقائي",
                    "`!autorole` - رتبة تلقائية",
                    "`!change-log` (`!clog`) - سجل التغييرات",
                    "`!command-disable` (`!cd`) - تعطيل أمر",
                    "`!level-up-msg` (`!lum`) - رسالة ترقية",
                    "`!log` - إعداد السجلات",
                    "`!perms` (`!p`) - الصلاحيات",
                    "`!role-icon` - أيقونة الرتبة",
                    "`!self-roles` (`!sr`) - رتب ذاتية",
                    "`!embed` - إنشاء Embed",
                    "`!settings` (`!set`) - الإعدادات العامة",
                    "`!setup` - الإعداد الأولي",
                    "`!end-premium` - إنهاء البريميوم"
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
        embed.set_footer(text="استخدم !help للعودة للقائمة الرئيسية")
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpSelect())

    @discord.ui.button(label="🏠 القائمة الرئيسية", style=discord.ButtonStyle.secondary)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🤖 قائمة مساعدة البوت الشاملة",
            description="مرحباً بك! اختر قسماً من القائمة المنسدلة أدناه لعرض الأوامر التفصيلية الخاصة به.\n\n"
                        "💡 **ملاحظة:** جميع الأوامر تبدأ بـ `!` (Prefix Commands).\n"
                        "🔹 بعض الأوامر لها اختصارات قصيرة (مكتوبة بين قوسين).\n"
                        "⚠️ بعض الأوامر تتطلب صلاحيات إدارية محددة.",
            color=Colors.GOLD
        )
        embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
        embed.set_footer(text="!help | !h | !مساعدة")
        await interaction.response.edit_message(embed=embed, view=self)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_main_embed(self, user: discord.User = None) -> discord.Embed:
        """إنشاء الإيمبد الرئيسي لقائمة المساعدة"""
        embed = discord.Embed(
            title="🤖 قائمة مساعدة البوت الشاملة",
            description="مرحباً بك! اختر قسماً من القائمة المنسدلة أدناه لعرض الأوامر التفصيلية الخاصة به.\n\n"
                        "💡 **ملاحظة:** جميع الأوامر تبدأ بـ `!` (Prefix Commands).\n"
                        "🔹 بعض الأوامر لها اختصارات قصيرة (مكتوبة بين قوسين).\n"
                        "⚠️ بعض الأوامر تتطلب صلاحيات إدارية محددة.",
            color=Colors.GOLD
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="!help | !h | !مساعدة")
        if user:
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        return embed

    # ==========================================
    # 🔹 أمر المساعدة بالبادئة !
    # ==========================================
    @commands.command(
        name="help",
        aliases=["h", "مساعدة", "اوامر", "الاوامر", "?", "commands"],
        description="❓ عرض قائمة الأوامر والمساعدة"
    )
    async def help_prefix(self, ctx: commands.Context):
        """عرض قائمة المساعدة الرئيسية"""
        embed = self.get_main_embed(ctx.author)
        view = HelpView()
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Help(bot))