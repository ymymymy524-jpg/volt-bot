import discord
from discord import app_commands
from discord.ext import commands
from config import Colors

# ==========================================
# ❓ نظام المساعدة (Help System)
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
                    "`/ping` - عرض سرعة استجابة البوت",
                    "`/avatar user/server` - عرض صورة العضو أو السيرفر",
                    "`/banner user/server` - عرض بانر العضو أو السيرفر",
                    "`/user` - عرض معلومات تفصيلية عن عضو",
                    "`/server` - عرض معلومات وإحصائيات السيرفر",
                    "`/daily` - استلام الرصيد اليومي",
                    "`/rank` - عرض مستوى العضو وتقدمه",
                    "`/top` - عرض أفضل 10 أعضاء في المستويات",
                    "`/volt` - عرض أو تعديل رصيد Bitcoin"
                ]
            },
            "moderation": {
                "emoji": "👑",
                "title": "👑 الإدارة",
                "description": "أوامر إدارة الأعضاء والقنوات والرتب",
                "commands": [
                    "`/ban, /kick, /unban, /ban-all` - إدارة الحظر والطرد",
                    "`/warn, /warnings` - إدارة الإنذارات",
                    "`/mute, /unmute, /timeout` - كتم أو توقيت العضو",
                    "`/clear, /slowmode, /lock, /unlock` - إدارة القنوات",
                    "`/nick, /role, /role-all` - إدارة الأسماء والرتب"
                ]
            },
            "protection": {
                "emoji": "🛡️",
                "title": "🛡️ الحماية",
                "description": "أنظمة حماية السيرفر من السبام والاختراق",
                "commands": [
                    "`/protection auto` - تفعيل/تعطيل الحماية التلقائية",
                    "`/protection spam` - حماية من السبام",
                    "`/protection link` - حماية من روابط التشهير",
                    "`/protection join` - حماية من انضمام الحسابات الجديدة",
                    "`/protection hacked, bans, kicks, channels, roles, bots`"
                ]
            },
            "levels": {
                "emoji": "📊",
                "title": "📊 المستويات",
                "description": "نظام الخبرة والمستويات وتخصيص المكافآت",
                "commands": [
                    "`/rank` - عرض مستوى العضو",
                    "`/top` - عرض لوحة المتصدرين",
                    "`/setlevel, /resetlevel` - إدارة المستويات (للإدارة)"
                ]
            },
            "welcome": {
                "emoji": "👋",
                "title": "👋 الترحيب",
                "description": "إعداد رسائل الترحيب والمغادرة",
                "commands": [
                    "`/setwelcome` - تعيين قناة ورسالة الترحيب",
                    "`/setgoodbye` - تعيين قناة ورسالة المغادرة",
                    "`/testwelcome` - اختبار رسالة الترحيب",
                    "`/welcome-set-status` - تفعيل أو تعطيل نظام الترحيب"
                ]
            },
            "music": {
                "emoji": "🎵",
                "title": "🎵 الموسيقى",
                "description": "تشغيل وإدارة الموسيقى في القنوات الصوتية",
                "commands": [
                    "`/play` - تشغيل أغنية أو إضافة للقائمة",
                    "`/pause, /resume` - إيقاف مؤقت أو استئناف",
                    "`/skip, /stop` - تخطي الأغنية أو إيقاف التشغيل",
                    "`/queue, /volume, /nowplaying` - إدارة قائمة التشغيل والصوت"
                ]
            },
            "invites": {
                "emoji": "📨",
                "title": "📨 الدعوات",
                "description": "تتبع دعوات الأعضاء وإحصائياتها",
                "commands": [
                    "`/invites` - عرض عدد دعواتك",
                    "`/inviter` - معرفة من قام بدعوتك",
                    "`/invitetop` - عرض أفضل الأعضاء في الدعوات",
                    "`/resetinvites` - تصفير دعوات عضو (للإدارة)"
                ]
            },
            "tickets": {
                "emoji": "🎫",
                "title": "🎫 التذاكر",
                "description": "نظام فتح وإدارة تذاكر الدعم الفني",
                "commands": [
                    "`/ticket` - فتح تذكرة دعم جديدة",
                    "`/close` - إغلاق التذكرة الحالية",
                    "`/add, /remove` - إضافة أو إزالة أعضاء من التذكرة",
                    "`/setticket` - إعداد قناة ورسالة نظام التذاكر"
                ]
            },
            "games": {
                "emoji": "🎮",
                "title": "🎮 الألعاب",
                "description": "ألعاب تفاعلية جماعية وسريعة مع نظام Fizzy",
                "commands": [
                    "`/game bomb, button, chairs, colors, faster, flags, mafia, roulette`",
                    "`/fizzy` - عرض رصيد Fizzy الخاص بك",
                    "`/fizzytop` - عرض أفضل 10 لاعبين في Fizzy"
                ]
            },
            "economy": {
                "emoji": "💎",
                "title": "💎 الاقتصاد",
                "description": "نظام Bitcoin، العمل، التحويل، والمتجر",
                "commands": [
                    "`/balance` - عرض رصيدك أو رصيد عضو آخر",
                    "`/daily, /work` - طرق كسب الـ Bitcoin",
                    "`/transfer` - تحويل الرصيد لعضو آخر",
                    "`/bitcoin-top, /bitcoin-history, /bitcoin-shop, /buy, /bitcoin-admin`"
                ]
            },
            "ai": {
                "emoji": "🤖",
                "title": "🤖 الذكاء الاصطناعي",
                "description": "أوامر مدعومة بـ Google Gemini AI",
                "commands": [
                    "`/ai ask` - طرح سؤال للذكاء الاصطناعي",
                    "`/ai imagine` - توليد وصف أو فكرة",
                    "`/ai translate` - ترجمة النصوص",
                    "`/ai summarize` - تلخيص النصوص الطويلة",
                    "`/ai code, /ai story, /ai analyze`"
                ]
            },
            "settings": {
                "emoji": "⚙️",
                "title": "⚙️ الإعدادات",
                "description": "إعدادات السيرفر المتقدمة والتخصيص",
                "commands": [
                    "`/add-emoji, /auto-message, /auto-reply, /automod`",
                    "`/autorole, /change-log, /command-disable`",
                    "`/level-up-msg, /log, /perms, /role-icon, /self-roles`",
                    "`/embed, /server, /settings, /setup, /shorts, /end-premium`"
                ]
            }
        }

        options = [
            discord.SelectOption(
                label=data["title"].split(" ", 1)[1], # إزالة الإيموجي من الاسم للعرض النظيف
                value=key,
                emoji=data["emoji"],
                description=data["description"][:100] # وصف مختصر للقائمة المنسدلة
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
        embed.set_footer(text="استخدم /help للعودة للقائمة الرئيسية")
        
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpSelect())
        
        # زر للعودة للقائمة الرئيسية
        @discord.ui.button(label="🏠 القائمة الرئيسية", style=discord.ButtonStyle.secondary)
        async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = discord.Embed(
                title="🤖 قائمة مساعدة البوت الشاملة",
                description="مرحباً بك! اختر قسماً من القائمة المنسدلة أدناه لعرض الأوامر التفصيلية الخاصة به.\n\n"
                            "💡 **ملاحظة:** جميع الأوامر هي Slash Commands (تبدأ بـ `/`).\n"
                            "⚠️ بعض الأوامر تتطلب صلاحيات إدارية محددة.",
                color=Colors.GOLD
            )
            embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
            await interaction.response.edit_message(embed=embed, view=self)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def show_help(self, interaction: discord.Interaction):
        """دالة لعرض قائمة المساعدة الرئيسية، يمكن استدعاؤها من cog آخر"""
        embed = discord.Embed(
            title="🤖 قائمة مساعدة البوت الشاملة",
            description="مرحباً بك! اختر قسماً من القائمة المنسدلة أدناه لعرض الأوامر التفصيلية الخاصة به.\n\n"
                        "💡 **ملاحظة:** جميع الأوامر هي Slash Commands (تبدأ بـ `/`).\n"
                        "⚠️ بعض الأوامر تتطلب صلاحيات إدارية محددة.",
            color=Colors.GOLD
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="help", description="❓ عرض قائمة الأوامر والمساعدة")
    async def help_command(self, interaction: discord.Interaction):
        await self.show_help(interaction)


async def setup(bot):
    await bot.add_cog(Help(bot))