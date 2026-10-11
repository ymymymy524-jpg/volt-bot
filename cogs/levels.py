import discord
from discord.ext import commands
import json
import os
import random

# مسار ملف التخزين
LEVELS_FILE = "levels.json"


# دالة لتحميل البيانات من ملف JSON
def load_data():
    if os.path.exists(LEVELS_FILE):
        try:
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


# دالة لحفظ البيانات في ملف JSON
def save_data(data):
    with open(LEVELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.cooldowns = {}

    # ==========================================
    # 🔧 دوال مساعدة
    # ==========================================
    def xp_needed(self, level):
        """حساب الـ XP المطلوب للترقية"""
        return 100 + (level * 50)

    def progress_bar(self, current, total, length=10):
        """إنشاء Progress Bar نصي"""
        percentage = current / total if total > 0 else 0
        filled = int(length * percentage)
        bar = "▰" * filled + "▱" * (length - filled)
        return f"{bar} {int(percentage * 100)}%"

    def get_user_data(self, guild_id, user_id):
        guild_id = str(guild_id)
        user_id = str(user_id)
        if guild_id not in self.data:
            self.data[guild_id] = {}
        if user_id not in self.data[guild_id]:
            self.data[guild_id][user_id] = {"xp": 0, "level": 0}
        return self.data[guild_id][user_id]

    def save(self):
        save_data(self.data)

    # ==========================================
    # 📩 Event: حساب XP عند الرسائل
    # ==========================================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # ⚠️ مهم: لازم نستدعي process_commands عشان الأوامر تشتغل
        await self.bot.process_commands(message)

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        now = discord.utils.utcnow()

        # Cooldown لمدة 60 ثانية
        cooldown_key = (guild_id, user_id)
        if cooldown_key in self.cooldowns:
            last_time = self.cooldowns[cooldown_key]
            if (now - last_time).total_seconds() < 60:
                return
        self.cooldowns[cooldown_key] = now

        user_data = self.get_user_data(guild_id, user_id)

        xp_gained = random.randint(5, 15)
        user_data["xp"] += xp_gained

        level = user_data["level"]
        needed = self.xp_needed(level)
        leveled_up = False

        while user_data["xp"] >= needed:
            user_data["xp"] -= needed
            level += 1
            user_data["level"] = level
            needed = self.xp_needed(level)
            leveled_up = True

        self.save()

        if leveled_up:
            try:
                await message.channel.send(
                    f"🎉 مبروك يا {message.author.mention}! وصلت للمستوى **{level}**!"
                )
            except discord.HTTPException:
                pass

    # ==========================================
    # 📊 أمر !rank - عرض المستوى
    # ==========================================
    @commands.command(
        name="rank",
        aliases=["r", "مستوى", "لفل", "level"],
        description="📊 عرض مستوى ورتبة عضو في السيرفر"
    )
    async def rank_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """عرض مستوى عضو"""
        target = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(target.id)

        user_data = self.get_user_data(guild_id, user_id)
        level = user_data["level"]
        xp = user_data["xp"]
        needed = self.xp_needed(level)

        # حساب الترتيب
        all_users = self.data.get(guild_id, {})
        sorted_users = sorted(
            all_users.items(),
            key=lambda x: (x[1]["level"], x[1]["xp"]),
            reverse=True
        )
        rank_pos = 1
        for uid, udata in sorted_users:
            if uid == user_id:
                break
            rank_pos += 1

        embed = discord.Embed(
            title=f"📊 بطاقة مستوى {target.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 المستوى", value=f"**{level}**", inline=True)
        embed.add_field(name="⭐ XP", value=f"**{xp}/{needed}**", inline=True)
        embed.add_field(name="🥇 الترتيب", value=f"**#{rank_pos}**", inline=True)
        embed.add_field(name="📈 التقدم", value=self.progress_bar(xp, needed), inline=False)
        embed.set_footer(text=f"المطلوب للترقية: {needed - xp} XP")

        await ctx.send(embed=embed)

    # ==========================================
    # 🏆 أمر !top - أفضل 10 أعضاء
    # ==========================================
    @commands.command(
        name="top",
        aliases=["t", "توب", "افضل", "leaderboard", "lb"],
        description="🏆 عرض أفضل 10 أعضاء في المستويات"
    )
    async def top_prefix(self, ctx: commands.Context):
        """عرض لوحة المتصدرين"""
        guild_id = str(ctx.guild.id)
        all_users = self.data.get(guild_id, {})

        if not all_users:
            await ctx.send("❌ مفيش بيانات مستويات في السيرفر ده!")
            return

        sorted_users = sorted(
            all_users.items(),
            key=lambda x: (x[1]["level"], x[1]["xp"]),
            reverse=True
        )[:10]

        medals = ["🥇", "🥈", "🥉"]
        description = ""

        for i, (user_id, udata) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"Unknown User ({user_id})"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            description += f"{medal} **{name}** — المستوى: **{udata['level']}** | XP: **{udata['xp']}**\n"

        embed = discord.Embed(
            title="🏆 أفضل 10 أعضاء في المستويات",
            description=description,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    # ==========================================
    # 📊 أمر !setlevel - تحديد مستوى (للمشرفين)
    # ==========================================
    @commands.command(
        name="setlevel",
        aliases=["sl", "تحديد-مستوى", "عين-مستوى"],
        description="📊 تحديد مستوى عضو (للمشرفين)"
    )
    @commands.has_permissions(administrator=True)
    async def setlevel_prefix(self, ctx: commands.Context, member: discord.Member, level: int):
        """تحديد مستوى عضو - يتطلب Administrator"""
        # التحقق من النطاق
        if level < 0 or level > 1000:
            await ctx.send("❌ المستوى لازم يكون بين **0** و **1000**!", delete_after=8)
            return

        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        user_data = self.get_user_data(guild_id, user_id)
        user_data["level"] = level
        user_data["xp"] = 0
        self.save()

        embed = discord.Embed(
            title="✅ تم تحديث المستوى",
            description=f"تم تعيين مستوى **{member.mention}** إلى **{level}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    # ==========================================
    # 🔄 أمر !resetlevel - تصفير مستوى (للمشرفين)
    # ==========================================
    @commands.command(
        name="resetlevel",
        aliases=["rl", "تصفير-مستوى", "صفر-مستوى"],
        description="📊 تصفير مستوى عضو (للمشرفين)"
    )
    @commands.has_permissions(administrator=True)
    async def resetlevel_prefix(self, ctx: commands.Context, member: discord.Member):
        """تصفير مستوى عضو - يتطلب Administrator"""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        user_data = self.get_user_data(guild_id, user_id)
        user_data["level"] = 0
        user_data["xp"] = 0
        self.save()

        embed = discord.Embed(
            title="🔄 تم التصفير",
            description=f"تم تصفير مستوى **{member.mention}**",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    # ==========================================
    # ⚠️ معالجة الأخطاء
    # ==========================================
    @setlevel_prefix.error
    @resetlevel_prefix.error
    async def on_admin_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك صلاحية **Administrator**!", delete_after=8)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو ده في السيرفر!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "❌ لازم تحدد العضو والمستوى!\n"
                "**مثال:** `!setlevel @عضو 5`",
                delete_after=8
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد إن المستوى رقم صحيح!", delete_after=8)


async def setup(bot):
    await bot.add_cog(Levels(bot))