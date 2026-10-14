import discord
from discord.ext import commands
from discord import app_commands
import time
import os
import platform
import psutil
from datetime import datetime
from config import Colors

START_TIME = time.time()


class Utility(commands.Cog):
    """🧰 أوامر الأدوات والمعلومات"""

    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}  # {channel_id: {content, author, timestamp}}

    # ═══════════════════════════════════════
    # 🤖 botinfo
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="botinfo", aliases=["معلومات_البوت", "عن_البوت", "بوت"], description="🤖 معلومات البوت")
    async def botinfo(self, ctx: commands.Context):
        bot = self.bot
        uptime_seconds = int(time.time() - START_TIME)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        total_members = sum(g.member_count or 0 for g in bot.guilds)
        
        embed = discord.Embed(title=f"🤖 {bot.user.name}", color=Colors.INFO)
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        embed.add_field(name="🌐 السيرفرات", value=f"{len(bot.guilds):,}", inline=True)
        embed.add_field(name="👥 الأعضاء", value=f"{total_members:,}", inline=True)
        embed.add_field(name="⏱️ التشغيل", value=f"{hours}س {minutes}د", inline=True)
        embed.add_field(name="📚 discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="🧩 الأوامر", value=f"{len(list(bot.commands)):,}", inline=True)
        embed.add_field(name="📡 البنق", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.set_footer(text=f"ID: {bot.user.id}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📊 stats
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="stats", aliases=["احصائيات", "احصاءات"], description="📊 إحصائيات النظام")
    async def stats(self, ctx: commands.Context):
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            mem_used = mem.used / (1024 ** 2)
            mem_total = mem.total / (1024 ** 2)
        except:
            cpu = 0
            mem_used = 0
            mem_total = 0
        uptime_seconds = int(time.time() - START_TIME)
        
        embed = discord.Embed(title="📊 إحصائيات النظام", color=Colors.INFO)
        embed.add_field(name="🖥️ النظام", value=f"{platform.system()} • {platform.machine()}", inline=True)
        embed.add_field(name="⚙️ المعالج", value=f"{os.cpu_count()} أنوية", inline=True)
        embed.add_field(name="🔥 CPU", value=f"{cpu}%", inline=True)
        embed.add_field(name="🧠 الرام", value=f"{mem_used:.0f} / {mem_total:.0f} MB", inline=True)
        embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
        embed.add_field(name="⏱️ التشغيل", value=f"{uptime_seconds // 3600}س {(uptime_seconds % 3600) // 60}د", inline=True)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎭 roleinfo
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="roleinfo", aliases=["معلومات_رتبة", "رتبة_معلومات"], description="🎭 معلومات رتبة")
    @app_commands.describe(role="الرتبة")
    async def roleinfo(self, ctx: commands.Context, role: discord.Role):
        embed = discord.Embed(title=f"🎭 {role.name}", color=role.color or Colors.INFO)
        embed.add_field(name="🆔 ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="🎨 اللون", value=str(role.color), inline=True)
        embed.add_field(name="👥 الأعضاء", value=f"{len(role.members):,}", inline=True)
        embed.add_field(name="📌 الترتيب", value=f"{role.position}", inline=True)
        embed.add_field(name="📢 منشن", value="نعم" if role.mentionable else "لا", inline=True)
        embed.add_field(name="👁️ منفصلة", value="نعم" if role.hoist else "لا", inline=True)
        embed.add_field(name="📅 الإنشاء", value=discord.utils.format_dt(role.created_at, 'R'), inline=False)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📺 channelinfo
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="channelinfo", aliases=["معلومات_روم", "روم_معلومات"], description="📺 معلومات روم")
    @app_commands.describe(channel="الروم (اختياري)")
    async def channelinfo(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        embed = discord.Embed(title=f"📺 {channel.name}", color=Colors.INFO)
        embed.add_field(name="🆔 ID", value=f"`{channel.id}`", inline=True)
        embed.add_field(name="📂 النوع", value=str(channel.type), inline=True)
        embed.add_field(name="📅 الإنشاء", value=discord.utils.format_dt(channel.created_at, 'R'), inline=True)
        if channel.topic:
            embed.add_field(name="📝 الوصف", value=channel.topic[:1000], inline=False)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👥 members
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="members", aliases=["الاعضاء", "اعضاء"], description="👥 إحصائيات الأعضاء")
    async def members(self, ctx: commands.Context):
        g = ctx.guild
        humans = sum(1 for m in g.members if not m.bot)
        bots = sum(1 for m in g.members if m.bot)
        online = sum(1 for m in g.members if m.status != discord.Status.offline and not m.bot)
        in_voice = sum(1 for m in g.members if m.voice and m.voice.channel)
        
        embed = discord.Embed(title="👥 إحصائيات الأعضاء", color=Colors.INFO)
        embed.add_field(name="📊 الإجمالي", value=f"{g.member_count:,}", inline=True)
        embed.add_field(name="👤 بشر", value=f"{humans:,}", inline=True)
        embed.add_field(name="🤖 بوتات", value=f"{bots:,}", inline=True)
        embed.add_field(name="🟢 متصل", value=f"{online:,}", inline=True)
        embed.add_field(name="🎙️ في الصوت", value=f"{in_voice:,}", inline=True)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🕐 time
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="time", aliases=["الوقت", "الساعة"], description="🕐 الوقت والتاريخ")
    async def time_cmd(self, ctx: commands.Context):
        now = datetime.now()
        embed = discord.Embed(title="🕐 الوقت الآن", color=Colors.INFO)
        embed.description = f"{discord.utils.format_dt(now, 'F')}\n{discord.utils.format_dt(now, 'R')}"
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🧮 calc
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="calc", aliases=["حاسبة", "احسب"], description="🧮 آلة حاسبة")
    @app_commands.describe(expression="المعادلة (مثل 5*(3+2))")
    async def calc(self, ctx: commands.Context, *, expression: str):
        raw = expression.replace("×", "*").replace("÷", "/").replace("^", "**")
        if not all(c in "0123456789+-*/().% " for c in raw):
            await ctx.send("❌ معادلة غير صحيحة!")
            return
        try:
            result = eval(raw, {"__builtins__": {}}, {})
        except:
            await ctx.send("❌ ما قدرت أحسب!")
            return
        if not isinstance(result, (int, float)):
            await ctx.send("❌ معادلة غير صحيحة!")
            return
        embed = discord.Embed(title="🧮 الحاسبة", color=Colors.INFO)
        embed.add_field(name="المعادلة", value=f"`{expression}`", inline=False)
        embed.add_field(name="الناتج", value=f"`{result}`", inline=False)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📊 vote
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="vote", aliases=["تصويت", "استفتاء"], description="📊 تصويت")
    @commands.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(question="السؤال")
    async def vote(self, ctx: commands.Context, *, question: str):
        embed = discord.Embed(
            title="📊 تصويت جديد",
            description=f"## {question}\n\n✅ موافق\n❌ غير موافق",
            color=Colors.INFO
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        try:
            await ctx.message.delete()
        except:
            pass
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    # ═══════════════════════════════════════
    # ⏰ remind
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="remind", aliases=["تذكير", "ذكرني"], description="⏰ تذكير")
    @app_commands.describe(seconds="بعد كام ثانية؟", text="النص")
    async def remind(self, ctx: commands.Context, seconds: int, *, text: str):
        if seconds < 5 or seconds > 2592000:  # 30 يوم
            await ctx.send("❌ المدة من 5 ثواني لـ 30 يوم!")
            return
        await ctx.send(f"⏰ راح أذكرك بعد **{seconds}** ثانية!", delete_after=5)
        
        async def reminder():
            await asyncio.sleep(seconds)
            embed = discord.Embed(
                title="⏰ تذكير!",
                description=f"{ctx.author.mention} — {text}",
                color=Colors.WARNING
            )
            try:
                await ctx.send(embed=embed)
            except:
                pass
        
        import asyncio
        asyncio.create_task(reminder())

    # ═══════════════════════════════════════
    # 😀 emoji
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="emoji", aliases=["ايموجي", "كبر"], description="😀 تكبير إيموجي")
    @app_commands.describe(emoji="الإيموجي")
    async def emoji(self, ctx: commands.Context, emoji: str):
        import re
        match = re.match(r"<(a?):(\w+):(\d+)>", emoji)
        if not match:
            await ctx.send("❌ اكتب إيموجي مخصص من السيرفر!")
            return
        anim, name, eid = match.groups()
        url = f"https://cdn.discordapp.com/emojis/{eid}.{'gif' if anim else 'png'}?size=256"
        embed = discord.Embed(title=f"😀 {name}", color=Colors.INFO)
        embed.set_image(url=url)
        embed.description = f"[الرابط]({url})"
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔗 invite
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="invite", aliases=["الدعوة", "ضيف_البوت"], description="🔗 رابط الدعوة")
    async def invite(self, ctx: commands.Context):
        url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        embed = discord.Embed(
            title="🔗 دعوة البوت",
            description=f"[اضغط هنا لإضافة البوت]({url})",
            color=Colors.INFO
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎭 roles
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="roles", aliases=["الرتب", "قائمة_الرتب"], description="🎭 عرض رتب السيرفر")
    async def roles(self, ctx: commands.Context):
        roles = [r for r in ctx.guild.roles if r.name != "@everyone"]
        roles.sort(key=lambda r: r.position, reverse=True)
        if not roles:
            await ctx.send("📭 مفيش رتب!")
            return
        text = " ".join(r.mention for r in roles[:50])
        if len(text) > 4000:
            text = text[:3990] + "..."
        embed = discord.Embed(title=f"🎭 رتب السيرفر ({len(roles)})", description=text, color=Colors.INFO)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🖼️ servericon
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="servericon", aliases=["ايقونة_السيرفر"], description="🖼️ أيقونة السيرفر")
    async def servericon(self, ctx: commands.Context):
        if not ctx.guild.icon:
            await ctx.send("❌ السيرفر مفيش عنده أيقونة!")
            return
        embed = discord.Embed(title=f"🖼️ {ctx.guild.name}", color=Colors.INFO)
        embed.set_image(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👥 membercount
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="membercount", aliases=["عدد_الاعضاء"], description="👥 عدد الأعضاء")
    async def membercount(self, ctx: commands.Context):
        await ctx.send(f"👥 السيرفر فيه **{ctx.guild.member_count:,}** عضو")

    # ═══════════════════════════════════════
    # 🏓 ping2
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="ping2", aliases=["بنق2"], description="🏓 بنق متقدم")
    async def ping2(self, ctx: commands.Context):
        ws = round(self.bot.latency * 1000)
        start = time.time()
        msg = await ctx.send("🏓 جاري القياس...")
        msg_time = round((time.time() - start) * 1000)
        embed = discord.Embed(title="🏓 البنق", color=Colors.SUCCESS)
        embed.add_field(name="📡 WebSocket", value=f"`{ws}ms`", inline=True)
        embed.add_field(name="💬 الرسائل", value=f"`{msg_time}ms`", inline=True)
        await msg.edit(content=None, embed=embed)

    # ═══════════════════════════════════════
    # ⏱️ uptime
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="uptime", aliases=["مدة_التشغيل"], description="⏱️ وقت تشغيل البوت")
    async def uptime(self, ctx: commands.Context):
        seconds = int(time.time() - START_TIME)
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        embed = discord.Embed(
            title="⏱️ وقت التشغيل",
            description=f"**{days}** يوم، **{hours}** ساعة، **{minutes}** دقيقة، **{secs}** ثانية",
            color=Colors.INFO
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔍 snipe
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        self.snipes[message.channel.id] = {
            "content": message.content,
            "author": str(message.author),
            "author_avatar": message.author.display_avatar.url,
            "timestamp": datetime.now()
        }

    @commands.hybrid_command(name="snipe", aliases=["اخر_رسالة"], description="🔍 آخر رسالة محذوفة")
    @commands.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    async def snipe(self, ctx: commands.Context):
        snipe = self.snipes.get(ctx.channel.id)
        if not snipe:
            await ctx.send("❌ مفيش رسائل محذوفة!")
            return
        embed = discord.Embed(description=snipe["content"], color=Colors.INFO, timestamp=snipe["timestamp"])
        embed.set_author(name=snipe["author"], icon_url=snipe["author_avatar"])
        embed.set_footer(text=f"#{ctx.channel.name}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))