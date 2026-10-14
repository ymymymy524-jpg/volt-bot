import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import aiohttp
from config import Colors

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
        gid = str(guild_id)
        if gid not in self.data:
            self.data[gid] = {
                "prefix": "!",
                "welcome_channel": None,
                "goodbye_channel": None,
                "welcome_message": "أهلاً {user} في {server}!",
                "auto_messages": [],
                "auto_replies": [],
                "automod_rules": [],
                "autorole": None,
                "tempvoice_creator": None,
                "auto_line_channels": [],
                "auto_line_image": None,
                "log_channel": None,
                "level_up_msg": None,
                "disabled_commands": [],
                "self_roles": [],
                "premium_end": None
            }
        # ترقية البيانات
        gd = self.data[gid]
        gd.setdefault("prefix", "!")
        gd.setdefault("welcome_message", "أهلاً {user} في {server}!")
        gd.setdefault("tempvoice_creator", None)
        gd.setdefault("auto_line_channels", [])
        gd.setdefault("auto_line_image", None)
        return gd

    def save(self):
        save_data(self.data)

    # ═══════════════════════════════════════
    # 🔣 prefix
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="prefix", aliases=["بريفكس", "بادئة"], description="🔣 تغيير البريفكس")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(prefix="البريفكس الجديد أو 'بدون'")
    async def prefix(self, ctx: commands.Context, prefix: str = None):
        gd = self.get_guild_data(ctx.guild.id)
        if not prefix:
            await ctx.send(f"🔣 البريفكس الحالي: `{gd.get('prefix') or 'بدون'}`")
            return
        new_prefix = "" if prefix == "بدون" else prefix[:3]
        gd["prefix"] = new_prefix
        self.save()
        if new_prefix:
            await ctx.send(f"✅ البريفكس الجديد: `{new_prefix}`")
        else:
            await ctx.send("✅ تم إلغاء البريفكس — الأوامر تشتغل بدون رمز")

    # ═══════════════════════════════════════
    # 👋 setwelcomech
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="setwelcomech", aliases=["ترحيب_اعداد", "اعداد_ترحيب"], description="👋 روم الترحيب")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="الروم أو 'حذف'")
    async def setwelcomech(self, ctx: commands.Context, channel: str):
        gd = self.get_guild_data(ctx.guild.id)
        if channel.lower() in ["حذف", "الغاء", "ايقاف"]:
            gd["welcome_channel"] = None
            self.save()
            await ctx.send("✅ تم إلغاء روم الترحيب")
            return
        ch = None
        if ctx.message.channel_mentions:
            ch = ctx.message.channel_mentions[0]
        elif channel.isdigit():
            ch = ctx.guild.get_channel(int(channel))
        if not ch or not isinstance(ch, discord.TextChannel):
            await ctx.send("❌ منشن روم كتابي أو `حذف`")
            return
        gd["welcome_channel"] = ch.id
        self.save()
        await ctx.send(f"✅ روم الترحيب: {ch.mention}")

    # ═══════════════════════════════════════
    # 🚪 setgoodbyech
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="setgoodbyech", aliases=["خروج_اعداد", "اعداد_مغادرة"], description="🚪 روم المغادرة")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="الروم أو 'حذف'")
    async def setgoodbyech(self, ctx: commands.Context, channel: str):
        gd = self.get_guild_data(ctx.guild.id)
        if channel.lower() in ["حذف", "الغاء", "ايقاف"]:
            gd["goodbye_channel"] = None
            self.save()
            await ctx.send("✅ تم إلغاء روم المغادرة")
            return
        ch = None
        if ctx.message.channel_mentions:
            ch = ctx.message.channel_mentions[0]
        elif channel.isdigit():
            ch = ctx.guild.get_channel(int(channel))
        if not ch or not isinstance(ch, discord.TextChannel):
            await ctx.send("❌ منشن روم كتابي أو `حذف`")
            return
        gd["goodbye_channel"] = ch.id
        self.save()
        await ctx.send(f"✅ روم المغادرة: {ch.mention}")

    # ═══════════════════════════════════════
    # ✏️ welcomemsg
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="welcomemsg", aliases=["ترحيب_رسالة", "رسالة_ترحيب"], description="✏️ رسالة الترحيب")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(text="النص ({user} {name} {server} {count})")
    async def welcomemsg(self, ctx: commands.Context, *, text: str):
        gd = self.get_guild_data(ctx.guild.id)
        gd["welcome_message"] = text[:800]
        self.save()
        # معاينة
        preview = text.replace("{user}", ctx.author.mention)
        preview = preview.replace("{name}", ctx.author.display_name)
        preview = preview.replace("{server}", ctx.guild.name)
        preview = preview.replace("{count}", str(ctx.guild.member_count))
        embed = discord.Embed(
            title="✅ تم الحفظ — معاينة",
            description=preview,
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👋 testwelcome
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="testwelcome", aliases=["تجربة_ترحيب", "ترحيب_تجربة"], description="👋 تجربة الترحيب")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def testwelcome(self, ctx: commands.Context):
        gd = self.get_guild_data(ctx.guild.id)
        msg = gd.get("welcome_message", "أهلاً {user} في {server}!")
        preview = msg.replace("{user}", ctx.author.mention)
        preview = preview.replace("{name}", ctx.author.display_name)
        preview = preview.replace("{server}", ctx.guild.name)
        preview = preview.replace("{count}", str(ctx.guild.member_count))
        embed = discord.Embed(
            title="👋 ترحيب تجريبي",
            description=preview,
            color=Colors.SUCCESS,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎭 autorole
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="autorole", aliases=["رتبة_تلقائية", "رتبة_الدخول"], description="🎭 رتبة تلقائية")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(role="الرتبة أو 'حذف'")
    async def autorole(self, ctx: commands.Context, role: str):
        gd = self.get_guild_data(ctx.guild.id)
        if role.lower() in ["حذف", "الغاء", "ايقاف"]:
            gd["autorole"] = None
            self.save()
            await ctx.send("✅ تم إلغاء الرتبة التلقائية")
            return
        r = None
        if ctx.message.role_mentions:
            r = ctx.message.role_mentions[0]
        elif role.isdigit():
            r = ctx.guild.get_role(int(role))
        if not r:
            await ctx.send("❌ منشن الرتبة أو اكتب اسمها!")
            return
        if r.position >= ctx.guild.me.top_role.position:
            await ctx.send("❌ الرتبة أعلى من رتبة البوت!")
            return
        gd["autorole"] = r.id
        self.save()
        await ctx.send(f"✅ الأعضاء الجدد هياخدوا {r.mention}")

    # ═══════════════════════════════════════
    # 🎙️ tempvoice
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="tempvoice", aliases=["روم_مؤقت_اعداد"], description="🎙️ روم الرومات المؤقتة")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="الروم الصوتي أو 'حذف'")
    async def tempvoice(self, ctx: commands.Context, channel: str):
        gd = self.get_guild_data(ctx.guild.id)
        if channel.lower() in ["حذف", "الغاء", "ايقاف"]:
            gd["tempvoice_creator"] = None
            self.save()
            await ctx.send("✅ تم إلغاء نظام الرومات المؤقتة")
            return
        ch = None
        if ctx.message.channel_mentions:
            ch = ctx.message.channel_mentions[0]
        elif channel.isdigit():
            ch = ctx.guild.get_channel(int(channel))
        if not ch or not isinstance(ch, discord.VoiceChannel):
            await ctx.send("❌ منشن روم صوتي أو `حذف`")
            return
        gd["tempvoice_creator"] = ch.id
        self.save()
        await ctx.send(f"✅ أي عضو يدخل {ch.mention} ينفتح له روم صوتي خاص فيه")

    # ═══════════════════════════════════════
    # 📏 autoline
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="autoline", aliases=["خط_اعداد", "خط_تلقائي"], description="📏 الخط التلقائي")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="الروم (اختياري)")
    async def autoline(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gd = self.get_guild_data(ctx.guild.id)
        lines = gd.get("auto_line_channels", [])
        if channel.id in lines:
            lines.remove(channel.id)
            msg = f"❌ تم إلغاء الخط من {channel.mention}"
        else:
            lines.append(channel.id)
            msg = f"✅ تم تفعيل الخط في {channel.mention}"
        gd["auto_line_channels"] = lines
        self.save()
        await ctx.send(msg)

    # ═══════════════════════════════════════
    # 🖼️ autolineimg
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="autolineimg", aliases=["خط_صورة", "صورة_الخط"], description="🖼️ صورة الخط")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(url="رابط الصورة")
    async def autolineimg(self, ctx: commands.Context, url: str = None):
        if not url and ctx.message.attachments:
            url = ctx.message.attachments[0].url
        if not url or not url.startswith("http"):
            await ctx.send("❌ رابط صورة صحيح!")
            return
        gd = self.get_guild_data(ctx.guild.id)
        gd["auto_line_image"] = url
        self.save()
        embed = discord.Embed(title="✅ تم حفظ صورة الخط", color=Colors.SUCCESS)
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💬 addreply
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="addreply", aliases=["رد_اضافة", "اضافة_رد"], description="💬 إضافة رد تلقائي")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(trigger="الكلمة", response="الرد")
    async def addreply(self, ctx: commands.Context, trigger: str, *, response: str):
        gd = self.get_guild_data(ctx.guild.id)
        replies = gd.get("auto_replies", [])
        if len(replies) >= 50:
            await ctx.send("❌ وصلت الحد الأقصى 50 رد!")
            return
        replies = [r for r in replies if r.get("trigger") != trigger.lower()]
        replies.append({"trigger": trigger.lower(), "response": response[:1500]})
        gd["auto_replies"] = replies
        self.save()
        await ctx.send(f"✅ إذا كتب أحد **{trigger}** هرد عليه")

    # ═══════════════════════════════════════
    # 🗑️ delreply
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="delreply", aliases=["رد_حذف", "حذف_رد"], description="🗑️ حذف رد تلقائي")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(trigger="الكلمة")
    async def delreply(self, ctx: commands.Context, *, trigger: str):
        gd = self.get_guild_data(ctx.guild.id)
        replies = gd.get("auto_replies", [])
        before = len(replies)
        replies = [r for r in replies if r.get("trigger") != trigger.lower()]
        if len(replies) == before:
            await ctx.send("❌ ما لقيت رد بهذه الكلمة!")
            return
        gd["auto_replies"] = replies
        self.save()
        await ctx.send("✅ تم الحذف")

    # ═══════════════════════════════════════
    # 📋 replies
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="replies", aliases=["الردود", "قائمة_الردود"], description="📋 عرض الردود")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    async def replies(self, ctx: commands.Context):
        gd = self.get_guild_data(ctx.guild.id)
        replies = gd.get("auto_replies", [])
        if not replies:
            await ctx.send("📭 مفيش ردود مسجلة!")
            return
        lines = [f"**{i+1}.** `{r['trigger']}` ← {r['response'][:60]}" for i, r in enumerate(replies)]
        text = "\n".join(lines[:30])
        embed = discord.Embed(
            title=f"🤖 الردود التلقائية ({len(replies)})",
            description=text,
            color=Colors.INFO
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📨 Event: ردود تلقائية
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        gd = self.get_guild_data(message.guild.id)
        content = message.content.lower().strip()
        for reply in gd.get("auto_replies", []):
            if reply.get("trigger") == content:
                try:
                    await message.channel.send(reply["response"])
                except:
                    pass
                return

    # ═══════════════════════════════════════
    # 👋 Event: ترحيب
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_join(self, member):
        gd = self.get_guild_data(member.guild.id)
        # Autorole
        role_id = gd.get("autorole")
        if role_id:
            role = member.guild.get_role(int(role_id))
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass
        # Welcome message
        ch_id = gd.get("welcome_channel")
        if ch_id:
            ch = member.guild.get_channel(int(ch_id))
            if ch:
                msg = gd.get("welcome_message", "أهلاً {user} في {server}!")
                msg = msg.replace("{user}", member.mention)
                msg = msg.replace("{name}", member.display_name)
                msg = msg.replace("{server}", member.guild.name)
                msg = msg.replace("{count}", str(member.guild.member_count))
                try:
                    await ch.send(msg)
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        gd = self.get_guild_data(member.guild.id)
        ch_id = gd.get("goodbye_channel")
        if ch_id:
            ch = member.guild.get_channel(int(ch_id))
            if ch:
                try:
                    await ch.send(f"👋 مع السلامة **{member.display_name}**")
                except:
                    pass

    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت مفيش عنده الصلاحيات!")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي القناة!")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ مش لاقي الرتبة!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Settings(bot))