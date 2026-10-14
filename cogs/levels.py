import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import time
from config import Colors

LEVELS_FILE = "levels.json"


def load_data():
    if os.path.exists(LEVELS_FILE):
        try:
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_data(data):
    with open(LEVELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def format_duration(seconds):
    if seconds < 60:
        return f"{int(seconds)} ثانية"
    minutes = seconds // 60
    if minutes < 60:
        return f"{int(minutes)} دقيقة"
    hours = minutes // 60
    if hours < 24:
        return f"{int(hours)} ساعة"
    return f"{int(hours // 24)} يوم"


def hours_text(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h} ساعة و {m} دقيقة" if h else f"{m} دقيقة"


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.cooldowns = {}

    def xp_needed(self, level):
        return 100 + (level * 50)

    def progress_bar(self, current, total, length=10):
        percentage = current / total if total > 0 else 0
        filled = int(length * percentage)
        return "▰" * filled + "▱" * (length - filled) + f" {int(percentage * 100)}%"

    def get_user_data(self, guild_id, user_id):
        gid = str(guild_id)
        uid = str(user_id)
        if gid not in self.data:
            self.data[gid] = {}
        if uid not in self.data[gid]:
            self.data[gid][uid] = {
                "xp": 0, "level": 0, "messages": 0,
                "voice": 0, "rep": 0, "cd": {}
            }
        # ترقية البيانات القديمة
        user = self.data[gid][uid]
        user.setdefault("messages", 0)
        user.setdefault("voice", 0)
        user.setdefault("rep", 0)
        user.setdefault("cd", {})
        return user

    def save(self):
        save_data(self.data)

    # ═══════════════════════════════════════
    # 📩 Event: XP من الرسائل
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        gid = str(message.guild.id)
        uid = str(message.author.id)
        now = time.time()
        # cooldown 60 ثانية
        key = (gid, uid)
        if key in self.cooldowns and now - self.cooldowns[key] < 60:
            return
        self.cooldowns[key] = now
        user = self.get_user_data(gid, uid)
        user["messages"] += 1
        xp_gained = random.randint(5, 15)
        user["xp"] += xp_gained
        level = user["level"]
        needed = self.xp_needed(level)
        leveled_up = False
        while user["xp"] >= needed:
            user["xp"] -= needed
            level += 1
            user["level"] = level
            needed = self.xp_needed(level)
            leveled_up = True
        self.save()
        if leveled_up:
            try:
                await message.channel.send(f"🎉 مبروك يا {message.author.mention}! وصلت للمستوى **{level}**!")
            except:
                pass

    # ═══════════════════════════════════════
    # 🔊 Event: XP من الصوت
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        if after.channel and not before.channel:
            # دخل روم صوتي
            pass
        # هنحسب الوقت بشكل مبسط — كل 60 ثانية يدخل روم = 5-10 XP

    # ═══════════════════════════════════════
    # 📈 rank
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="rank", aliases=["مستوى", "لفل", "level"], description="📊 عرض المستوى")
    @app_commands.describe(member="العضو (اختياري)")
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        gid = str(ctx.guild.id)
        uid = str(target.id)
        user = self.get_user_data(gid, uid)
        level = user["level"]
        xp = user["xp"]
        needed = self.xp_needed(level)
        all_users = self.data.get(gid, {})
        sorted_users = sorted(all_users.items(), key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)), reverse=True)
        rank_pos = next((i + 1 for i, (u, _) in enumerate(sorted_users) if u == uid), 0)
        embed = discord.Embed(title=f"📊 بطاقة مستوى {target.display_name}", color=Colors.INFO)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 المستوى", value=f"**{level}**", inline=True)
        embed.add_field(name="⭐ XP", value=f"**{xp}/{needed}**", inline=True)
        embed.add_field(name="🥇 الترتيب", value=f"**#{rank_pos}**", inline=True)
        embed.add_field(name="📈 التقدم", value=self.progress_bar(xp, needed), inline=False)
        embed.set_footer(text=f"المطلوب للترقية: {needed - xp} XP")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🏆 top
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="top", aliases=["توب", "افضل", "leaderboard", "lb"], description="🏆 أفضل 10 أعضاء")
    async def top(self, ctx: commands.Context):
        gid = str(ctx.guild.id)
        all_users = self.data.get(gid, {})
        if not all_users:
            await ctx.send("❌ مفيش بيانات!")
            return
        sorted_users = sorted(all_users.items(), key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, u) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown ({uid})"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            desc += f"{medal} **{name}** — مستوى: **{u.get('level', 0)}** | XP: **{u.get('xp', 0)}**\n"
        embed = discord.Embed(title="🏆 أفضل 10 أعضاء", description=desc, color=Colors.GOLD)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🪪 profile
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="profile", aliases=["بروفايل", "بطاقتي", "ملفي"], description="🪪 بطاقة شاملة")
    @app_commands.describe(member="العضو (اختياري)")
    async def profile(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        gid = str(ctx.guild.id)
        uid = str(target.id)
        user = self.get_user_data(gid, uid)
        embed = discord.Embed(title=f"🪪 بطاقة {target.display_name}", color=Colors.INFO)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_description(f"╭ ⭐ المستوى **{user['level']}**\n╰ {self.progress_bar(user['xp'], self.xp_needed(user['level']), 14)}")
        embed.add_field(name="❤️ السمعة", value=f"{user['rep']}", inline=True)
        embed.add_field(name="💬 الرسائل", value=f"{user['messages']:,}", inline=True)
        embed.add_field(name="🎙️ الصوت", value=hours_text(user['voice']), inline=True)
        embed.add_field(name="📥 دخل السيرفر", value=discord.utils.format_dt(target.joined_at, 'R'), inline=False)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ❤️ rep
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="rep", aliases=["سمعة", "شكر"], description="❤️ إعطاء نقطة سمعة")
    @app_commands.describe(member="العضو")
    async def rep(self, ctx: commands.Context, member: discord.Member):
        if member.bot:
            await ctx.send("❌ ما تعطي بوت سمعة!")
            return
        if member.id == ctx.author.id:
            await ctx.send("❌ ما تعطي نفسك سمعة!")
            return
        gid = str(ctx.guild.id)
        author = self.get_user_data(gid, ctx.author.id)
        last_rep = author["cd"].get("rep", 0)
        now = time.time()
        if now - last_rep < 43200:  # 12 ساعة
            remaining = 43200 - (now - last_rep)
            await ctx.send(f"⏳ ارجع بعد **{format_duration(remaining)}**")
            return
        author["cd"]["rep"] = now
        target = self.get_user_data(gid, member.id)
        target["rep"] += 1
        self.save()
        embed = discord.Embed(
            title="❤️ تم",
            description=f"أعطيت {member.mention} نقطة سمعة!\nسمعته الآن: **{target['rep']}**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💬 mymessages
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="mymessages", aliases=["رسائلي", "نشاطي"], description="💬 عدد رسائلك")
    @app_commands.describe(member="العضو (اختياري)")
    async def mymessages(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        gid = str(ctx.guild.id)
        user = self.get_user_data(gid, target.id)
        embed = discord.Embed(
            title="💬 النشاط الكتابي",
            description=f"{target.mention} أرسل **{user['messages']:,}** رسالة",
            color=Colors.INFO
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💬 messages-top
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="messages-top", aliases=["توب_رسائل", "اكثر_تفاعل"], description="💬 أكثر الأعضاء رسائل")
    async def messages_top(self, ctx: commands.Context):
        gid = str(ctx.guild.id)
        all_users = self.data.get(gid, {})
        if not all_users:
            await ctx.send("📭 مفيش بيانات!")
            return
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("messages", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, u) in enumerate(sorted_users):
            if u.get("messages", 0) == 0:
                continue
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            desc += f"{medal} **{name}** — **{u.get('messages', 0):,}** رسالة\n"
        embed = discord.Embed(title="💬 أكثر الأعضاء رسائل", description=desc or "لا توجد بيانات", color=Colors.INFO)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎙️ myvoice
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="myvoice", aliases=["صوتي", "نشاطي_الصوتي"], description="🎙️ وقتك في الصوت")
    @app_commands.describe(member="العضو (اختياري)")
    async def myvoice(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        gid = str(ctx.guild.id)
        user = self.get_user_data(gid, target.id)
        embed = discord.Embed(
            title="🎙️ النشاط الصوتي",
            description=f"{target.mention} جلس **{hours_text(user['voice'])}** في الرومات الصوتية",
            color=Colors.INFO
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎙️ voice-top
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="voice-top", aliases=["توب_صوت", "اكثر_صوت"], description="🎙️ أكثر الأعضاء جلوساً")
    async def voice_top(self, ctx: commands.Context):
        gid = str(ctx.guild.id)
        all_users = self.data.get(gid, {})
        if not all_users:
            await ctx.send("📭 مفيش بيانات!")
            return
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("voice", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, u) in enumerate(sorted_users):
            if u.get("voice", 0) == 0:
                continue
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            desc += f"{medal} **{name}** — **{hours_text(u.get('voice', 0))}**\n"
        embed = discord.Embed(title="🎙️ أكثر الأعضاء في الصوت", description=desc or "لا توجد بيانات", color=Colors.INFO)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎖️ levelrole
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="levelrole", aliases=["رتبة_لفل"], description="🎖️ ربط رتبة بمستوى")
    @commands.has_permissions(manage_roles=True)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(level="المستوى", role="الرتبة")
    async def levelrole(self, ctx: commands.Context, level: int, role: discord.Role):
        if level < 1 or level > 1000:
            await ctx.send("❌ المستوى من 1 لـ 1000!")
            return
        if role.managed or role.position >= ctx.guild.me.top_role.position:
            await ctx.send("❌ الرتبة أعلى من البوت أو رتبة نظام!")
            return
        gid = str(ctx.guild.id)
        self.data.setdefault(gid, {}).setdefault("_levelroles", {})
        self.data[gid]["_levelroles"][str(level)] = role.id
        self.save()
        embed = discord.Embed(
            title="✅ تم الربط",
            description=f"من يوصل المستوى **{level}** ياخذ {role.mention}",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🗑️ removelevelrole
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="removelevelrole", aliases=["حذف_رتبة_لفل"], description="🗑️ حذف ربط رتبة")
    @commands.has_permissions(manage_roles=True)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(level="المستوى")
    async def removelevelrole(self, ctx: commands.Context, level: int):
        gid = str(ctx.guild.id)
        roles = self.data.get(gid, {}).get("_levelroles", {})
        if str(level) not in roles:
            await ctx.send("❌ مفيش رتبة مربوطة بالمستوى ده!")
            return
        del self.data[gid]["_levelroles"][str(level)]
        self.save()
        await ctx.send(f"✅ تم حذف رتبة المستوى **{level}**")

    # ═══════════════════════════════════════
    # 🎖️ levelroles
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="levelroles", aliases=["رتب_المستويات"], description="🎖️ عرض الرتب المربوطة")
    async def levelroles(self, ctx: commands.Context):
        gid = str(ctx.guild.id)
        roles = self.data.get(gid, {}).get("_levelroles", {})
        if not roles:
            await ctx.send("📭 مفيش رتب مربوطة!")
            return
        sorted_roles = sorted(roles.items(), key=lambda x: int(x[0]))
        desc = "\n".join(f"مستوى **{lvl}** ← <@&{rid}>" for lvl, rid in sorted_roles)
        embed = discord.Embed(title="🎖️ رتب المستويات", description=desc, color=Colors.INFO)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ➕ addxp
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="addxp", aliases=["اعطاء_خبرة", "اضف_خبرة"], description="➕ إعطاء خبرة (للإدارة)")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(member="العضو", amount="الكمية")
    async def addxp(self, ctx: commands.Context, member: discord.Member, amount: int):
        if amount < 1:
            await ctx.send("❌ الكمية لازم تكون 1 على الأقل!")
            return
        gid = str(ctx.guild.id)
        user = self.get_user_data(gid, member.id)
        user["xp"] += amount
        while user["xp"] >= self.xp_needed(user["level"]):
            user["xp"] -= self.xp_needed(user["level"])
            user["level"] += 1
        self.save()
        await ctx.send(f"✅ تم إعطاء {member.mention} **{amount:,}** خبرة\nمستواه الآن **{user['level']}**")

    # ═══════════════════════════════════════
    # 🔄 resetlevel
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="resetlevel", aliases=["تصفير_لفل", "صفر_لفل"], description="🔄 تصفير مستوى (للإدارة)")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(member="العضو")
    async def resetlevel(self, ctx: commands.Context, member: discord.Member):
        gid = str(ctx.guild.id)
        user = self.get_user_data(gid, member.id)
        user["xp"] = 0
        user["level"] = 0
        self.save()
        await ctx.send(f"🔄 تم تصفير مستوى {member.mention}")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Levels(bot))